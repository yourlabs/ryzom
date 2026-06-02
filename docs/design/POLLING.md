# Polling fallback: client-pull live lists where push is not allowed

This document states the design choices and implementation plan for running the
reactive Product demo (and `ryzom_django_channels` in general) **without any
server-initiated communication** — i.e. with HTTP polling instead of the
websocket push.

It is a companion to `PROBLEM.md` (which is about *computing* the per-write
delta). This document is about *transporting* that delta when the only thing the
server is allowed to do is **answer a request the client made**.

---

## 1. The constraint

> No communication from outside to the client that is not client-initiated.

Every byte that reaches the browser must be the response to a request the
browser itself issued. This rules out, for these deployments:

- **websockets** (the server pushes frames unprompted),
- **server-sent events / long-poll-hold** (the server holds a connection open
  and writes when *it* decides),
- a server-driven **outbox delivery** (anything where the server "sends" queued
  messages).

The only shape that satisfies the constraint is **client-pull**: the browser
asks "what changed for me?" on its own schedule, and the server *only ever
responds*. This is Meteor's poll-and-diff, pulled by the client.

It also subsumes the weaker reading "websockets are blocked / `CHANNELS_ENABLE`
is off": a client-pull transport needs **no Redis, no Celery, no Channels, no
ASGI** — it runs over plain WSGI request/response. So the same mechanism is both
the strict-constraint answer and the no-infra answer.

---

## 2. The key structural fact: computation and transport are separable

The live list already works in two independent halves, and only the second is
coupled to the websocket:

**Delta computation — transport-agnostic, already correct (see `PROBLEM.md`):**

| Piece | Role |
|-------|------|
| `Subscription.get_queryset()` (`models.py`) | re-window a subscription, persist its id list into `qs` |
| `signals._push_window_delta()` (`signals.py`) | diff old `qs` vs. new window → the minimal `insert`/`change`/`remove` ops, incl. pagination ripple |
| `signals._candidate_ids()` (`signals.py`) | reverse-match a changed row to only the subscriptions it can affect (facets) |

**Transport — the only websocket-coupled part:**

| Piece | Role |
|-------|------|
| `ddp.send_insert/change/remove` (`ddp.py`) | serialize a row (`to_obj()`) and push onto `sub.client.channel` via the channel layer |
| `Consumer.handle_ddp` (`consumers.py`) | wrap as `{type:'DDP', params:{…}}` and write to the socket |
| `ryzom.js:handleDDP` / `constructDOM` / `changeDOM` / `removeDOM` | apply the op to the DOM |

The browser-side renderer and the whole diff engine are reusable **unchanged**.
Polling replaces only the middle pipe: instead of the server pushing DDP
messages onto a channel, the browser **pulls** the same DDP messages over HTTP
and feeds them through the same `handleDDP`.

Crucially, `send_*` already early-return when `sub.client.channel == ''`
(`ddp.py`), so a polling client — which never has a channel — is a no-op for the
push path by construction. **Polling must not go through `send_*`**; it must
compute the same ops and return them in the HTTP response.

---

## 3. The design: diff-on-poll

> When a client has no socket, it `POST`s its token to a poll endpoint on its own
> `setInterval`. The server, for each of that client's subscriptions, recomputes
> the window and diffs it against the subscription's stored `qs` — the same diff
> `_push_window_delta` does — but **collects** the ops into a JSON list instead of
> sending them over the channel layer, and returns them. The client feeds each op
> into the existing `handleDDP`.

Why this shape and not the alternatives:

- **`Subscription.qs` is already the per-client cursor.** It stores the last
  *membership* (which rows, in what order) the client was brought to. So the
  diff needs no outbox, no message queue, no sequence numbers — the subscription
  row *is* the high-water mark for inserts/removes/reorders. Recompute window,
  diff vs. `qs`, return ops, persist new `qs`. (One thing `qs` does *not*
  capture is an in-window row whose *content* changed without changing
  membership; the push path knows that from `changed_pk`, the poll path recovers
  it from a small per-row content fingerprint stored alongside `qs` — see §11.)
- **No new infra.** Pure DB + request/response. Works with
  `CHANNELS_ENABLE=False`.
- **Pixel-identical to the push path**, because it emits the *same ops* through
  the *same* client renderer — not a re-render of the whole table.

### Why not the others

| Approach | Verdict |
|----------|---------|
| Websocket, fall back on failure | Violates the constraint (server pushes). Not opened at all in poll deployments. |
| Server-sent events / long-poll-hold | Server writes unprompted on a held connection. Violates the constraint. |
| Server-delivered outbox | Still presumes the server eagerly computes deltas from signals and *delivers* them. Pointless when the poll request can diff on demand. |
| Full-window re-render each tick | Reuses only `get_queryset` + SSR, not `handleDDP`. Flicker, lost scroll/focus, no minimal delta. Acceptable only as a crude stopgap. |

Diff-on-poll has the same infra cost as the crude re-render but is identical to
the websocket result.

