# MR !68 — review comments: analysis & fixes

Maintainer **jpic** formally **requested changes** on MR !68
(`crud-example` → `master`) on 2026-06-09, with a follow-up UI request on
2026-06-16. This file maps each comment to the **current code** and proposes a
concrete fix per item.

> Scope note: the MR head is `1c20c1a` (= current git `HEAD`). The working tree
> has uncommitted WIP on top (`ryzom_django_mdc/crudlfap.py` deleted →
> `crud.py` + new `reactive.py`, plus `ryzom_example_crud/*` rewritten). Line
> numbers in the original comments are from the 2026-06-09 state; everything
> below is located against the **current** code.

## Status at a glance

| # | Topic | File | Current state | Effort |
|---|-------|------|---------------|--------|
| 1 | Background sweep via Celery | `ryzom_django_channels/views.py` | Not addressed | Small (but see caveat) |
| 2 | Restore auto-generated API docs | `docs/source/` | Not addressed | Small |
| 3 | Simplify `getattr(...) or ...` | `py2js/transpiler.py` | Not addressed | Trivial |
| 4 | Explicit `if/else` for `in_str` | `py2js/transpiler.py` | Not addressed | Trivial |
| 5 | Drop vendored autocomplete assets | `ryzom_django_autocomplete/` | Not addressed | Small |
| 6 | No Subscription creation on GET | `ryzom_django_channels/` | Not addressed (design conflict) | **Large** |
| 7 | Restore empty DB defaults | `ryzom_django_example/settings.py` | Not addressed | Small |
| 8.1 | Click-to-sort columns | `ryzom_django_mdc/reactive.py` | **Already done** | — |
| 8.2 | Rows-per-page MDC select | `ryzom_django_mdc/reactive.py` | **Already done** | — |
| 8.3 | Material filter form | `ryzom_django_mdc/reactive.py` | **Already done** | — |
| 8.4 | Delete action (red trash, modal, new-tab) | `ryzom_django_mdc/reactive.py` | Partial (modal yes; no icon/URL) | Medium |
| 8.5 | Edit action (orange pen, ModelForm modal, new-tab) | `ryzom_django_mdc/reactive.py` | Missing | Medium |

---

## 1. Send the stale-client sweep via Celery — `ryzom_django_channels/views.py`

**Comment (jpic):** "Ca serait sympa de l'envoyer en background avec celery" — send it in the background with Celery.

**Current state:** Not addressed. `src/ryzom_django_channels/views.py:78` still runs the sweep synchronously inside `ddp_poll`:

```python
# views.py:77-79
else:
    sweep_stale_clients(getattr(settings, 'POLL_TTL', 60))
    resp = http.JsonResponse({'messages': poll_client(client)})
```

`sweep_stale_clients` (`polling.py:145`) is a repo-wide `Client.objects.filter(...).delete()` (cascades to subscriptions). Its result is **not** used in the response, yet every poll from every client pays for the scan/delete synchronously.

**Proposed solution:** Wrap it in a Celery task and fire-and-forget, mirroring the existing `ddp_process_task.delay(...)` pattern in `signals.py` (`celery.py` defines `app`):

```python
# signals.py
@celery_app.task()
def sweep_stale_clients_task(ttl_seconds):
    from ryzom_django_channels.polling import sweep_stale_clients
    sweep_stale_clients(ttl_seconds)
```

```python
# views.py:78
    else:
        from ryzom_django_channels.signals import sweep_stale_clients_task
        sweep_stale_clients_task.delay(getattr(settings, 'POLL_TTL', 60))
        resp = http.JsonResponse({'messages': poll_client(client)})
```

**Caveats — worth raising back to jpic before implementing:**
- This is the **poll transport**, which by design runs *without a Celery worker* (CLAUDE.md: poll mode = "no worker/ws"). If the sweep is pushed to Celery and no worker/broker is up, stale clients accumulate forever. A **Celery beat periodic task** (global housekeeping, not per-poll) is the cleaner fit.
- `.delay()` needs a broker (Redis); under `CELERY_TASK_ALWAYS_EAGER` it runs synchronously anyway.
- Only the side-effecting *sweep* can be backgrounded — `poll_client(client)` builds the HTTP body and must stay synchronous.

