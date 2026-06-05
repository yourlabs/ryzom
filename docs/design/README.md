# Design documents

Architecture and design notes for Ryzom. These are prose design docs (problem
statements, design decisions, implementation plans), distinct from the Sphinx
API reference under [`../source/`](../source/).

Code comments throughout `src/` refer to these by bare filename (e.g.
"see `POLLING.md`", "PROBLEM.md §3"); they now live here.

## Project-wide

- [SYNTHESIS.md](SYNTHESIS.md) — what Ryzom is, the package map, and overall status.
- [CRUDLFAP_COMPONENTS.md](CRUDLFAP_COMPONENTS.md) — component build list for the
  CRUDLFAP-on-Ryzom rewrite.
- [MATERIAL_COMPLIANCE.md](MATERIAL_COMPLIANCE.md) — how far the `ryzom_example_crud`
  Product demo is from Material Design norms, and the steps to close the gap.

## Reactive live-list (the `ryzom_example_crud` demo + `ryzom_django_channels`)

Read in this order — each builds on the previous:

1. [PROBLEM.md](PROBLEM.md) — the central scaling problem: routing writes to the
   subscriptions they affect (problem statement, not a solution).
2. [PAGINATION.md](PAGINATION.md) — numbered/offset pagination as a window over
   each standing query, and the window-ripple it forces.
3. [MATCHING.md](MATCHING.md) — reverse matching (PROBLEM.md step 3): visit only
   candidate subscriptions instead of all of them.
4. [POLLING.md](POLLING.md) — client-pull (polling) transport for deployments
   that forbid server-initiated push.
5. [LOGIN.md](LOGIN.md) — per-user row visibility: login, group attribution, and
   the public/group/staff visibility matrix.
