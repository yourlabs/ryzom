# ryzom_example_crud

Two CRUD demos built on Ryzom components:

- **`crud.py`** — a classic server-rendered CRUD on the `User` model via the
  generic `Router` (`ryzom_django_mdc.crudlfap`). Plain links + form POSTs, full
  page reloads, modals via `MDCDialog`. No websockets.
- **the reactive Product demo** (`models.py` / `components.py` / `views.py`) —
  a live, server-pushed table + auto-updating detail view over a websocket.

This README documents the **reactive** demo, since that's the non-obvious part.

---

## What it demonstrates

The browser never polls. It opens one websocket and waits. Every time a
`Product` is saved server-side, the server decides which connected clients care
and pushes them a freshly-rendered component, which the client patches into the
DOM. The result:

- **a dynamic table** — new products insert a row, edits change a row, deletes
  remove a row, live, with no reload;
- **an auto-updating detail view** — an open detail page re-renders itself when
  its product changes from anywhere;
- **live search + filter** — type to narrow the table over the websocket (no
  reload), and the filter is *persisted on the subscription* so subsequent live
  pushes respect it (a product edited to match/unmatch inserts/removes itself).

It runs on the reactive plumbing in **`ryzom_django_channels`** (the channels /
DDP / pub-sub layer). This app is a *consumer* of that plumbing.

---

## The two flows

### Flow A — page load (subscribe + render initial state)

```
Browser                              Daphne (single process)
───────                              ───────────────────────
GET /crud/products/  ───────────────► ProductListView (ReactiveMixin)
                                        get_token() → create Client row,
                                        emit <meta name="ryzom-config" …token…>
                                       ProductTable renders:
                                        ProductRows (subscribed <tbody>) →
                                          create Subscription(client, 'products')
                                          render one ProductRow per object
                     ◄──────────────── full HTML, table already populated

ryzom.js reads the meta ────────────► WS  ws://<same-origin>/ws/ddp/?<token>
                                       Consumer.connect():
                                         find Client by token,
                                         store this socket's channel on the Client
                     ◄──────────────── {"type":"Connected"}
        socket now idle, waiting
```

### Flow B — a mutation (push the delta)

```
click "Sell 1" ─ fetch POST ────────► ProductSellView
  /crud/products/<pk>/sell/             product.stock_qty -= 1; product.save()
                     ◄──── 204 ───────  (response is empty on purpose)

                                       post_save signal (Product is Publishable):
                                         for each Subscription on 'products':
                                           recompute queryset, diff old vs new pks
                                           → send_insert / send_change / send_remove
                                             onto that Client's channel
                                       post_save receiver in models.py:
                                         register('product-detail-<pk>').refresh()
                     ◄═══ DDP ═════════ {"type":"DDP","params":{"type":"change",
                                          "params": <serialized ProductRow>}}
ryzom.js changeDOM()
replaces <tr id="product-<pk>">        (only that row; detail tab updates too)
```

**Key point:** the visible update is the *push*, never the HTTP response. The
mutate endpoints return `204` and the `fetch` widgets do nothing with the body.

---

## File map

| File | Role |
|------|------|
| `models.py` | `Product(Publishable, Model)`. `@publish def products` registers the named publication. A `post_save` receiver refreshes any open detail view. |
| `components.py` | The reactive layout. See breakdown below. |
| `views.py` | `ProductListView` / `ProductDetailView` (reactive, `ReactiveMixin`), thin `ProductCreateView` / `ProductSellView` mutate endpoints, `ReactiveApp` (shell + `ryzom.js`), and `urlpatterns`. |
| `migrations/` | The `Product` table. |
| `crud.py` | The unrelated non-reactive `UserRouter` CRUD demo. |

### components.py

