---
name: seed-demo
description: Seed or reset the demo's data and login identities (groups, users, grouped products). Use when asked to seed, reset, or repopulate demo data, or when you need known logins (alice/bob/carol/boss) to test per-user visibility.
---

# Seed / reset demo data

```
python manage.py seed_demo
```

Idempotent — it `update_or_create`s by name/username, so re-running **resets** the
demo to a known state (and resets every password back to `demo`) without
duplicating rows. Needs Postgres reachable; run migrations first if the schema is
fresh (`python manage.py migrate`).

## What it creates

- **Groups:** `sales`, `ops`.
- **Users** (password `demo` for all):
  - `alice` — sales
  - `bob` — ops
  - `carol` — sales + ops
  - `boss` — staff (sees everything)
- **11 products** spread across `public` (no group), `sales`, and `ops`.

## Why it's shaped this way

The split makes **per-user visibility** observable: each identity sees a
different slice of `/crud/products/` (public rows + their groups' rows; staff see
all). This is the live demonstration of `GroupFacet` — see
`docs/design/LOGIN.md` and `docs/design/MATCHING.md`.

## To exercise it

Log in at `/login/` as one of the users above, open `/crud/products/`, and note
the identity banner + which rows appear. Source of truth for the data is
`src/ryzom_example_crud/management/commands/seed_demo.py`.
