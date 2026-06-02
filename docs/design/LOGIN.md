# Login, group attribution, and per-user availability

This document is the design for **who sees which rows** in the reactive product
list once users log in. It is the human-facing other half of
[`MATCHING.md`](./MATCHING.md): `MATCHING.md` describes the *mechanism*
(`GroupFacet`, the `filter AND can_see(user, obj)` predicate routed forward and
reverse); this describes the *plumbing around it* — how a logged-in user's
identity reaches the subscription, how rows and users get their groups, and the
resulting visibility matrix.

It is a **design doc**, not a finished feature: §2 already exists in the demo,
§5 (the seeding/affordances that make it demonstrable live) is the work left.

---

## 1. The rule, in one line

> **staff** see every product; a **logged-in user** sees products whose `group`
> is one of their groups, plus **public** products (`group IS NULL`); an
> **anonymous** visitor sees only public products.

`group` is the `Product.group` FK to `auth.Group` (added in migration
`0002_product_group`). The rule is enforced by `GroupFacet('group')` in
`ProductRows.facets` — see [`MATCHING.md`](./MATCHING.md) for the forward/reverse
queries.

---

## 2. What already exists (the auth surface)

The demo is **not** anonymous-only by accident; the login surface is already
wired, it just isn't connected to product visibility yet.

- **Session auth** via `UserRouter.get_auth_urls()` (`crud.py` →
  `ryzom_django_mdc/crudlfap.py`): `path('login/')`, `path('logout/')`,
  `path('home/')` mounted at the root so `reverse('login')` works globally.
  Login uses Django's `AuthenticationForm` + `django.contrib.auth.login`; logout
  uses `logout`. Standard session cookie, nothing custom.
