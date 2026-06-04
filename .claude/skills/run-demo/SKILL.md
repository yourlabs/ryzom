---
name: run-demo
description: Launch the live Ryzom Product demo (the reactive /crud/products/ page). Use when asked to run, start, boot, serve, or "see" the demo/app/live list, in either websocket-push mode (full stack) or the simpler polling mode. Pair with the stop-demo skill to tear it down.
---

# Run the demo

The demo is the reactive Product list at `http://127.0.0.1:8000/crud/products/`.
Two transports — pick one. Always run from the repo root, always
`python manage.py …` (settings module is wired by `manage.py`).

## Prerequisite for BOTH modes: Postgres + schema + data

Postgres is required (ArrayField). Defaults: db/user/password all `ryzom`.

1. Check Postgres is reachable: `python manage.py migrate --plan` (errors if not).
   If the DB is missing, the user must create it (suggest they run, with `!`):
   `! sudo -u postgres createdb -O ryzom ryzom` (and a `ryzom` role if needed).
2. Apply migrations: `python manage.py migrate`
3. Seed identities + products (idempotent): `python manage.py seed_demo`
   → users alice/bob/carol/boss, password `demo`. (See the **seed-demo** skill.)

## Mode A — polling (simplest; no Redis, no Celery worker)

Best default when you just need to see it working.

```
RYZOM_TRANSPORT=poll python manage.py runserver
```

Run it with `run_in_background: true` so it keeps serving across turns; tee logs
to a file (e.g. `/tmp/ryzom-runserver.log`) and grep that to confirm it booted.
The client pulls deltas every `POLL_INTERVAL` ms — no server push, so no worker.

## Mode B — websocket push (full stack; the real reactive path)

Needs Redis running and a Celery worker, or pushes silently never arrive.

1. Redis: settings auto-detect it on `127.0.0.1:6379`. Confirm with
   `redis-cli ping` (expect `PONG`). If absent, ask the user to start their Redis
   service (don't assume how it's managed).
2. Celery worker (background): `celery -A ryzom_django_channels worker -l info`
   → run with `run_in_background: true`, logs to `/tmp/ryzom-celery.log`.
3. Server (background): `python manage.py runserver`
   (Redis being up flips `CHANNELS_ENABLE` on, so this serves over ASGI/daphne.)
   To force push even if detection is odd: `RYZOM_TRANSPORT=ws python manage.py runserver`.

## Verify

- `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/crud/products/`
  → `200`.
- To see reactivity: open the page in two tabs, add/sell a product in one, watch
  the other update with no reload. Log in at `/login/` as a seeded user to see
  per-user (group) visibility.

## Notes

- Track the PIDs/log files you started so **stop-demo** can clean up.
- Do **not** start or kill the user's Postgres/Redis services yourself — only the
  runserver and Celery worker that this skill launches.
- **Restart the Celery worker after editing component code (Mode B).** In ws-push
  mode the row/detail updates pushed over the websocket are rendered *inside the
  Celery worker* (`ddp_process_task`), which — unlike `runserver`'s StatReloader
  — does **not** auto-reload. So after changing anything rendered reactively
  (`@model_template` rows like `ProductRow`, `ReactiveComponent` detail views, or
  helpers they call), the freshly loaded page shows the new code but live-pushed
  rows still come from the stale worker — they revert to the old markup "after
  use". Kill and relaunch the worker to pick up the change:
  `pkill -9 -f 'celeryd: celery@'` then start it again as in Mode B. (The web
  layer — views, list render, POST handlers — hot-reloads, so only the worker
  needs the manual restart.)