| Class | Base | What it is |
|-------|------|------------|
| `ProductRow` | `@model_template('product-row')`, `MDCDataTableTr` | One row. Deterministic `id=f'product-{obj.id}'` so the push can target it. The unit the server re-renders and ships. |
| `ProductRows` | `SubscribeComponentMixin`, `MDCDataTableTbody` | The subscribed element. `publication='products'`, `model_template='product-row'`. Its rows are its direct children (required for position-based inserts). `get_queryset` orders by name. |
| `ProductTable` | `MDCDataTableResponsive` | thead + `ProductRows` tbody. |
| `ProductDetail` | `ReactiveComponentMixin`, `Div` | Single-object view. `register=f'product-detail-{pk}'` → re-rendered + pushed on change. |
| `SellButton` | `Component` (custom element) | `fetch` POST to the sell endpoint, no reload. |
| `ProductCreateForm` | `Component` (custom element) | `fetch` POST of the create form, `preventDefault` + reset. |
| `ProductFilter` | `Component` (custom element) | Debounced search input + "in stock only" checkbox; `fetch` POSTs the filter to re-narrow the live table. |

---

## How the plumbing connects (the non-obvious bits)

- **Publications auto-register.** `ryzom_django_channels` AppConfig.ready()
  walks every model; for each `Publishable` it calls `.publish()`, creating a
  `Publication` row named after each `@publish` method. So defining
  `Product.products` is all it takes — no manual registration.

- **`view` reaches nested components via context.** Ryzom's `to_html` passes
  `**context` (including `view`) down to every child, so a deeply nested
  `ProductRows` can find `view.client` in `reactive_setup`. `get_token()` must
  run *before* render so `view.client` exists.

- **Rows are addressed two ways.** Inserts use a numeric **position** among the
  tbody's children (from the subscription's ordered pk list). Changes/removes
  use the **deterministic DOM id** `product-<pk>`. Both must line up — hence the
  explicit `id=` on `ProductRow` and the subscriber being the `<tbody>`.

- **List vs detail are different mechanisms.** The table is a *Subscription*
  (driven by the global publication signals). The detail is a *Registration*
  (a named re-renderable component) and is refreshed explicitly by the
  `post_save` receiver in `models.py` — the publication signals don't touch
  registrations.

- **Mutations must hit the server process.** See the runtime note below.

- **Filtering is just a re-diff with new options.** `ProductRows.get_queryset`
  reads `opts` (`q`, `in_stock`) that live on the `Subscription`. The
  `ProductFilter` widget POSTs to `ProductFilterView`, which updates the
  subscription's stored opts, recomputes the queryset, and pushes the
  membership delta (`send_insert`/`send_remove`) — the exact same machinery the
  save signals use. Because the opts are stored, every later publication push
  re-applies the filter, so the live table stays filter-correct. The widget
  finds *which* subscription to update via the page's `ryzom-config` token.

---

## Runtime / infra

The reactive stack runs on its full production shape: **Postgres + Redis + a
Celery worker + an ASGI server (daphne)**. Each piece has a job:

| Piece | Role |
|-------|------|
| Postgres | `Subscription.qs` is an `ArrayField` (Postgres-specific); the DB also stores `Client`/`Subscription`/`Publication` rows. |
| Redis | both the Celery broker/result backend **and** the channels group layer (`RedisChannelLayer`). |
| Celery worker | runs the DDP push: `post_save` fires `ddp_insert_change_task.delay(...)`, the worker diffs each subscription and sends the delta over the channel layer. |
| daphne | the ASGI server — serves HTTP **and** the `ws/ddp/` websocket. `daphne` is also prepended to `INSTALLED_APPS` so `manage.py runserver` serves ASGI too. |

Settings auto-enable channels when Redis is reachable on `127.0.0.1:6379` (or
`redis:6379`): the socket probe in `settings.py` sets `CHANNELS_ENABLE`, which
installs the channels apps and the `RedisChannelLayer`. The DB defaults to
Postgres (`ryzom`/`ryzom`/`ryzom` on `127.0.0.1:5432`), overridable via the
`DB_*` env vars (the same ones CI sets).

> **Because the push runs in the Celery worker and the channel layer is Redis
> (not in-process)**, a `Product.save()` from *any* process — a shell, a
> management command, another request — reaches every connected socket. The
> `fetch`-based mutate widgets are a UX choice (no reload), not a constraint.

### Run it