- **The App shell already shows the affordance**: `NavDrawer` renders the
  username and a **Login**/**Logout** link depending on
  `request.user.is_authenticated` (`crudlfap.py` ~line 1016).

So a user can already log in. What's missing is that **product visibility
ignores the result** — until `GroupFacet` (now in place) is fed a real user.

---

## 3. How the logged-in user reaches the reactive layer

This is the key seam, and it is already in place — the framework threads the
user end to end:

```
HTTP GET /crud/products/        request.user  (session-authenticated, or AnonymousUser)
  │
  ▼
ReactiveMixin.get_token()       Client.objects.create(user=request.user)
  │                             (AnonymousUser -> ValueError -> Client(user=None))
  ▼
Client row                      client.user  ← persisted server-side
  │
  ▼
ProductRows.create_subscription()
  Subscription(client=client, …)
  │
  ▼
Subscription.row_queryset()     publish_function(client.user)            (forward)
  → ProductRows.get_queryset(client.user, qs, opts)
      → GroupFacet.forward(qs, _, client.user)   ← scopes the visible set
```

Two consequences worth stating explicitly, because they shape the UX:

1. **Identity is captured once, at page render, and stored on the `Client`
   row.** The websocket only ever carries the opaque `token`; it never needs to
   re-authenticate. When a base-row change fires, the signal/reverse-match reads
   `sub.client.user` straight from the DB (`MATCHING.md` §Flow,
   `Q(client__user__…)`). So **the socket and the session are decoupled** — no
   cross-origin cookie problem between the Django view and the daphne worker.

2. **Visibility is bound at subscription-creation time.** A `Subscription` is
   created when the page loads; its `client.user` is fixed then. Therefore
   **logging in or out requires a page reload** to re-scope the list — the old
   subscription keeps the old identity until its page goes away. This is natural
   (login already navigates), but it must be documented: we do *not* try to
   mutate a live subscription's user in place.

---

## 4. Group attribution

Two independent assignments feed the rule. Both are ordinary Django data; the
only design choice is *where the demo exposes them*.

### 4a. Users → groups

`user.groups` is Django's built-in M2M (`auth_user_groups`). Assign via:

- **Django admin** (`/admin/auth/user/…`) — zero code, fine for the demo.
- **`UserRouter`** (`crud.py`): add `'groups'` to `form_fields` /
  `detail_fields` so the existing User CRUD at `/crud/users/` edits membership.
  (The Router is `open_access = True` — a demo bypass, see §6.)

A user in *no* group sees only public rows; `is_staff` overrides everything.

### 4b. Products → group

`Product.group` is a nullable FK. `NULL` = **public**. Assign via:

- **`ProductCreateForm`** (`components.py`): add a `<select name="group">`
  populated from `Group.objects.all()` (blank option = public), and have
  `ProductCreateView` set `group_id=request.POST.get('group') or None`. This is
  the one small code change needed to make grouping demonstrable from the live
  page.
- **Admin** for back-filling existing rows.

> **Why a single FK, not an M2M `groups`.** A product belongs to one group (or is
> public). That keeps the visibility key a *concrete column* (`group_id`), so it
> lands in the reverse-matching `_snapshot` and a regroup routes to both the old
> and the new group's subscribers for free. An M2M-per-product is more flexible
> but isn't a concrete field — invisible to `_snapshot`, and it fires
> `m2m_changed` rather than `post_save`. Deferred (see `MATCHING.md`).

---

## 5. Availability / visibility matrix

| Viewer            | `group=NULL` (public) | `group=sales` | `group=ops` |
|-------------------|:---------------------:|:-------------:|:-----------:|
| anonymous         | ✅ | ❌ | ❌ |
| user ∈ {sales}    | ✅ | ✅ | ❌ |
| user ∈ {sales,ops}| ✅ | ✅ | ✅ |
| staff             | ✅ | ✅ | ✅ |

The matrix holds **both** for the initial server render *and* for every live
push, because the same `GroupFacet` is applied in both directions:

- **Initial render & every re-window** go through `Subscription.get_queryset()`
  → `GroupFacet.forward(...)`. This is the **security boundary**: a client's
  stored window is recomputed by the forward query, so it can only ever contain
  rows that user may see.
- **Reverse routing** (`_candidate_ids`) decides *which subscriptions to wake*
  for a given change. It is an **optimization, not the boundary** — even if it
  over-matched, the woken subscription's forward re-window would still exclude an
  invisible row, so nothing leaks. (It does not over-match; the predicates are
  the same rule.) This defense-in-depth is worth keeping in mind when tuning the
  reverse query: correctness lives in `forward`.

A consequence for the live ripple: a "sell" on a `sales` product is routed to
staff + sales subscriptions only; an `ops`-only viewer's window never recomputes,
so they receive nothing — exactly right, and cheaper than waking them to
discover "no change."

---

## 6. Seeding to make it demonstrable

For a live two-tab demo you want fixtures (or a `manage.py` snippet):

- groups `sales`, `ops`;
- users: `alice` ∈ {sales}, `bob` ∈ {ops}, `boss` is_staff, each with a
  password; (a couple in both, to show union);
- products: a handful public, some `sales`, some `ops`.

Then: log in as `alice` in one tab and `bob` in another, sell a `sales`
product, and watch only `alice`'s (and any staff) tab update.

---

## 7. Security notes & limits

- **`UserRouter.open_access = True` is a demo bypass** for the *User CRUD*
  pages; it has nothing to do with product visibility. Product visibility is
  enforced in the publish/subscription layer (`GroupFacet.forward`), server-side,
  regardless of the Router bypass. The two are independent permission planes.
- **Staff bypass** is total by design (`is_staff` → see all). If "staff" should
  be narrower (e.g. a `can_view_all_products` permission), swap the
  `is_staff=True` test in `GroupFacet` for a permission check expressible over
  `client__user` (e.g. a group, or `user_permissions`/`groups__permissions`),
  keeping the reverse a single SQL predicate.
- **Anonymous = public-only** falls out of `client.user IS NULL`; no special
  case needed in the reverse query (a NULL user is neither staff nor a group
  member).
- **Deferred** (carried from `MATCHING.md`): M2M-per-product visibility; and
  arbitrary non-SQL `has_perm(user, obj)` rules, whose reverse can't be a `Q`
  and would fall back to a Python test over the already-narrowed candidates.

---

## 8. Implementation checklist

Done:
- [x] `Product.group` FK + migration `0002_product_group`.
- [x] `GroupFacet` (forward + reverse) wired into `ProductRows.facets`.
- [x] User identity already threaded view → `Client` → `Subscription` →
      `GroupFacet` (no change needed).
- [x] Login/logout/home + NavDrawer affordance already exist.

Left to make it demonstrable live:
- [ ] `group` select on `ProductCreateForm` + `ProductCreateView` sets it.
- [ ] `'groups'` in `UserRouter.form_fields` (or just use admin) for user→group.
- [ ] Seed fixture (groups, users-in-groups, mixed-group products).
- [ ] Optional: a "logged in as …" hint on the products page so the demo viewer
      knows which identity each tab holds (the NavDrawer already shows username).
