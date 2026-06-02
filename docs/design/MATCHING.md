# Reverse matching — routing a change to only the subscriptions it affects

This is the implementation of [`PROBLEM.md`](./PROBLEM.md) **step 3**: stop
visiting *every* standing query on every write. It is the second half of the
problem — the first (computing each subscription's minimal delta, incl. window
ripple) is in [`PAGINATION.md`](./PAGINATION.md).

## What it removes

Even after steps 1–2 + pagination, a single `Product` save still **loaded and
visited all N subscriptions** for the model (`Subscription.objects.filter(model=…)`)
to ask each whether it cared. We killed the `× table` factor; this kills the
`× subscriptions` factor for filtered subscriptions.

## The key fact that makes it sound

> A subscription is a **candidate** for a change to row X **iff X matches its
> filter with X's new values, or matched with its old values.** The window is
> irrelevant to candidacy.

Why the window doesn't matter: a window is a slice of the filtered set S. If
X ∉ S before *and* ∉ S after, then S is unchanged, so no window over S changed.
Therefore *affected ⟹ X ∈ S_old ∪ S_new*, and `X ∈ S` is exactly `X matches the
filter`. (Caveat: this assumes a row's rendered content depends only on itself —
no cross-row aggregates/ranks. The demo's rows are independent.)

So routing reduces to a **reverse query**: given one row, which subscriptions'
filters match it (new or old)?

## Facets: the filter expressed once, used both ways

A subscriber declares its filter as `facets` (`ryzom_django_channels/facets.py`),
each a single definition with two directions:

- **forward** `forward(qs, value)` — apply this subscription's stored value to
  the data queryset (renders + windows the list). `SubscribeComponentMixin.get_queryset`
  applies them; this is the one source of truth for the filter.
- **reverse** `candidate(row) -> (annotations, Q)` — a predicate over the
  *Subscription* table selecting subs whose stored value admits `row`.

`ProductRows` declares:

```python
facets = [SearchFacet('q', 'name'), BooleanFacet('in_stock', 'stock_qty'),
          GroupFacet('group')]
```

- `BooleanFacet` reverse: an in-range row (`stock_qty > 0`) is admitted by every
  subscription; an out-of-range row only by subs that didn't switch the flag on
  (`~Q(options__in_stock=True)`).
- `SearchFacet` reverse: a sub admits the row iff its stored term is a substring
  of the row's field — `strpos(lower(row.name), lower(options->>'q')) > 0`
  (empty/missing term matches all). One in-DB sequential scan over the
  subscription table's terms — the cheap, un-indexed end of PROBLEM.md §5.
- `GroupFacet` is the **permission** facet (PROBLEM.md §6, `filter AND
  can_see(user, obj)`). Unlike the others it keys off the subscription's *user*,
  not a stored option: forward scopes the queryset (staff → all; a user → their
  groups' rows + public; anonymous → only public), reverse emits a `Q` over
  `client__user` — a public row (`group_id` NULL) admits every subscription, a
  private row only `Q(client__user__is_staff=True) | Q(client__user__groups=
  row.group_id)`. This is one indexed membership test (the "bucket by value"
  easy case of §5) AND-composed with the others by the same `predicate &= q`
  loop, so the effective predicate is literally `filter AND can_see`.
  `Product.group` is a single FK (not M2M) so the visibility key is a concrete
  column landing in `_snapshot`, letting a regroup route via both old and new
  group. *Deferred:* M2M-per-row visibility (not a concrete field, fires
  `m2m_changed` not `post_save`) and arbitrary non-SQL `has_perm(user, obj)`
  rules (reverse can't be a `Q`; would fall back to a Python test over the
  already-narrowed candidates).

## Flow

1. **`pre_save`** snapshots the row's old field values onto the instance
   (`_ddp_old`), so the "in → out" transition (matched before, not after) is
   detectable.
2. **`post_save` / `post_delete`** (in the saving process) call `_candidate_ids`,
   which groups the model's subscriptions by subscriber class and, per class,
   `annotate(**facet annotations).filter(<AND of facet predicates>)` against the
   row's new and old snapshots — the union is the candidate set. One query over
   the (small) subscription table replaces N requeries of the data table. A
   subscriber that declares no facets has an unknown filter → all its
   subscriptions are candidates (no worse than before).
3. Only the candidate ids are enqueued to the Celery worker, which locks each
   (`select_for_update`) and runs `_push_window_delta` — the window diff from
   PAGINATION.md. The previous `exists()` per-subscription skip is gone: it's
   subsumed by candidate selection (non-candidates are never visited at all).

## Cost

Per write: one reverse-matching query over the subscription table (a seq scan
for substring terms; partial indexes help boolean/equality facets), then a
window diff for **only the matched candidates** — not O(subscriptions). For a
sell among 500 filtered lists, the worker now touches the handful whose filter
the product matches, instead of all 500.

## Honest limits (deferred)

- **Substring is an un-indexed scan** over subscription terms. Sub-linear
  matching needs an inverted index / trie over terms (a real content-based
  matcher, PROBLEM.md §5/§7-step-3) — deferred.
- **Candidate selection runs in the saving request** (sync), adding one query
  (+ the `pre_save` SELECT). Fine here; a heavier deployment would move it to
  the worker with a serialized snapshot.
- **Cross-row derived content** (aggregates/ranks) breaks the candidacy fact
  above; not present in the demo.
- This is step 3, *not* step 4 (IVM/differential dataflow): we still re-window
  each affected subscription rather than propagate deltas through query
  structure.
