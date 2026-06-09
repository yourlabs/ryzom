# Plan — Persist reactive subscriptions across transient WebSocket disconnects

**Status:** ready to implement
**Branch:** `reactive`
**Package:** `ryzom_django_channels`
**Authoring context:** investigated 2026-06-08 for the DINUM project, where bureau
tables "stop updating live" intermittently and only recover on a full page reload
(disruptive). Shared library — also used by `electis` and `cse`, so changes must
be backward compatible and covered by tests.

---

## 1. The bug, precisely

A reactive component (`SubscribeComponentMixin` for lists, `ReactiveComponentMixin`
for single components) persists its server→client binding in the DB:

- `Client` — one row per connected browser (`token` unique, `channel` = the
  Channels channel name). `src/ryzom_django_channels/models.py:17`.
- `Subscription` — `client = ForeignKey(Client, models.CASCADE)`, plus the
  publication and the live `qs` (the list of ids currently shown).
  `models.py:87` (FK at `models.py:99`).
- `Registration` — `client = ForeignKey(Client, models.CASCADE)`, the single
  component register. `models.py:48` (FK at `models.py:50`).

On a WebSocket disconnect the consumer **deletes the Client row**, which
**cascade-deletes every Subscription and Registration** for that browser:

```python
# src/ryzom_django_channels/consumers.py:52  (disconnect)
clients = Client.objects.filter(channel=self.channel_name)
for c in clients:
    clear_queue(c.token)
clients.delete()                      # <-- CASCADE → Subscription + Registration gone
```

On reconnect the browser re-opens the socket with the **same token** (it lives in
the server-rendered `<meta name="ryzom-config" content="TOKEN">` tag, read on
every connect — `static/ryzom.js:290`, appended to the URL at `ryzom.js:329`).
The consumer tries to re-bind by token:

```python
# consumers.py:22 (connect)
client = Client.objects.filter(token=token).last()
...
if client and client.channel != self.channel_name:
    client.channel = self.channel_name; ...; self.send({'type': 'Connected'})
elif not client:
    self.send({'type': 'Reload'})      # <-- token unknown → force full reload
```

**Why live updates die:**

1. A redeploy / Daphne restart / network blip drops the socket.
2. `disconnect()` deletes the Client → all its Subscriptions/Registrations vanish.
3. The browser reconnects with its token, but the row is gone, so the server
   sends `'Reload'` → `document.location.reload()` (`ryzom.js`, `case 'Reload'`).
4. If the reload is slow, racing with another blip, or the user has navigated,
   the bindings never come back and the table is frozen.

Even in the lucky race where the Client row still exists at reconnect, its
Subscriptions were already cascade-deleted, so nothing pushes until a reload
re-renders the components (which is what recreates the subscriptions, in
`SubscribeComponentMixin.create_subscription` / `ReactiveComponentMixin.create_registration`).

There is a reaper meant to clean zombies, but it keys off **creation** time, not
disconnect time, so it cannot be used to hold a row open after a disconnect:

```python
# consumers.py:66
expiration = timezone.now() - timedelta(minutes=2)
deadclients = Client.objects.filter(channel='', transport='ws', created__lt=expiration)
deadclients.delete()
```

---

## 2. Fix strategy

**Core idea:** a WebSocket disconnect is almost always *transient*. Stop
destroying the Client (and its Subscriptions/Registrations) on disconnect. Mark
the client *detached* instead, keep its bindings, and let a same-token reconnect
re-attach the channel. A reaper deletes clients that stay detached past a grace
period (those are the genuinely-gone tabs).

That alone makes live updates resume after a blip **for future changes**. The one
remaining correctness gap is **state drift**: while detached, model saves still
run the signal, which advances `Subscription.qs` (via `get_queryset()`) but the
actual `send_*` is a no-op because the channel is empty
(`ddp.py:_client_is_available` returns False for ws + empty channel,
`ddp.py:10`). So the server believes the client is in sync while the browser DOM
is stale, and the next change only sends the *new* delta.

We close that gap with a **dirty flag**: whenever a push is skipped because the
client is detached, mark the client `needs_resync`. On reconnect:

- `needs_resync == False` → send `'Connected'` (seamless; DOM still correct, subs
  intact, live updates just resume). **This is the common case** (blip with no
  data change) and removes the constant reload.
- `needs_resync == True` → send `'Reload'` (exactly one clean reload rebuilds the
  DOM from current state). Correct, and only when something actually changed.

This maps onto the **existing** JS with no client changes: `ryzom.js` already does
`init()` on `'Connected'` and `document.location.reload()` on `'Reload'`.

> Strategy note: a fuller "live resync without reload" (Strategy 1, §7) is
> possible but riskier; do the dirty-flag version first — it already turns
> "reload on almost every blip" into "reload only when data changed while away".

---

## 3. Schema change

Add two fields to `Client` (`src/ryzom_django_channels/models.py:17`):