---

## 4. The one refactor that makes it clean

`_push_window_delta` currently **interleaves computing the delta with sending
it** — it calls `send_change`/`send_insert`/`send_remove` inline
(`signals.py`). Split it:

- Extract a pure generator, e.g. `iter_window_ops(sub, changed_pk)`, holding all
  the window/ripple logic and **yielding ops** —
  `('insert', position, obj)`, `('change', obj)`, `('remove', dom_id)` — with no
  I/O.
- Two thin emitters consume it:
  - **channel emitter** (existing behaviour): for each op call the matching
    `ddp.send_*`. `_push_window_delta` becomes this.
  - **poll emitter** (new): for each op build the same
    `{type:'insert'|'change'|'remove', params: tmpl(obj).to_obj()}` dict the
    consumer builds in `insert_component`/`remove_component` (`consumers.py`),
    and append to a list.

This removes the duplicated serialization shape, gives the diff logic exactly
one home, and kills the latent hazard of two code paths that must agree on
positions. It is **behaviour-preserving and shippable on its own**, before any
polling code lands.

---

## 5. Changes by file

### Server

1. **`signals.py`** — extract `iter_window_ops(sub, changed_pk)` (pure delta) out
   of `_push_window_delta`; keep `_push_window_delta` as its channel-layer
   consumer. No behaviour change.

2. **A generic poll view** in `ryzom_django_channels/views.py` (not
   Product-specific):
   - look up `Client` by token (same pattern as `ProductFilterView`);
   - bump `client.last_seen` (see §6);
   - for each `Subscription` of that client: `select_for_update`, run
     `iter_window_ops`, build DDP message dicts;
   - for each `Registration` of that client: re-render and emit a `change` only
     if its content changed (see §7);
   - return `JsonResponse({'messages': [...]})`.

   Note: the poll path does **not** use `_candidate_ids`. That reverse-match
   exists to avoid touching every subscription on a *global* write. A poll
   request only re-windows *this one client's* subscriptions — bounded and
   cheap — so it just diffs them directly.

3. **`views.py` / `urls.py`** — register the poll endpoint
   (`path('poll/', …)`).

4. **`ReactiveMixin.get_token`** (`views.py`) — add to the `ryzom-config` meta:
   - `data-transport` = `"ws"` when `CHANNELS_ENABLE` else `"poll"`,
   - `data-poll-interval` (ms),
   so the client knows the mode up front and **never constructs a `WebSocket`**
   in poll mode.

### Client (`ryzom.js`)

5. `getRyzomConfig` — read `transport` + `poll_interval`.

6. Bootstrap branch (currently auto-connects the socket): if
   `transport === 'poll'`, **do not open a socket** — call `init()` and start
   `setInterval(poll, interval)`. The websocket branch is untouched for
   push-capable deployments.

7. `poll()` = `fetch(pollUrl, {token})` → `data.messages.forEach(handleDDP)`. The
   renderer is unchanged; positions/ids line up because the server diffs against
   the same stored `qs`.

### Unchanged

The mutation widgets — `SellButton`, `ProductCreateForm`, `ProductFilter`,
`ProductPager` — already `fetch`+204 and rely on the update arriving separately.
Under polling it simply lands on the next tick (latency ≈ poll interval). No
change required.

