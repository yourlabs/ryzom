# The reactive list-view problem: routing writes to subscriptions

This document states the central scaling/design problem behind the live list
view in the reactive Product demo (and behind `ryzom_django_channels` in
general). It is the "grosse difficulté de la vue de liste."

It is a **problem statement**, not a solution. The goal is to make the problem,
its known shape, and the solution spectrum legible to whoever implements it next.

---

## 1. Context in this example

Every browser that opens `/crud/products/` creates one `Subscription` row tied
to the `products` publication, **with that client's filter baked into
`options`** (`{q, in_stock}` — see `components.py:ProductRows.get_queryset` and
`views.py:ProductFilterView`).

So with many clients you get **one subscription per distinct queryset**:

```
sub A: products, {}                      (unfiltered)
sub B: products, {in_stock: true}
sub C: products, {q: "wid"}
sub D: products, {q: "gad", in_stock: true}
…                                        (one per connected client+filter)
```

Each subscription is, in effect, a **standing query** the server has promised to
keep live on a specific socket.

---

## 2. What happens today, and why it does not scale

When a single `Product` is created/updated/deleted, a `post_save`/`post_delete`
signal fires `ryzom_django_channels/signals.py:ddp_insert_change`, which does:

```python
subscriptions = Subscription.objects.filter(publication__model_class='Product', …)
for sub in subscriptions:                 # every subscription for this model
    old_qs = sub.queryset                 # stored id list
    qs = sub.get_queryset()               # ← RE-RUNS the full filtered query in the DB
    new_qs = sub.queryset
    diff = set(new_qs) ^ set(old_qs)       # whole-set difference
    → send insert / change / remove
```

`sub.get_queryset()` re-executes `Product.objects.all()` → applies that
subscription's filter → `SELECT id FROM product WHERE … ORDER BY name`,
materializes the id list, and Python set-diffs old vs new.

**Cost:** one write = one full filtered query **per subscription** + a whole-set
diff. With 500 connected filtered lists, selling one product triggers ~500
filtered `SELECT`s, just to discover the change affects maybe 3 of them. It is
`O(subscriptions × table)` per write. Fine for a demo; untenable in production.

This is exactly **Meteor's original "poll-and-diff"** livequery strategy — the
one Meteor itself had to abandon (for oplog tailing) to scale. This stack is a
re-implementation of Meteor's DDP, so it inherits the same starting point.

---

## 3. The shape of the problem: forward vs. reverse query

A normal request is a **forward query**: "give me the rows matching this
filter." Databases are built for it (indexes, planner).

A live list needs the **inverse**: "a single row changed — which standing
queries does it now match or stop matching, and how does each result change?"

You have **N standing queries** and a **stream of single-row events**, and must
route each event to the queries it affects and emit the minimal delta. Databases
do not optimize this direction; it is its own field. Names for it:

- **Reactive / live queries** — Meteor, RethinkDB changefeeds, Firebase,
  Supabase Realtime
- **Incremental View Maintenance (IVM)** — treat each subscription as a
  materialized view, maintained as base data changes (Materialize, Noria,
  differential dataflow)
- **Content-based publish/subscribe matching** — "match one event against many
  stored predicates" (Siena, Gryphon)
- **Production-rule matching** — the Rete algorithm in rules engines (same
  matching kernel)

---

## 4. Two sub-problems

When `Product #5` changes, for a given subscription you must decide:

**(a) Membership transition** — is #5 in this query's result, and was it before?

| was → now | action |
|-----------|--------|
| out → in  | `insert` |
| in → out  | `remove` |
| in → in   | `change` (and maybe **move position** if sorted) |
| out → out | ignore |

