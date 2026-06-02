---
name: stop-demo
description: Stop the running Ryzom demo — tear down the runserver and Celery worker started by the run-demo skill. Use when asked to stop, kill, shut down, or clean up the demo/app/server/worker.
---

# Stop the demo

Tear down only what the **run-demo** skill starts: the Django `runserver` and the
Celery worker. Leave the user's Postgres and Redis services alone.

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

## Do not

- Do **not** `pkill redis`, `redis-cli shutdown`, or stop Postgres — those are
  shared services the demo only connects to, it does not own them.
- Optional cleanup: remove the log files you created (`/tmp/ryzom-*.log`).
