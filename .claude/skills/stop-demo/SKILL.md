---
name: stop-demo
description: Stop the running Ryzom demo — tear down the runserver and Celery worker started by the run-demo skill. Use when asked to stop, kill, shut down, or clean up the demo/app/server/worker.
---

# Stop the demo

Tear down what the **run-demo** skill starts: the Django `runserver` and the
Celery worker (always), and — if asked — the Postgres/Redis **containers** it may
have launched. Never touch the user's host-managed Postgres/Redis services.

## If you started them as background Bash tasks this session

Prefer stopping those tracked tasks directly (they are the processes you own).
List background tasks and stop the runserver/celery ones.

## Otherwise, match by command line

```
pkill -f "manage.py runserver"
pkill -9 -f 'ryzom_django_channels [w]orker'
```

**Important — match the real celery process title.** Once started, the worker
renames itself via setproctitle to `celeryd: celery@<host> … (-A
ryzom_django_channels worker -l info)`, so a pattern like
`celery -A ryzom_django_channels` matches **nothing** and silently leaks the
worker (this is how multiple stale workers pile up — and why pushed rows then
render with a random mix of old/new markup). The pattern above matches the args
that survive the rename; the `[w]` bracket trick keeps the `pkill` command from
matching its own command line.

Then confirm **none** remain (there may have been several):

```
pgrep -af "manage.py runserver" || echo "runserver stopped"
ps -eo pid,cmd | grep -i 'ryzom_django_channels' | grep -iv 'grep\|/bin/bash -c' \
  || echo "all workers stopped"
```

If port 8000 is still held, find the holder before force-killing:
`ss -ltnp 'sport = :8000'` (or `lsof -i :8000`), then `kill <pid>`.

## Containers (only if run-demo launched them)

If the DB/Redis are running as the `ryzom-pg` / `ryzom-redis` Docker containers
(run-demo brings these up when the local ports are closed), leave them up by
default — they hold the demo's data and the user may be using them elsewhere. Stop
them **only when the user asks** to fully tear down:

```
docker stop ryzom-pg ryzom-redis
```

`docker stop` is non-destructive — the data persists in the stopped container and
`docker start` (or run-demo) brings it back. **Never** `docker rm` these
containers or delete their volumes — that destroys the user's demo data.

## Do not

- Do **not** `pkill redis`, `redis-cli shutdown`, or stop a host Postgres — those
  are shared services the demo only connects to, it does not own them. (The
  `ryzom-pg`/`ryzom-redis` *containers* are the exception, per above.)
- Do **not** `docker rm` the containers or remove their volumes.
- Optional cleanup: remove the log files you created (`/tmp/ryzom-*.log`).
