# ryzom_example_crud

Two **live, server-pushed** CRUD demos, each a thin declarative subclass of the
generic **`ReactiveRouter`** (`ryzom_django_mdc.reactive`):

- **Products** (`/crud/products/`) — `ProductCrud` in `components.py` over the
  `Product` model.
- **Users** (`/crud/users/`) — `UserCrud` in `crud.py` over a `LiveUser`
  Publishable proxy of `auth.User` (see "Making a non-Publishable model live"
  below). `crud.py` also keeps a small classic `UserRouter` purely for the
  auth shell (home / login / logout).

You give `ReactiveRouter` a model + `columns` / `facets` / `actions` and get the
whole suite — live table, search/filter, click-to-sort, pager, bulk + per-row
actions, create form, auto-updating detail — over a websocket (or polling). The
generic components live in `ryzom_django_mdc/reactive.py`; this app only supplies
the model-specific bits (custom cell renderers, action handlers, a Sell button).

This README documents the **reactive plumbing** underneath, since that's the
non-obvious part — what `ReactiveRouter` automates for you.

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
| `models.py` | `Product(Publishable, Model)` + `LiveUser` (Publishable proxy of `auth.User`). Each `@publish` method registers a named publication; `post_save` receivers refresh open detail views. |
| `components.py` | `ProductCrud(ReactiveRouter)` + the Product-only bits: custom cell renderers (group badge, low-stock chip), action handlers, the `SellButton` custom element + its endpoint. |
| `crud.py` | `UserCrud(ReactiveRouter)` over `LiveUser`, plus a small classic `UserRouter` kept only for `get_auth_urls()` (home/login/logout). |
| `views.py` | One-liner: `urlpatterns, app_name = ProductCrud.get_urls()`, with `ProductListView`/`ProductBulkView` aliases for tests. |
| `migrations/` | The `Product` table + the `LiveUser` proxy. |

The reactive components and the `ReactiveRouter` itself live in
**`src/ryzom_django_mdc/reactive.py`** — `ProductCrud` just configures them.
`ReactiveRouter.__init_subclass__` generates the per-model `ProductRow` /
`ProductRows` / `ProductDetail` classes (named after the model) into the router's
module and registers the `product-row` template, so the push/poll layer
reconstructs them exactly as a hand-written demo would. Each declarative knob maps
to a generated piece:

| Router config | Generates |
|---------------|-----------|
| `columns` | the `<tr>` cells + sortable thead; custom `cell(obj)` renderers for chips/buttons |
| `facets` | the search/filter UI **and** the reverse routing of a write to affected subscriptions |
| `order` / `paginate_by` | the subscription's total order + paged window |
| `actions` | the bulk toolbar + per-row ⋮ menu + their confirm/input dialogs |
| `create_fields` / `detail_fields` | the fetch-POST create form + the live detail card |

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
  reads `opts` (`q`, `in_stock`) that live on the `Subscription`. The generic
  `ReactiveFilter` widget POSTs to the router's filter view, which updates the
  subscription's stored opts, recomputes the queryset, and pushes the membership
  delta (`send_insert`/`send_remove`) — the exact same machinery the save signals
  use. Because the opts are stored, every later publication push re-applies the
  filter, so the live table stays filter-correct. The widget finds *which*
  subscription to update via the page's `ryzom-config` token.

---

## Making a non-Publishable model live (the Users demo)

The push routes a write to its publication by the **saved instance's class**:
`signals.py` gates on `Publishable in type(instance).mro()` and matches
`instance.__module__` + `type(instance).__name__` against the publication. So a
model you don't own (here `auth.User`) is made live with a **Publishable proxy**:

```python
class LiveUser(Publishable, User):
    class Meta:
        proxy = True
    @publish
    def users(cls, user):
        return cls.objects.all()
```

`UserCrud` points at `LiveUser`, so its create/update/delete go through the proxy
and push. Plain `auth.User` saves (login, admin) keep their own class and **don't**
push — the intended scope for the demo. The proxy needs a (state-only) migration
and a `ContentType`, both produced by `makemigrations`.

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

The router's filter view does a read-modify-write of the subscription's stored
queryset. Overlapping requests interleave it and desync from the DOM. The
`ReactiveFilter` element keeps **one request in flight** and re-sends the latest
state on completion.

---

## Request/URL map

All but `sell/` are generated by `ReactiveRouter.get_urls()` (the same set exists
under `/crud/users/`); `sell/` is Product-specific, added via `extra_urls()`.

| URL | Method | Purpose |
|-----|--------|---------|
| `/crud/products/` | GET | live table + create form |
| `/crud/products/<pk>/` | GET | auto-updating detail |
| `/crud/products/create/` | POST | create → `insert` push (returns 204) |
| `/crud/products/<pk>/sell/` | POST | stock−1 → `change` push (returns 204, Product-only) |
| `/crud/products/filter/` | POST | update sub opts → delta (JSON: `[]` in push mode, the rows in poll mode) |
| `/crud/products/sort/` · `page/` · `bulk/` | POST | re-sort / paginate / run a bulk action → delta (same JSON shape) |
| `/crud/products/poll/` | GET | client-pull transport (POLLING.md) |
| `/ws/ddp/?<token>` | WS | the push channel |
