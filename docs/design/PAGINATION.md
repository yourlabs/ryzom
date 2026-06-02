# Paginated reactive live-list — design

This is the implementation design for adding **numbered (offset) pagination** to
the reactive product list, while keeping it live. It builds directly on the
problem stated in [`PROBLEM.md`](./PROBLEM.md): a subscription is a *standing
query*, a save is an *event*, and the job is to compute each standing query's
minimal delta. Pagination turns each standing query into a **window** and forces
us to handle the **window ripple** that `PROBLEM.md` §4(b) flagged as the hard
part.

Reference for the UX (not the mechanism): CRUDLFAP's pager
(`crudlfap/src/crudlfap/html.py:788`, `MDCDataTablePagination`) — *total
indicator + first / prev / next / last + rows-per-page select*. CRUDLFAP renders
it as a server round-trip that swaps the table (Unpoly partial); this demo is
websocket-push based, so we reproduce the **UX**, not the swap mechanism.

---

## 1. Choices (fixed for v1)

- **Numbered offset pages**: `ORDER BY <key> LIMIT per_page OFFSET offset`, with
  first / prev / next / last and a per-page select.
- **Fixed total order**: `('name', 'id')`. The `id` tiebreak makes it a *total*
  order — without it, two rows with the same name have ambiguous rank and the
  window/diff math is undefined.
- **Page size**: default 5 (small, so ripple is visible in the demo);
  selectable from `(3, 5, 10, 25)`.

The inherent consequence of offset pages: **an insert/delete near the front
ripples through every later page.** Adding a row that sorts first shifts every
rank by one, so page 2 loses its bottom row and gains a new top row — and
neither is the row that changed. This is what "page N of an offset list" *means*,
not an inefficiency we can optimize away.

---

## 2. The window-diff engine (the core)

The key realization: a windowed query materialises only `offset + per_page`
rows, **never the whole table**. So for an affected subscription we recompute
*just its window* (≤ per_page rows) and diff the old window id-list against the
new one. A single base-row event changes a window by at most: one row leaves +
one row enters, plus the changed row's content/position.

Per save/delete, for every subscription on the model (under the
`select_for_update` row lock already in place):

1. `was_in = changed_pk in sub.window_ids` (in memory)
2. `now_matches = subscriber.get_queryset(user, base.filter(pk=changed)).exists()`
   — the cheap per-object test from `PROBLEM.md` step 2.
3. **Sound skip:** `if not was_in and not now_matches: continue`. If the row
   neither matched the filter before nor after, the filtered *set* is unchanged,
   so this window cannot have changed. (Most rows don't match most filters →
   this skips the overwhelming majority cheaply.)
4. **Otherwise re-window + diff:** recompute `new_window = get_queryset()[offset:offset+per_page]`,
   then against `old_window`:
   - `removed = old - new` → `send_remove(id)` (the evicted boundary row, or the
     changed row leaving)
   - `added = new - old` → `send_insert(id, pos)` at its index *within the window*
   - the changed row, if it stayed in the window: `send_change` if its position
     is unchanged, else `send_remove`+`send_insert` (a move)

   Ops are emitted **removes first, then inserts by ascending position**, so
   each `insert(position)` lands at the right child index of the current DOM.

Cost: O(subscriptions) in-memory membership checks + the cheap `exists()`, and a
≤ per_page re-window **only** for subscriptions whose filtered set the change
actually touched — versus the old O(subscriptions × table).

### Protocol

No new DDP op. Everything is expressed with the existing
`insert(position)` / `change(id)` / `remove(id)`. The client (`ryzom.js`) is
unchanged; `send_insert` already uses `position = window_ids.index(pk)`, which is
now the index *within the window*.

---

## 3. State on the Subscription

All carried in the existing `options` JSON (no new columns / migration):

| key | meaning |
|-----|---------|
| `offset`, `per_page` | the window (per client; changed by the pager) |
| `q`, `in_stock` | the filter (unchanged from before) |
| `first_key`, `last_key` | the sort-key tuples (`[name, id]`) of the window's first/last rows — JSON-comparable; reserved for the boundary skip in §6 |
| `total` | filtered row count, for the pager indicator |

`qs` (the `ArrayField`) now stores the **window's** ordered ids (≤ per_page),
not the whole set. `Subscription.get_queryset` slices when the subscriber opts
in (declares `paginate_by` + `order`); non-paginated subscribers behave exactly
as before. The `clear_limits` hack in `signals.py` is removed — we *want* the
limit now.

A subtlety: a sliced queryset can't be `.get(pk=...)`'d. So `get_queryset`
returns the sliced window (for the initial render), and the signal handler
fetches row instances for `insert`/`change` from a fresh *unsliced* filtered
queryset (`get_queryset_unsliced().get(pk=...)`), preserving any annotations.

---

## 4. The pager (UX from CRUDLFAP, mechanism native to this demo)

`ProductPager` is a custom element (same shape as `ProductFilter` / `SellButton`):
*total indicator + first / prev / next / last + per-page select.* A click does a
`fetch` POST to `ProductPagerView` with the new `offset`/`per_page` + token.

`ProductPagerView` (mirrors `ProductFilterView`): locks the subscription, writes
the new `offset`/`per_page`, re-windows, diffs old-vs-new window (a page jump is
just a full replace expressed as removes + inserts), pushes the row deltas over
the websocket, and **returns JSON** `{offset, per_page, total, num_pages}`. The
pager element updates its own total text and button disabled-states from that
JSON. So: rows update via the push (consistent with the rest of the demo); the
pager's own chrome updates from the fetch response.

> Why not CRUDLFAP's re-render-and-swap? This demo has no Unpoly and is built
> entirely on the "visible update = websocket push" model. Pushing the row diff
> reuses `ProductFilterView` almost verbatim and keeps one coherent update path;
> returning the counts as JSON is enough to drive the pager chrome without a
> second rendering mechanism.

---

## 5. Edge cases handled

- **Offset past the end** (deletes shrank the set below `offset`): clamp `offset`
  to the last non-empty page in `get_queryset`.
- **Ties**: resolved by the `('name', 'id')` total order.
- **Empty window**: `first_key`/`last_key` are `None`; the skip in §6 degrades
  to "never skip", still correct.
- **Live total**: the indicator is refreshed on filter/pager interaction. A
  background create/delete by another user does not live-update *my* total until
  I next interact (same freshness as CRUDLFAP, which only recomputes on nav).

---

## 6. Deferred (documented, not built)

- **Boundary-key skip for updates/deletes/deep windows.** v1's sound skip only
  fires for rows that don't match the filter at all. A change that matches the
  filter but lands *below* the visible window still triggers a (wasted) re-window
  of that subscription. Using `first_key`/`last_key` (already stored) plus the
  changed row's sort key would skip those too — but for updates/deletes the
  *old* key isn't available post-event, so doing it soundly needs either passing
  the pre-change key through the signal or storing a per-row last-known key.
- **Bulk "replace-window" DDP op** to make a page jump one message instead of
  up to 2 × per_page.
- **Keyset / cursor pagination** to avoid `OFFSET`'s O(offset) scan on deep
  pages. Out of scope: we chose numbered offset pages.
- **Live "Page X of Y"** that updates from background mutations (see §5).
```
