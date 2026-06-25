---
name: run-demo
description: Launch the live Ryzom Product demo (the reactive /crud/products/ page). Use when asked to run, start, boot, serve, or "see" the demo/app/live list, in either websocket-push mode (full stack) or the simpler polling mode. Pair with the stop-demo skill to tear it down.
---

# Run the demo

The demo is the reactive Product list at `http://127.0.0.1:8000/crud/products/`.
Two transports — pick one. Always run from the repo root.

**Path:** the settings module `ryzom_django_example` lives under `src/`. If the
packages aren't installed editable, `manage.py` can't import it
(`ModuleNotFoundError: No module named 'ryzom_django_example'`). Prefix every
`manage.py` / `celery` command with `PYTHONPATH=src` (the examples below do). A
quick probe: `PYTHONPATH=src python -c "import ryzom_django_example"`.

## Prerequisite for BOTH modes: Postgres (Redis too for Mode B)

Postgres is required (ArrayField); Mode B also needs Redis. Settings now default
to the local **unix socket** (user `$USER`, no password), so this skill — which
provisions Postgres in **Docker** as `ryzom`/`ryzom` on `127.0.0.1:5432` (Redis on
`127.0.0.1:6379`) — must point Django at it explicitly. Prepend this DB env to
**every** `manage.py`/`celery` command below (shown inline alongside `PYTHONPATH`):

```
DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom
```

### 1. Probe what's already up

CLI clients (`psql`, `pg_isready`, `redis-cli`) are often **not installed** — probe
the TCP ports instead:

```
python - <<'PY'
import socket
def up(h,p):
    s=socket.socket(); s.settimeout(1)
    try: return s.connect_ex((h,p))==0
    finally: s.close()
print('postgres', up('127.0.0.1',5432))
print('redis',    up('127.0.0.1',6379))
PY
```

### 2. If a service is down, launch it as a Docker container

Don't touch the user's host-managed services. But if a port is closed, **start (or
create) a Docker container** that matches the settings defaults. Reuse the
canonical names `ryzom-pg` / `ryzom-redis` so a stopped container (and its data) is
restarted rather than duplicated — `docker start` first, fall back to `docker run`:

```
# Postgres (required)
docker start ryzom-pg 2>/dev/null || docker run -d --name ryzom-pg \
  -e POSTGRES_USER=ryzom -e POSTGRES_PASSWORD=ryzom -e POSTGRES_DB=ryzom \
  -p 5432:5432 postgres:16

# Redis (Mode B only)
docker start ryzom-redis 2>/dev/null || docker run -d --name ryzom-redis \
  -p 6379:6379 redis:7
```

First check Docker is usable (`docker version`); if it isn't, ask the user to start
their DB/Redis themselves (suggest a `! …` command — don't assume how they manage
it). Confirm Postgres accepts connections before migrating (the image *does* ship
`pg_isready`): `docker exec ryzom-pg pg_isready -U ryzom` → "accepting
connections" (retry a couple of times; the container takes a second or two).

### 3. Schema + data

1. Apply migrations: `DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom PYTHONPATH=src python manage.py migrate`
   (`migrate --plan` errors out if Postgres still isn't reachable.)
2. Seed identities + products (idempotent):
   `DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom PYTHONPATH=src python manage.py seed_demo`
   → users alice/bob/carol/boss, password `demo`. (See the **seed-demo** skill.)

## Mode A — polling (simplest; no Redis, no Celery worker)

Best default when you just need to see it working.

```
DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom RYZOM_TRANSPORT=poll PYTHONPATH=src python manage.py runserver
```

Run it with `run_in_background: true` so it keeps serving across turns; redirect
logs to a file (e.g. `/tmp/ryzom-runserver.log`) and grep that to confirm it
booted. The client pulls deltas every `POLL_INTERVAL` ms — no server push, so no
worker. (Mode A still needs the `ryzom_django_channels` models, which only load
when `CHANNELS_ENABLE` is on — Redis being up flips that automatically; without
Redis, force it with `CHANNELS_ENABLE=1`.)

## Mode B — websocket push (full stack; the real reactive path)

Needs Redis running (see step 2) and a Celery worker, or pushes silently never
arrive.

1. Celery worker (background): `DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom PYTHONPATH=src celery -A ryzom_django_channels worker -l info`
   → run with `run_in_background: true`, logs to `/tmp/ryzom-celery.log`. Confirm it
   logged `celery@<host> ready.` with no traceback.
2. Server (background): `DB_HOST=127.0.0.1 DB_USER=ryzom DB_PASSWORD=ryzom PYTHONPATH=src python manage.py runserver`
   (Redis being up flips `CHANNELS_ENABLE` on, so this serves over ASGI/daphne.)
   To force push even if detection is odd: prepend `RYZOM_TRANSPORT=ws`.

## Verify

- Wait for boot without a foreground `sleep` (it's blocked in this harness) — let
  `curl` retry instead:
  `curl -sS --retry 10 --retry-connrefused --retry-delay 1 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/crud/products/`
  → `200`.
- Transport sanity: the page meta carries `transport="ws"` (Mode B) or
  `transport="poll"` (Mode A) — `curl … | grep -o 'transport="[a-z]*"'`.
- To see reactivity: open the page in two tabs, add/sell a product in one, watch
  the other update with no reload. Log in at `/login/` as a seeded user to see
  per-user (group) visibility.

## Notes

- Track the PIDs/log files you started so **stop-demo** can clean up. Any
  `ryzom-pg` / `ryzom-redis` containers this skill **started** can be paused with
  `docker stop …`; do **not** `docker rm` them or delete their volumes — that
  destroys the user's demo data.
- Do **not** start or kill the user's host-managed Postgres/Redis services — the
  container path above is the only infra this skill brings up itself.
- **Restart the Celery worker after editing component code (Mode B).** In ws-push
  mode the row/detail updates pushed over the websocket are rendered *inside the
  Celery worker* (`ddp_process_task`), which — unlike `runserver`'s StatReloader
  — does **not** auto-reload. So after changing anything rendered reactively
  (`@model_template` rows like `ProductRow`, `ReactiveComponent` detail views, or
  helpers they call), the freshly loaded page shows the new code but live-pushed
  rows still come from the stale worker — they revert to the old markup "after
  use", and if several stale workers are alive they alternate old/new markup at
  random. Kill **all** workers and relaunch one to pick up the change:
  `pkill -9 -f 'ryzom_django_channels [w]orker'` then start it again as in Mode B.
  Match the renamed process title (`celeryd: celery@… (-A ryzom_django_channels
  worker)`), not `celery -A …` (which matches nothing and leaks the worker); the
  `[w]` bracket keeps `pkill` from matching its own command line. Verify exactly
  one remains: `ps -eo pid,cmd | grep '[r]yzom_django_channels'`. (The web layer
  — views, list render, POST handlers — hot-reloads, so only the worker needs the
  manual restart.)