> Optional later enhancement: have the mutate endpoints return the *originating*
> client's own delta in their response body, so the actor sees an instant local
> update while other clients wait for their next poll. This stays within the
> constraint (it is the response to the client's own POST).

---

## 6. Lifecycle / cleanup — the one genuinely new problem

The websocket gives a free `disconnect` that deletes the `Client` and cascades
its `Subscription`s (`consumers.py`). Polling has **no disconnect**, so those
rows would accumulate forever.

Fix: add `Client.last_seen`, bump it on every poll, and sweep stale clients. The
disconnect handler already TTL-sweeps `channel=''` clients older than 2 minutes;
generalize that into a periodic cleanup keyed on `last_seen < now - TTL`
(management command, or a lazy sweep at the top of the poll view), with TTL a
small multiple of the poll interval.

---

## 7. The detail view (Registration) under polling — deferred

The detail page is a `Registration`, refreshed today by
`models.py:_refresh_product_detail` over the channel layer. Under polling the
poll view would re-render the client's registered components and emit a `change`
**only when the output differs** from last time (a content hash, as the list
already does — see §11).

**It is deferred in this first cut**, for a concrete reason: a `Registration`
stores *what* component to re-render (`subscriber_class`/`module`/`id`/`parent`)
but **not the constructor args** it needs — `RegisterManager.refresh(instance)`
relies on the *caller* (the `post_save` receiver) to supply the changed
instance. A generic poll handler has no such caller, so it cannot rebuild
`ProductDetail(product)` without a way to recover `product` from the
registration. The register name encodes the pk (`product-detail-<pk>`), but
decoding it back to a model fetch is app-specific.

Closing it cleanly means giving a registration a **refresh recipe** (e.g. the
model + pk, or a small "rehydrate" hook on the component) so the poll view can
reconstruct the args the same way for any registered component. That is its own
small design step; the list view — the headline feature — works without it.
`poll_client` therefore handles subscriptions only and leaves registrations
untouched.

---

## 8. What the constraint removes from the design

- **No websocket fallback-after-failure.** Poll mode never opens a socket; it is
  a deterministic, server-advertised setting (`data-transport`), not something
  auto-detected by letting a socket fail.
- **No outbox delivery.** Diff on demand in the poll handler instead.
- **No server-initiated `Reload` / `pong` nudges.** Today `Consumer.connect`
  sends `Connected`/`Reload` and answers pings — all server-initiated. In a
  client-pull deployment none of that exists; the **poll response is the only
  channel** for "you're stale, re-sync", which the diff already handles
  implicitly (e.g. a poll after a server restart returns a full window
  replacement). The client must not assume any server-sent `Reload`.

---

## 9. Plan (phased, each step shippable)

1. ✅ **Refactor** `_push_window_delta` → pure `iter_window_ops` + channel
   emitter. Behaviour-preserving; landed on its own. (`signals.py`, `ddp.py`)
2. ✅ **Poll endpoint** (generic `ddp_poll` in `ryzom_django_channels.views`) +
   `Client.last_seen` + `polling.sweep_stale_clients`.
3. ✅ **Client**: config-driven transport switch; `poll_once` feeding
   `handleDDP`; no socket in poll mode. (`static/ryzom.js`)
4. ⏳ **Registration polling**: blocked on the refresh-recipe step in §7.
5. ⏳ **Optional**: actor-local instant delta from the mutate endpoints; interval
   tuning (jitter, idle backoff).

---

## 10. Mental model

A subscription is a *standing query* whose last delivered state is its stored
`qs`. Push and poll are **two emitters over one diff**: push runs the diff on
every write and speaks unprompted; poll runs the same diff inside a request the
client made and speaks only in reply. The constraint "client-initiated only"
just means we keep the diff and drop the unprompted speaker.

---

## 11. What landed (implementation notes)

**Files**

| File | Change |
|------|--------|
| `signals.py` | `iter_window_ops(sub, changed_pk)` — pure delta generator; `_push_window_delta` is now a thin channel emitter over it. |
| `ddp.py` | `_row_obj` / `_remove_ref` extracted; `client_message(sub, tmpl, kind, instance)` builds the `{type, params}` a polling client applies. `send_*` unchanged on the wire. |
| `polling.py` *(new)* | `poll_client(client)`, `_poll_subscription(sub)`, `_fingerprint(instance)`, `sweep_stale_clients(ttl)`. |
| `views.py` | `ddp_poll` view + `_transport()`; `get_token` meta now carries `data-transport` / `data-poll-url` / `data-poll-interval`. |
| `models.py` | `Client.last_seen` (+ migration `0008`). |
| `static/ryzom.js` | reads the transport attrs; in `poll` mode runs `poll_start` (no `WebSocket`). |
| `ryzom_example_crud/{views,…}` | mounts `poll/`; `settings.py` adds `RYZOM_TRANSPORT` / `POLL_URL` / `POLL_INTERVAL` / `POLL_TTL`. |

**Two concrete decisions made while implementing**

- **Idle polls stay empty via a per-row fingerprint.** The push path knows the
  one `changed_pk`; the poll path doesn't, so to avoid re-`change`ing the whole
  window every tick it stores a content hash per visible row in
  `Subscription.options['_fp']` and emits a `change` only where the hash moved.
  A row with no prior hash (just server-rendered, or just inserted) is left
  alone — its DOM is already fresh.
- **Reorders fall back to a full window replace.** Removes-first +
  inserts-in-ascending-position (the existing filter/pager reconciliation)
  cannot express a *reorder* of surviving rows with position ops, so when the
  surviving rows' relative order changes, `_poll_subscription` removes the whole
  old window and re-inserts the new one in order. Always correct; only triggered
  by an actual reorder, never by an idle poll.

**Endpoint shape.** `ddp_poll` is a token-authenticated `GET` (the token is the
capability, exactly like the websocket — so no CSRF, and it works on pages
without a form), returns `{messages: [...]}` (or `{reload: true}` for an unknown
/ swept client) with `Cache-Control: no-store`.

## 12. Run it in poll mode

```bash
# Force the client-pull transport even with Redis/Channels available:
RYZOM_TRANSPORT=poll python manage.py runserver
# open http://127.0.0.1:8000/crud/products/ in two tabs
```

No Redis, Celery, daphne or websocket is involved on this path — the page polls
`/crud/products/poll/` every `POLL_INTERVAL` ms and applies the returned deltas.
Add/sell/filter/page in one tab; the other reflects it within one interval.

Tests: `tests/test_polling.py` (idle-empty, insert/change/remove, reorder
replace, the HTTP endpoint, and the sweep).