---

## 2. Restore the auto-generated API docs — `docs/source/`

**Comment (jpic):** "Pourquoi t'as enlevé les docs d'API auto-générées ? Je pense qu'on en a tjs besoin" — why did you remove the auto-generated API docs? we still need them.

**Current state:** Not addressed. `docs/source/` now has only `index.rst`, `install.rst`, `ryzom.rst`, `ryzom.components.rst`, `ryzom_mdc.rst`, `ryzom_django_mdc.rst`. Autodoc is **still configured** in `conf.py` (`sphinx.ext.autodoc`, `sys.path` → `../../src`, `django.setup()`), but the toctree generates **no API reference for `ryzom_django_channels`** at all, and the mdc pages are hand-written prose, not `automodule`.

**Why they were removed (commit `59703ae`):** the 10 deleted stubs were `.. automodule:: ryzom.<x>` directives pointing at modules that no longer exist *under `ryzom`* (the package was split), producing "failed to import" warnings. The fix removed the content instead of repointing it.

**Which stubs were stale vs still-valid:** 8 of 10 modules were **moved, not deleted** — they now live in `ryzom_django_channels` (`consumers`, `ddp`, `models`, `pubsub`, `routing`, `signals`, `views`, `apps`) or `ryzom_django` (`urls`). Only `ryzom.reactive` (old prose guide) is genuinely obsolete. So the reviewer's concern is valid: real API surface lost its reference.

**Proposed solution:** Add one new autodoc page pointing at the surviving package and wire it into the toctree (no new infra — autodoc already works):

Create `docs/source/ryzom_django_channels.rst` with `.. automodule::` blocks for
`ryzom_django_channels.{models,views,consumers,pubsub,ddp,routing,signals,facets,methods,polling}`
(each with `:members: :undoc-members: :show-inheritance:`), then add
`ryzom_django_channels` to the `index.rst` toctree after `ryzom_django_mdc`.
Optionally add a `ryzom_django.rst` for the moved `ryzom.urls`/`.forms`/`.template_backend`.

Mechanical alternative matching the commit's intent:
`sphinx-apidoc -f -o docs/source src/ryzom_django_channels src/ryzom_django`
then verify `sphinx-build` stays warning-clean (the new import paths resolve).

---

## 3. Simplify the value extraction — `py2js/transpiler.py`

**Comment (jpic):** "`getattr(node, 'n', node.value)` ça fait presque pareil ? outre le cas où node.n == 0 et que node.value != 0 mais ça serait étonnant".

**Current state / code** (`src/py2js/transpiler.py:690-691`):

```python
def visit_Num(self, node):
    return getattr(node, 'n', None) or node.value
```

(`visit_Str` at line 697 uses the same `getattr(node, 's', None) or node.value` shape.)

**Analysis of the edge case:** the two forms diverge only when the `n`/`s` attribute *exists but is falsy* (`0`, `0.0`, `''`):
- Current `... or node.value` discards a legit `0`/`''` and falls through to `node.value`.
- Proposed `getattr(node, 'n', node.value)` returns `0` correctly (the attribute exists) and uses `node.value` only as the absent-attribute default.

The reviewer's framing is slightly off (`getattr` handles `0` fine), but the proposed form is in fact **more correct** — it removes the falsy-`0` footgun. On Python 3.8+ `ast.Num.n` and `.value` are the same object so it's academic for real inputs; no functional regression.

**Proposed solution:**

```python
def visit_Num(self, node):
    return getattr(node, 'n', node.value)
```

(For consistency, `visit_Str`: `s = getattr(node, 's', node.value)`.)

---

## 4. Explicit `if/else` for `in_str` — `py2js/transpiler.py`