```python
detached_at = models.DateTimeField(null=True, blank=True)
needs_resync = models.BooleanField(default=False)
```

- `detached_at` — set on disconnect, cleared on reconnect; the reaper keys off
  this (not `created`).
- `needs_resync` — set when a push is skipped due to a detached channel; consumed
  on reconnect.

New migration: `src/ryzom_django_channels/migrations/0009_client_detached_resync.py`
(additive, both fields nullable / defaulted → safe for `electis` and `cse`).

---

## 4. Consumer changes (`src/ryzom_django_channels/consumers.py`)

### 4.1 `disconnect()` — detach, don't delete (replaces lines 52–70)

```python
def disconnect(self, close_code):
    from ryzom_django_channels.models import Client
    # Detach (keep the row + its Subscriptions/Registrations) so a same-token
    # reconnect can re-attach and resume live updates. Genuinely-gone tabs are
    # removed by the grace-period reaper below.
    Client.objects.filter(channel=self.channel_name).update(
        channel='', detached_at=timezone.now())

    # Reap clients detached longer than the grace period (their bindings are
    # cascade-deleted with them), plus never-attached zombies from page loads
    # that opened no socket.
    grace = timezone.now() - timedelta(
        seconds=getattr(settings, 'RYZOM_CLIENT_GRACE_SECONDS', 900))  # 15 min
    Client.objects.filter(transport='ws', detached_at__lt=grace).delete()
    Client.objects.filter(
        transport='ws', channel='', detached_at__isnull=True,
        created__lt=timezone.now() - timedelta(minutes=2),
    ).delete()
```

Notes:
- Do **not** `clear_queue` here. The poll queue is keyed by token and a detached
  ws client may immediately come back; the queue (if any) is harmless and TTL'd.
  (Poll clients never hit the ws `disconnect()` anyway.)
- `RYZOM_CLIENT_GRACE_SECONDS` (default 900) lets each project tune retention.

### 4.2 `connect()` — re-attach and decide Connected vs Reload (replaces lines 22–50)

Keep the existing token-login block, then:

```python
self.accept()
if client:
    client.channel = self.channel_name
    if not client.user and isinstance(user, User):
        client.user = user
    resync = client.needs_resync
    client.detached_at = None
    client.needs_resync = False
    client.save(update_fields=['channel', 'user', 'detached_at', 'needs_resync'])
    # Reload only if something changed while this client was detached; otherwise
    # the DOM is still correct and subscriptions are intact — resume seamlessly.
    self.send(json.dumps({'type': 'Reload' if resync else 'Connected'}))
else:
    # Unknown/expired token (reaped after grace, or first-ever connect): the
    # browser must reload to obtain a fresh token + re-render its components.
    self.send(json.dumps({'type': 'Reload'}))
```

### 4.3 `receive()` guard (lines 86–88)

`receive()` currently sends `'Reload'` when no Client matches `self.channel_name`.
After 4.2 the channel is re-attached on reconnect before any `receive()` can run,
so this stays as a correct last-resort. No change required, but verify the
re-attach happens in `connect()` (it does) so a healthy reconnect never trips it.

---

## 5. Dirty-flag on skipped pushes

Mark a detached client `needs_resync` wherever a push is dropped because the
channel is empty. Use a single cheap conditional UPDATE (no-op once already set):

Add a helper (e.g. in `src/ryzom_django_channels/ddp.py`):

```python
def _mark_needs_resync(client):
    if client is None or client.transport == 'poll':
        return
    from ryzom_django_channels.models import Client
    Client.objects.filter(pk=client.pk, needs_resync=False).update(needs_resync=True)
```

Call it from the three send functions where they early-return on an unavailable
ws client (`ddp.py:send_insert`, `send_change`, `send_remove` — each begins with
`if not _client_is_available(sub.client): return`):

```python
if not _client_is_available(sub.client):
    _mark_needs_resync(sub.client)
    return
```

And from `RegisterManager._replace` (`src/ryzom_django_channels/views.py`), in the
branch where the registration's client has no channel. Today it calls
`self.defer(...)` which spins a thread waiting up to 10 s
(`views.py:wait`); keep that best-effort path, but also mark resync so a longer
gap still triggers a reload on reconnect:

```python
else:
    _mark_needs_resync(registration.client)
    self.defer(registration.client, content)
```

> Poll clients are never "detached" in the ws sense (they pull from a Redis queue
> by token via `PollReceiveView`), so `_mark_needs_resync` ignores them — their
> messages wait in the queue and are drained on the next poll.

---

## 6. Tests

Extend `tests/test_django_channels.py` (existing: `test_ws_connect`,
`test_ws_reload`, `test_ws_connected`, `test_register_changed`).

New / updated cases:

1. **Detach keeps bindings** — connect with a token, create a Subscription +
   Registration, disconnect; assert the `Client`, `Subscription`, and
   `Registration` rows still exist and `client.channel == ''`,
   `client.detached_at` is set.