```bash
# 1. infra (example: docker)
docker run -d --name ryzom-postgres \
  -e POSTGRES_DB=ryzom -e POSTGRES_USER=ryzom -e POSTGRES_PASSWORD=ryzom \
  -p 127.0.0.1:5432:5432 postgres:16
docker run -d --name ryzom-redis -p 127.0.0.1:6379:6379 redis:7

# 2. schema
python manage.py migrate

# 3. the push worker (separate terminal)
celery -A ryzom_django_channels.celery worker -l info

# 4. the ASGI server (serves HTTP + ws/ddp/)
daphne -b 127.0.0.1 -p 8000 ryzom_django_example.asgi:application
#   …or: python manage.py runserver   (daphne-backed ASGI)

# open http://127.0.0.1:8000/crud/products/ in two tabs
```

Add a product or click "Sell 1" in one tab and watch the table (and any open
detail page) update in the other — no reload.

---

## Gotchas (learned debugging the live filter)

These bit the reactive filter specifically; they're worth knowing before
building any DDP-driven UI.

### 1. DDP-inserted nodes must carry `ryzom-id` (the duplicate-rows bug)

**Symptom:** toggling the "in stock only" filter worked once, then after an
on/off cycle the filtered-out rows came back *duplicated* and stopped
filtering; the console showed `removeDOM … Cannot read properties of null
(reading 'dataset')`.

**Cause:** the client locates a node to change/remove via `getElementByUuid`,
which resolves by `document.querySelector("[ryzom-id=...]")`. Server-rendered
rows get `ryzom-id` from `Component.to_html`, but DDP-pushed rows are built from
`Component.to_obj`, which **did not** include `ryzom-id`. So the *first* set of
rows (SSR) was findable, but any row re-inserted over the websocket had no
`ryzom-id` → the next `remove` found `null` → the row was never removed, and the
following `insert` stacked a duplicate on top. It compounds every cycle.

This was invisible to a Node/jsdom harness that loads the on-disk `ryzom.js`
(which has a `window.components` registry fallback). The deployed page also
loads **`py2js.js`, whose hoisted `getElementByUuid` is querySelector-only and
overrides** `ryzom.js`'s — so in a real browser there is no registry fallback.
Only a real browser (driven via the Chrome DevTools Protocol) reproduced it.

**Fix:** `Component.to_obj` now emits `ryzom-id` in the serialized attrs, so
pushed nodes are self-identifying exactly like server-rendered ones
(`src/ryzom/components.py`). This is a shared-lib fix and also benefits the chat
example's DDP inserts.

### 2. `connectedCallback` fires before children are parsed

A parser-created custom element's `connectedCallback` can run before its child
`<input>`s exist, so `this.querySelector('input…')` returns `null`. Defer wiring
to `document.readyState`/`load` (see `ProductFilter`/`ProductCreateForm`). This
is why search/filter "did nothing" until fixed.

### 3. `ryzom.js` re-dispatches `load` after every DDP patch

`constructDOM`/`removeDOM` call `dispatchEvent(new Event('load'))`, so any
component that defers wiring to `load` gets `init()` re-run on every patch.
Guard `init()` with an idempotency flag (`this.wired`) or you stack duplicate
event listeners → one toggle fires N requests.

### 4. The filter mutates server state, so serialize the requests

`ProductFilterView` does a read-modify-write of the subscription's stored
queryset. Overlapping requests interleave it and desync from the DOM. The
`ProductFilter` element keeps **one request in flight** and re-sends the latest
state on completion.

---

## Request/URL map

| URL | View | Method | Purpose |
|-----|------|--------|---------|
| `/crud/products/` | `ProductListView` | GET | live table + create form |
| `/crud/products/<pk>/` | `ProductDetailView` | GET | auto-updating detail |
| `/crud/products/create/` | `ProductCreateView` | POST | create → `insert` push (returns 204) |
| `/crud/products/<pk>/sell/` | `ProductSellView` | POST | stock−1 → `change` push (returns 204) |
| `/crud/products/filter/` | `ProductFilterView` | POST | update sub opts → `insert`/`remove` delta (returns 204) |
| `/ws/ddp/?<token>` | channels `Consumer` | WS | the push channel |
