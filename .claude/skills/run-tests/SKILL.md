---
name: run-tests
description: Run the Ryzom test suite and linter the way CI does. Use when asked to run tests, check tests pass, run pytest, lint, run ruff, or verify a change before committing/pushing.
---

# Run tests & lint

From the repo root. `DJANGO_SETTINGS_MODULE` is already set by `pytest.ini`, so
no env juggling is needed for the default run.

## Tests (pytest)

```
python -m pytest -q
```

- Tests live in `tests/` (e.g. `test_facets.py`, `test_polling.py`,
  `test_demo.py`). The full suite should be green (~97 tests at last count).
- Run one file/test while iterating: `python -m pytest tests/test_demo.py -q`
  or `python -m pytest tests/test_demo.py::TEST_NAME -q`.
- Tests need **Postgres** reachable (same DB config as the app; ArrayField).
  Redis/Celery are **not** required — task code is exercised synchronously in
  tests, not through a live worker.

## Lint (ruff — this is the QA gate)

```
ruff check src
```

Config is `ruff.toml`. CI fails on any finding. One pre-existing `E741` in
`tests/test_py2js.py` is outside the `src` QA scope — don't chase it.

## Matching CI exactly

CI (`.gitlab-ci.yml`) runs with `CHANNELS_ENABLE=1` and Postgres env
(`DB_HOST`, `DB_USER=test`, `DB_NAME=test`, `DB_PASSWORD=test`). To reproduce a
channels-on run locally:

```
CHANNELS_ENABLE=1 python -m pytest -q
```

## Live end-to-end (manual, not part of pytest)

Behavioral reactive checks (real push through Celery+Redis+Postgres) are done by
running the demo and clicking — use the **run-demo** skill, not this one.

Always run pytest **and** `ruff check src` before reporting a change as done, and
before any commit/push.