2. **Clean reconnect → Connected** — after 1, reconnect with the same token with
   `needs_resync == False`; assert the server sends `'Connected'` (not
   `'Reload'`), `channel` is re-attached, `detached_at` cleared, and the
   Subscription/Registration are unchanged.
3. **Dirty reconnect → Reload** — after 1, set `needs_resync = True` (or trigger a
   publishable save while detached and assert the flag got set by the send path),
   reconnect; assert the server sends `'Reload'` and the flag is cleared.
4. **Skipped push marks resync** — with a detached client owning a subscription,
   save a publishable model; assert `send_*` was a no-op AND
   `client.needs_resync` became True.
5. **Grace reaper** — a client with `detached_at` older than
   `RYZOM_CLIENT_GRACE_SECONDS` is deleted on the next `disconnect()`; one within
   grace survives. A never-attached client (`detached_at IS NULL`,
   `created` > 2 min) is still reaped.
6. **Unknown token → Reload** — connect with a token whose Client was reaped;
   assert `'Reload'` (existing `test_ws_reload` covers the no-token case; add the
   stale-token case).

Run the whole package suite (`pytest` at the ryzom root) — `test_polling.py`
must stay green (poll path untouched by design; confirm `_mark_needs_resync`
ignores poll clients).

---

## 7. Optional follow-up — live resync without a reload (Strategy 1)

Eliminates even the single reload in the dirty case, at higher cost/risk. On a
dirty reconnect, instead of `'Reload'`:

- **Registrations:** call the equivalent of `RegisterManager.refresh()` for each
  of the client's Registrations — `_replace` already re-renders the full
  component and sends a `'changed'` (full replace). Reusable as-is.
- **Subscriptions:** harder — the protocol is per-item insert/remove/change and
  the server's `sub.qs` has already advanced past what the browser holds. Need a
  "replace whole container" op: reset `sub.qs = []`, instruct the client to clear
  the subscriber container, then re-run `get_queryset()` and `send_insert` every
  current item. Requires a small JS addition (a `clear`/`resync` DDP op in
  `handleDDP`, `ryzom.js:116`) and a server method to drive it.

Defer this until the dirty-flag version is shipped and proven; it removes the
last reload but touches the JS client and the subscription protocol.

---

## 8. Rollout / risk

- **Shared library.** `electis`, `cse`, and `dinum` all depend on this. The schema
  change is additive (nullable / defaulted) and the protocol is unchanged
  (`Connected` / `Reload` already handled by every client). Ship the migration
  with the code; each project runs `migrate` on deploy.
- **Behavior change.** Clients now persist up to the grace period instead of being
  deleted on disconnect → a bounded increase in `Client`/`Subscription` rows.
  `get_token()` already creates a fresh Client per page load, so churn exists
  today; the reaper (now keyed on `detached_at`) bounds it. Tune
  `RYZOM_CLIENT_GRACE_SECONDS` per project (default 15 min).
- **Security.** A token already grants channel re-bind (status quo). Holding the
  Client row open for the grace period widens the re-bind window slightly; the
  grace setting bounds it. No new capability is exposed.
- **Reaper cadence.** Reaping runs opportunistically inside `disconnect()` (as
  today). On a quiet system few disconnects fire, so also keep the
  `apps.ready()` boot-time zombie sweep (`AppConfig.ready()`), and consider a
  periodic Celery/`manage.py` reap if a project needs tighter bounds — note this
  but it is optional.
- **Validation in DINUM.** After the library bump, smoke-test the bureau pages:
  member tables update live across a Daphne restart without a reload (clean
  reconnect), and a row changed *during* the restart shows exactly one reload on
  reconnect. See the DINUM memory `ceremony-ui-reactivity` for the affected
  pages (member tables push live on `MembreBVEC` save; task cards are
  reload-only by design).

---

## 9. File-change checklist

- [ ] `src/ryzom_django_channels/models.py` — add `Client.detached_at`,
      `Client.needs_resync` (~line 17).
- [ ] `src/ryzom_django_channels/migrations/0009_client_detached_resync.py` — new.
- [ ] `src/ryzom_django_channels/consumers.py` — rewrite `disconnect()` (52–70)
      to detach + grace-reap; rewrite `connect()` tail (43–50) to re-attach and
      branch `Connected`/`Reload` on `needs_resync`.
- [ ] `src/ryzom_django_channels/ddp.py` — add `_mark_needs_resync`; call it in
      `send_insert`/`send_change`/`send_remove` unavailable-client guards (~10–
      180).
- [ ] `src/ryzom_django_channels/views.py` — call `_mark_needs_resync` in
      `RegisterManager._replace` no-channel branch.
- [ ] `tests/test_django_channels.py` — add cases §6 (1–6).
- [ ] (optional) settings doc: `RYZOM_CLIENT_GRACE_SECONDS` (default 900).
- [ ] Bump version / CHANGELOG entry; coordinate the dependency bump in
      `dinum`, `electis`, `cse`.
```