**Comment (jpic):** "Tant qu'à faire, je prefererrais avoir un if self.in_str et un else".

**Current state / code** (`src/py2js/transpiler.py:693-700`) — negated early return:

```python
def visit_Str(self, node):
    # ... docstring ...
    s = getattr(node, 's', None) or node.value
    if not self.in_str:
        return "%s" % repr(s).lstrip("urb")
    return s
```

**Proposed solution** — flip to positive `if self.in_str:` with an explicit `else` (and fold in fix #3):

```python
def visit_Str(self, node):
    # ... docstring ...
    s = getattr(node, 's', node.value)
    if self.in_str:
        return s
    else:
        return "%s" % repr(s).lstrip("urb")
```

Behavior unchanged: inside an f-string/`JoinedStr` the raw `s` is emitted; otherwise the `repr()`-quoted form.

---

## 5. Drop the vendored autocomplete assets — `ryzom_django_autocomplete/`

**Comment (jpic):** "on peut les avoir en installant django-autocomplete-light, ce qui m'a l'air preferrable au vendoring".

**Current state:** Not addressed. `src/ryzom_django_autocomplete/static/autocomplete_light/` holds `autocomplete-light.js` (14.5 KB), `autocomplete-light.css` (1.9 KB) and `SOURCE.md`. They're wired via `Static('autocomplete_light/autocomplete-light.{css,js}')` in `html.py:10-11` and consumed by `SelectWidget`. Commit `4140b34` dropped `'autocomplete-light'` from `setup.py` extras and `'autocomplete_light'` from INSTALLED_APPS.

**Important nuance:** the vendored files are the **standalone `autocomplete-light` web component** (a yourlabs project, pure vanilla JS — zero jQuery/select2), distributed on PyPI as `autocomplete-light`. That is **not** the heavy `django-autocomplete-light` (DAL) stack. The reviewer's wording ("django-autocomplete-light") almost certainly means re-adding the `autocomplete-light` package this commit removed — **do not substitute DAL**, which would pull in jQuery+select2.

**Why it was vendored (`4140b34`):** the package was being consumed as an *editable* install whose missing checkout could break `manage.py`; vendoring kept the same static URL while removing the fragile dependency.

**Proposed solution (revert):**
1. `setup.py`: restore `'autocomplete-light'` in `extras_require['project']` — **pin a published version** (e.g. `autocomplete-light>=1.1.6`) to avoid the editable-path failure that motivated the vendoring.
2. `ryzom_django_example/settings.py`: restore `'autocomplete_light'` in INSTALLED_APPS (before `'ryzom_django_autocomplete'`) so its static dir is found.
3. `git rm -r src/ryzom_django_autocomplete/static/autocomplete_light/`.
4. **No `html.py` change** — the package ships assets at the same `autocomplete_light/autocomplete-light.{css,js}` path, so the `Static(...)` refs resolve unchanged. *Verify the packaged static layout first.*

**Risk/caveats:** reintroduces a runtime dependency (mitigate with the version pin); confirm the PyPI version ≥ the `.dev7` commit recorded in `SOURCE.md` so the widget behaves identically.

---

## 6. Don't create Subscriptions on a GET — `ryzom_django_channels/` (consumers + views + polling)

**Comment (jpic):** JS-less clients (GoogleBot) shouldn't create Subscriptions; and a GET must be a safe/read-only method per RFC 7231/9110 (mutations belong on POST/PUT/PATCH/DELETE).

**Current state — where Subscriptions are created:** **Only on the HTTP GET render path, never over the websocket** — the opposite of the layout the reviewer remembers, and exactly what he's objecting to:
- `components.py:76-87` — `SubscribeComponentMixin.create_subscription()` does `Subscription.objects.create(...)`, called unconditionally from `reactive_setup()` (`components.py:72-73`) **during synchronous render** of the GET view.
- `views.py:35-42` — `ReactiveMixin.get_token()` also does `Client.objects.create(...)` on every render. So one GET writes a `Client` row **and** one `Subscription` per reactive list.
- `consumers.py:301-323` — `recv_subscribe()` is now a hard-coded `"Not implemented"` stub (docstring: "subscriptions are created server-side while the page renders").
- `polling.py:117-141` / `views.py:60-81` — the poll endpoint only **reads** existing subscriptions; it relies on the GET having created them.

**What the MR changed and why:** the reviewer's memory is correct. Pre-MR, `recv_subscribe()` created the Subscription over the websocket. Commit `f48fdf7` ("race-free pushes") gutted it to a no-op and made render-time `create_subscription()` the single source; `dd9b3bf` ("client-pull polling fallback") then added poll mode, whose read-only GET **depends on** the subscription already existing.

**The design conflict (this is the hard one):** poll mode has no websocket and no client-initiated "subscribe" event — the browser only fires read-only `ddp_poll` GETs. For a poll diff to return anything, the `Subscription` must already exist, which is why the MR creates it on the page GET. You cannot keep creation off the GET **and** have the current poll endpoint work, unless the poll/WS handshake creates the subscription itself.

**Proposed solution — defer creation to the first client-initiated request; keep the GET render-only:**
1. Make render **read-only**: split a `get_content()` that computes the first paint via the existing `get_queryset(user, qs, opts)` classmethod (`components.py:101`, needs no Subscription row). The GET emits `subscriber_id` / `publication` / `subscribe_options` as data-attributes only — **no DB write**.
2. Move the actual `Subscription.objects.create(...)` to client-initiated channels:
   - **WS push:** restore a real `recv_subscribe()` (`consumers.py:301`) doing `get_or_create` keyed on `(client, publication, subscriber_id)` from the replayed attributes — legitimately a client message on the WS path.
   - **Poll mode:** have the **first** `ddp_poll` (`views.py:60`) `get_or_create` the subscriptions from the posted descriptors. To keep GET safe, switch `ddp_poll` to **POST** (it already CSRF-exempts and authenticates by token) and send the descriptors in the first poll body; `poll_client` upserts before diffing.
3. Also gate the `Client.objects.create` in `get_token()` (`views.py:38`) behind the same client-initiated trigger.

Net: a JS-less GET renders the first page with **zero writes**; `Client`/`Subscription` rows appear only when JS actually connects (WS `recv_subscribe` or first POST `ddp_poll`). Use `get_or_create` everywhere for idempotent reconnect/re-poll. `sweep_stale_clients` TTL reclamation is unaffected.

---

## 7. Restore empty DB defaults — `ryzom_django_example/settings.py`

**Comment (jpic):** put `DB_HOST`/`DB_USER`/`DB_PASSWORD` back to empty defaults so the demo "just works" (local socket / peer auth after `createuser -s $USER`).

**Current state / code** (`src/ryzom_django_example/settings.py:132-141`):

```python
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'ryzom'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),    # line 137
        'USER': os.getenv('DB_USER', 'ryzom'),        # line 138
        'PASSWORD': os.getenv('DB_PASSWORD', 'ryzom'),# line 139
    }
}
```

With empty `HOST` psycopg uses the local unix socket; empty `USER` → OS username; empty `PASSWORD` → peer/trust auth — the classic zero-config local setup. **Keep the Postgres engine** (mandatory for `ArrayField`; the reviewer only objects to host/user/password).

**Proposed solution:**

```diff
-        'PORT': os.getenv('DB_PORT', '5432'),
-        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
-        'USER': os.getenv('DB_USER', 'ryzom'),
-        'PASSWORD': os.getenv('DB_PASSWORD', 'ryzom'),
+        'PORT': os.getenv('DB_PORT', ''),
+        'HOST': os.getenv('DB_HOST', ''),
+        'USER': os.getenv('DB_USER', ''),
+        'PASSWORD': os.getenv('DB_PASSWORD', ''),
```

`os.getenv('DB_*', '')` still honors every override, so CI/Docker are unaffected — only the fallback changes.

**Knock-on updates (each verified):**
- **CI `.gitlab-ci.yml` — no change.** It explicitly sets `DB_HOST=postgres`, `DB_USER/NAME/PASSWORD=test` (lines 21-25); those overrides win.
- **`run-demo` skill — needs an edit.** It assumes `ryzom`/`ryzom` on `127.0.0.1:5432` and starts a Docker `ryzom-pg` container. With empty defaults the Docker path no longer matches. Fix: `export DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom` before `manage.py` in the container path (consistent with CI).
- **`CLAUDE.md` line 26 — reword.** Change "Defaults: db/user/pass all `ryzom` on `127.0.0.1:5432`" to describe the default as local-socket/`$USER` (DB name `ryzom`), with `ryzom`/`127.0.0.1` now the Docker/CI override convention.
- No `docker-compose.yml` exists — nothing to change there.

---

## 8. Restore the full Material list UI (2026-06-16 feature request)

jpic posted a target screenshot vs the plainer view he currently sees and asked,
**in addition to** the inline comments, for five things. The WIP refactor swapped
the classic page-reload `Router` (which *had* per-object Edit/Delete with icons +
a delete modal, now in `ryzom_django_mdc/crud.py`) for the live `ReactiveRouter`
(`ryzom_django_mdc/reactive.py`). Sorting, the per-page select and the filter
form are **already Material and live** (8.1–8.3 done). The real work is the
per-object **edit/delete** affordances (8.4–8.5), which the reactive router
dropped: no `update/`/`delete/` routes, no edit ModelForm, no per-row icon
buttons, and no shareable URL (so middle-click-new-tab is impossible).

### 8.1 Click-to-sort columns — **already done**
Commit `146061c` survived. `sortable_th()` (`reactive.py:270-282`) emits clickable
`MDCDataTableTh`; `ReactiveSort` (`reactive.py:314-401`) toggles asc/desc, draws
▲/▼ and POSTs to `sort/` (`SortView`, `reactive.py:1569-1589`, route at `:1678`).
Demo columns set sortability (`components.py:183-190`). Nothing to do — if the
arrow was absent in the screenshot it's because no column was active yet.

### 8.2 Rows-per-page as MDC select — **already done**
`ReactivePager` already uses `MDCSelectOutlined` (`reactive.py:648-655`), bound to
`MDCSelect:change` → POST `page/` (`reactive.py:693-701`). (Don't switch to
`MDCSelectPerPage` at `html.py:1197` — it does a full URL reload, wrong for a live
table.) Nothing to do.

### 8.3 Material filter form — **already done**
`ReactiveFilter` (`reactive.py:488-526`) renders `MDCTextFieldOutlined` per
`SearchFacet` and `MDCCheckboxField` per `BooleanFacet`, labelled from
`router.filter_labels`; wired at `reactive.py:1483-1484`. Matches jpic's "il y a
tout dans ryzom". Optional cosmetic: wrap the inputs in an `MDCCard`/`FormContainer`
to read as a card.

### 8.4 Delete action (red trash, modal, middle-click new tab) — **partial**
Exists: a delete `Action` with a confirm dialog (`components.py:196-198`,
`crud.py:77-79`), surfaced only through the kebab menu (`row_actions_toggle()` →
`MDCIconButton('more_vert')`, `reactive.py:188-202`; `ReactiveRowActions` +
`ActionDialog`, `reactive.py:147-181, 989-1035`; POST to `bulk/`).
Missing: **(1)** not a red trash icon — it's a text item in a shared kebab;
**(2)** **no per-object URL** — `get_urls()` (`reactive.py:1674-1684`) only exposes
`list/create/filter/sort/page/bulk/poll/<int:pk>/`, so there's nothing to put in
an `<a href>` → middle-click-new-tab is impossible.

**Solution** — give each row a real `<a>` icon button pointing at a standalone
delete URL that also opens in a dialog on left-click:
1. Add routes to `get_urls()` (`reactive.py:1674`), reusing the classic
   `DeleteView`/`UpdateView` (`crud.py:1341-1389`):
   ```python
   path('<int:pk>/delete/', DeleteView.as_view(), name='delete'),
   path('<int:pk>/update/', UpdateView.as_view(), name='update'),
   ```
2. In `ReactiveRow.__init__` (`reactive.py:239-243`) render an icon link with the
   existing `MDCIconButton` (`html.py:1220`):
   ```python
   MDCIconButton('delete', tag='a',
                 href=self.router.reverse_url('delete', obj.pk),
                 addcls='row-delete', style='color:#c00', aria_label='Delete')
   ```
   Being a true `<a href>`, **middle-click opens a new tab for free**.
3. Intercept left-click to fetch that URL into an `MDCDialog` (`html.py:1807`),
   mirroring the classic `ModalLayer` (`crud.py:38-106`). The standalone URL then
   serves double duty: new-tab on middle-click, modal on left-click.

### 8.5 Edit action (orange pen, ModelForm modal, middle-click new tab) — **missing**
No edit affordance anywhere in the reactive stack: no `update` `Action`
(`components.py:195-204`, `crud.py:75-80`), no `<int:pk>/update/` route
(`reactive.py:1674-1684`), no update view, no edit ModelForm (only the inline
*create* form `ReactiveCreateForm`, `reactive.py:1203-1249`). The `rename` action
edits a single field, not a full form. The classic `Router` *does* have a working
`UpdateView` + `modelform_factory` (`crud.py:1341-1357`) to copy.

**Solution** — parallel to 8.4:
1. Add `<int:pk>/update/` backed by an `UpdateView` reusing
   `router.get_form_class()` (`reactive.py:1444-1446`; widen via an
   `update_fields` setting). `post_save` already pushes the row change live, so
   the modal just closes on save.
2. In `ReactiveRow.__init__` add an orange pen icon link:
   ```python
   MDCIconButton('edit', tag='a',
                 href=self.router.reverse_url('update', obj.pk),
                 addcls='row-edit', style='color:#fb8c00', aria_label='Edit')
   ```
3. Left-click opens the update ModelForm in an `MDCDialog` (`html.py:1807`),
   reusing the `ModalLayer`/`ActionDialog` approach; the form uses MDC widgets via
   `MDCInputWidget`/`SelectWidget` (`ryzom_django_mdc/html.py:27,271`).

**Shared note (8.4 + 8.5):** factor a `row_links(obj)` helper next to
`row_actions_toggle` (`reactive.py:188`) emitting both icon anchors, plus one
page-level custom element (like `ReactiveRowActions`, `reactive.py:989`) that
intercepts left-clicks on `.row-edit`/`.row-delete` and pops the URL into an
`MDCDialog`, leaving middle/ctrl-click to the browser's native new-tab. All
widgets already exist: `MDCIconButton` (`html.py:1220`), `MDCDialog` family
(`html.py:1760-1807`), `modelform_factory` plumbing (`reactive.py:1444`), and the
classic `UpdateView`/`DeleteView` to copy (`crud.py:1341-1389`).

---

## Suggested order of work

1. **Trivial / mechanical** (clears most of the "requested changes"):
   #3, #4 (transpiler), #7 (DB defaults), #2 (docs), #5 (un-vendor).
2. **Small but discuss first:** #1 (Celery sweep — propose Celery-beat instead of
   per-poll `.delay()`).
3. **Medium feature work:** #8.4 + #8.5 (edit/delete icon links + modals + routes).
4. **Large / needs design agreement with jpic:** #6 (move Subscription creation
   off GET — reconcile with poll mode by switching `ddp_poll` to POST + lazy
   `get_or_create`).

8.1–8.3 are already satisfied — just confirm at runtime and reply to jpic with
the file:line evidence above.
