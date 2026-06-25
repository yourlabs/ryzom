# Ryzom — agent orientation

Ryzom replaces Django HTML templates with **Python component classes**, plus an
optional real-time reactivity layer over Django Channels + Celery.

This file is the always-loaded map. Deeper knowledge lives in **`docs/design/`**
(read [`docs/design/README.md`](docs/design/README.md) first) and in **task
skills** under `.claude/skills/` (run-demo, stop-demo, run-tests, seed-demo,
create-component).

## Package map (`src/`, mono-repo, each dir is an installable package)

| Package | Purpose |
|---|---|
| `ryzom` | Core component engine — renders Python objects to HTML |
| `py2js` | Python → JavaScript transpiler (AST-based) |
| `ryzom_mdc` / `ryzom_django_mdc` | Material Components widgets (`html.py`); generic CRUD routers: classic `Router` (`crud.py`) + reactive `ReactiveRouter` (`reactive.py`) |
| `ryzom_django` | Django integration: template backend, forms, bundles |
| `ryzom_django_channels` | Reactivity: subscriptions, facets, DDP push + polling |
| `ryzom_example_crud` | Live demos via `ReactiveRouter`: Products (`/crud/products/`) + Users (`/crud/users/`) |

## How it runs (one source of truth: `src/ryzom_django_example/settings.py`)

- `manage.py` → `DJANGO_SETTINGS_MODULE=ryzom_django_example.settings`.
- **Postgres is required** (Subscription uses `django.contrib.postgres` ArrayField).
  Default: connects to local Postgres over the **unix socket** as `$USER` with no
  password (DB name `ryzom`) — so `createuser -s $USER` + `createdb -O $USER ryzom`
  "just works". Set `DB_HOST`/`DB_USER`/`DB_PASSWORD` to use TCP/Docker (the
  run-demo skill uses `ryzom`/`ryzom` on `127.0.0.1:5432`).
- Settings **auto-detect Redis** (`redis:6379` then `127.0.0.1:6379`); finding it
  sets `CHANNELS_ENABLE=True` and `runserver` serves over ASGI/daphne.
- Two transports: **ws push** (needs Redis + a Celery worker, signals use
  `.delay()`, no eager mode) and **poll** (client-pull, no worker/ws). Force with
  `RYZOM_TRANSPORT=ws|poll`. See `docs/design/POLLING.md`. → use the **run-demo** skill.
- Celery app is `ryzom_django_channels` (`celery -A ryzom_django_channels worker`).

## Conventions

- Components subclass `Component` (or an MDC widget) and build trees from
  `from ryzom_django_mdc.html import *`. Reactive rows use `@model_template(...)`
  + `SubscribeComponentMixin`; live detail views use `ReactiveComponentMixin`.
  Filtering/visibility is expressed as **facets** (`ryzom_django_channels/facets.py`).
  For a standard live CRUD, subclass **`ReactiveRouter`** (`ryzom_django_mdc/reactive.py`)
  with a model + columns/facets/actions instead of hand-rolling — see `ProductCrud`/
  `UserCrud`. → use the **create-component** skill. Canonical example:
  `src/ryzom_example_crud/components.py` (Product) + `src/ryzom_django_mdc/reactive.py`.
- Lint is **ruff** (`ruff check src`, config in `ruff.toml`). Tests are pytest.
  → use the **run-tests** skill.
- Commit messages use a topic prefix (`reactive:`, `ryzom_mdc:`, `docs:`, `ci:`)
  and end with the `Co-Authored-By` trailer. Commit/push only when asked.
- Design docs are referenced from code comments by **bare filename** (e.g.
  "see POLLING.md"); the files live in `docs/design/`.
