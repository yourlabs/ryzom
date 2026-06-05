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
pkill -f "celery -A ryzom_django_channels"
```

Then confirm they're gone:

```
pgrep -af "manage.py runserver|celery -A ryzom_django_channels" || echo "demo stopped"
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