**(b) Window ripple (the hard one)** — if the subscription has `ORDER BY … LIMIT
n` (pagination), inserting #5 into the visible window can **push another row
out** of it. So one write yields *two* ops (insert #5, remove #20) — and #20 is
not even the row that changed. Membership then depends on **other rows**, not
just the changed one.

> The current `Product` demo has **no limit**, so (b) does not bite yet. A real
> list view paginates, so (b) is unavoidable there. The present whole-set diff
> handles (b) for free but at the O(table) cost above; any cheaper scheme must
> reason about window boundaries explicitly.

---

## 5. Why "just test the changed object" is necessary but not sufficient

The cheap idea (see §7, step 2) answers (a) per subscription with an O(1)
indexed check instead of a full requery. But you still **iterate all N
subscriptions**. To skip the irrelevant ones, you must **index subscriptions by
their filters** — and indexability depends entirely on the operator:

| Filter in `Product` | Reverse-matchable? |
|---------------------|--------------------|
| `in_stock` (boolean / equality) | **Easy** — bucket subscriptions by value; a change only visits the relevant bucket. |
| `q` = `name ILIKE '%term%'` (substring) | **Hard** — needs an inverted index / trie over subscribers' search terms, tested against the changed name. |
| `ORDER BY name` + `LIMIT` (window) | **Very hard** — membership depends on neighbouring rows, not just the changed one. |
| per-object permission `has_perm(user, obj)` | The effective predicate is `filter AND can_see(user, obj)` — per subscription's user. |

That last row is the **crudlfap connection** (§6): a subscription's true
predicate is *filter + permission*, and it should be expressed **once** (the list
view's own rule) and **reused** for the reverse test, never duplicated.

---

## 6. The crudlfap analogy (the suggested pattern)

crudlfap builds an action menu by, for each candidate view, **binding it to the
same `request` (hence the same `user`) and calling a cheap
`has_perm(user, action, obj)`** — a tiny per-view boolean. It never computes
anything heavy; it asks each candidate "are you allowed for this user+object?"
and keeps the yeses.

Apply the same shape to subscriptions: instead of recomputing each
subscription's whole queryset, ask each one a **cheap per-object question** using
its own stored filter (+ user/permission), with the changed object as input.
Same role as `has_perm` per view; "un système peu coûteux."

Crucially: reuse the **single source of truth** — the list view's own filter
(`ProductRows.get_queryset`) and permission rule — for both the forward render
and the reverse test. Don't write the membership logic twice.

---

## 7. Solution spectrum (simplest → heaviest)

1. **Poll-and-diff, all subscriptions** *(current)*. Re-run every standing query
   on every write. Trivial, always correct, `O(subs × table)`. Demo-grade.

2. **Per-object predicate, all subscriptions** *(recommended next step)*. Still
   loop all subscriptions, but each check is O(1):
   ```python
   now_in = sub.get_queryset_for(Product.objects.filter(pk=changed.pk)).exists()
   was_in = changed.pk in sub.qs
   → insert / remove / change / ignore
   ```
   Reuses the view's filter (+ permission), drops the whole-table requery, and
   removes the stateful whole-set diff that made the filter racy/dupe-prone.
   Good to hundreds of clients. *(No window/limit handling yet.)*

3. **Predicate indexing / content-based matching**. Index subscriptions by their
   filter attributes so a change visits only potentially-affected subscriptions.
   Booleans/equality/ranges index cleanly; substring search needs an inverted
   index; windows still need boundary logic. This is the "on va pas toutes les
   essayer" goal — you are now building a small matching engine.

4. **Incremental View Maintenance / differential dataflow** (Materialize, Noria,
   RethinkDB). The system understands each query's structure and propagates
   deltas through filters/joins/aggregates/windows without re-running anything.
   The principled general answer; a large investment.

5. **DB-native change capture** (Postgres logical decoding / `LISTEN`/`NOTIFY`,
   Mongo oplog à la Meteor). Stop polling; the DB tells you what changed. You
   still need matching (steps 2–4) on top.

---

## 8. Where this example sits / recommendation

- **Now:** step 1 — correct, demo-grade, does not scale.
- **Next:** step 2 — the crudlfap-style cheap per-object test, filter + permission
  expressed once and reused. Modest effort, large win, and it also removes the
  stateful-`qs` fragility behind the duplicate-row bugs documented in the README.
- **Later / research-grade:** step 3+ (skip unaffected subscriptions; handle
  sort + limit windows, joins, aggregates). Worth knowing it exists; not worth
  building for a demo.

**Mental model to keep:** a subscription is a *standing query*; a save is an
*event*; the job is to (a) find the standing queries an event touches and
(b) compute each one's minimal delta — including ripple effects from sort+limit
windows. Databases optimize the forward direction; this is the reverse
direction, which is why it is its own field.

---

## 9. Open questions for the implementer

- How is a subscription's predicate expressed so it can be evaluated both
  forward (render) and reverse (per-object test) from **one** definition?
  (Today it is a `QuerySet` transform `get_queryset(user, qs, opts)`; scoping it
  to `qs.filter(pk=changed)` reuses it for the reverse test.)
- Where do per-object **permissions** plug into that predicate (the crudlfap
  `has_perm` step)?
- Do we need sort/limit **windows** in v1? If yes, step 2 must grow boundary
  handling; if no, defer.
- Is there a cheap **bucketing** for the common filters (e.g. boolean facets) to
  start approaching step 3 without a full matching engine?
