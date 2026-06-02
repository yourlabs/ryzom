# CRUD component suite — spec for the crudlfap-on-ryzom rewrite

This is the build list of **new Ryzom components** for rebuilding CRUDLFAP
directly on Ryzom. It lives here because these components belong in/near Ryzom;
the rewrite app will consume them.

**Scope.** These are CRUDLFAP-domain *composites* — they orchestrate existing
MDC primitives off a `Router` / its `get_menu(...)` / model reflection. They are
not generic widgets.

**References.** `crudlfap:html.py:NNN` pointers below refer to the **old**
crudlfap source (external repo, `../crudlfap/src/crudlfap/`) — copy the behavior,
not the code (it carries Jinja2/metaclass/tables2 baggage we're dropping). Full
rationale and the permission/CRUD model are in the old repo's
`RYZOM_REWRITE_DESIGN.md`.

---

## Already exists — DO NOT rebuild

Confirmed in `src/ryzom_mdc/html.py` + `src/ryzom_django_mdc/html.py`:

`MDCButton*` · `MDCIconButton` · `MDCTextButton` · `MDCCard` · `MDCChip` ·
`MDCDialog` (+ `Scrim`/`Surface`/`Title`/`Content`/`Actions`/`AcceptButton`/
`CloseButton`) · `MDCMenu` · `MDCList`/`MDCListItem`/`MDCCheckboxListItem` ·
`MDCDataTable*` (full family) · `MDCDataTablePagination` · `MDCSelectPerPage` ·
`MDCSelect` · `MDCSwitch` · `MDCField`/`MDCFilterField`/`MDCFormField` ·
`MDCTextField*` · `MDCSnackBar` · `MDCTabBar` · `MDCDrawerToggle` ·
`MDCLayoutGrid` · `MDCIcon` · forms (`SimpleForm`, `InlineForm`, `CSRFInput`,
`HiddenFields`, `ErrorList`) · autocomplete (`ryzom_django_autocomplete`).

The components below **compose** these.

---

## The data contract every component relies on

A component is handed a **bound view/action** and/or a **router**. To render and
self-secure, it reads:

- **bound view** → `.icon`, `.color`, `.url`, `.label`/`.title`,
  `.permission_shortcode`, `.menus`, `.authenticate`, `.controller`
  (`'modal'` or not), `.has_perm()`, and optionally `.object`/`.object_list`.
- **router** → `.model`, `.icon`, `.get_menu(name, request, **kwargs)`,
  `.get_queryset(view)`, `.get_fields(view)`, field-list config
  (`table_fields`, `filter_fields`, `search_fields`).

**Golden rule:** an action surface is never hand-coded with permission checks —
it is rendered from `router.get_menu(name, request, ...)`, which already returns
only the bound views that pass `has_perm()` for this request. Build Tier 2
first; everything else renders through it.

---

## Tier 2 — Permission-aware navigation primitives (build first)

Tiny, and every screen's actions flow through them.

### `ActionButton`
**Purpose.** Render a single bound view as a clickable button/link. Reads
`view.icon`, `view.color`, `view.url`, `view.label`. Decides modal-vs-navigation
from `view.controller`, and wires the `_next` redirect param so the destination
knows where to return.
**Composes.** `MDCButton`/`MDCTextButton` or `A`.
**Behavior to preserve.** When `controller == 'modal'`, open in a layer/dialog and
set the accept-location so the opener refreshes on success; for destructive
actions launched from a detail page, redirect to the list afterward instead of
back to a now-deleted object.
**Ref.** `crudlfap:html.py:71` (`PageMenu.link`).

### `ActionMenu` (was `PageMenu`)
**Purpose.** Render a *list* of bound views (one menu) as a row of `ActionButton`s
— the standard "page actions" / "object actions" bar.
**Fed by.** `router.get_menu('model'|'object'|'object_detail', request, ...)`.
**Behavior to preserve.** Skip the view matching the current page; track whether
the current page is "destructible" so a delete redirects sensibly.
**Ref.** `crudlfap:html.py:61`.

### `ActionDropdown`
**Purpose.** Collapse a menu of actions into a single icon-button that opens a
dropdown — used for per-row actions in tables where horizontal space is tight.
Collapse to a plain button when only one action is allowed.
**Composes.** `MDCMenu` + `MDCIconButton`.
**Ref.** replaces `crudlfap:router.py:344` (`get_menu_component`, which used an
inline `mark_safe` HTML hack — rebuild as a real tree).

### `ModalLayer`
**Purpose.** Wrap any view component so it renders inside a modal. **Open
decision:** use the new `MDCDialog` vs Unpoly `up-layer`. This choice drives
`ActionButton` and the form success-redirect contract, so settle it first.
**Composes.** `MDCDialog` (+ parts) **or** Unpoly layer attributes.
**Behavior to preserve.** On form success, signal the opener to refresh (Unpoly
`up-accept-location`, or a dialog-close callback).
**Ref.** `crudlfap:html.py:99`.

---

## Tier 1 — CRUD screen components (the core)

### `ObjectList` (was `ObjectList`/`ListView`)
**Purpose.** The list page for a model: a header `ActionMenu` (model-level
actions like *Create*), a search bar, an optional filter drawer + active-filter
chips, a data table of the (permission-scoped) queryset, and pagination.
**Fed by.** `router`, `router.get_queryset(view)`, `router.get_menu('model')`,
`get_menu('list_action')`, and the column config.
**Composes.** `MDCDataTableResponsive` + the Tier-1 sub-components below.
**Ref.** `crudlfap:html.py:494`.

### `SortableHeader`
**Purpose.** A table column header that toggles sort order via a `?sort=` query
param and reloads only the table region.
**Composes.** `MDCDataTableTh` + `A` (with `up-target='table'`).
**Ref.** `crudlfap:html.py:739` (`th_component`).

### `TableRow`
**Purpose.** One table row: the record's cells, plus a per-row action menu
(`ActionDropdown`) and an optional selection checkbox for bulk actions.
**Behavior to preserve.** Render the row checkbox **only if** at least one
`list_action` passes `has_perm()` for *that specific record* — i.e. bind each
list-action view with `object=record` and test it. This is the per-object
permission UX in action.
**Composes.** `MDCDataTableTr`/`Td` + `MDCCheckboxInput` + `ActionDropdown`.
**Ref.** `crudlfap:html.py:708` (`row_component`).

### `BulkActionBar` (was `ListActions`)
**Purpose.** A bar of actions that operate on the currently-checked rows
(e.g. bulk delete).
**Fed by.** `router.get_menu('list_action', request)`.
**Behavior to preserve.** Client-side: gather every checked `data-pk` into the
action URL before opening it; show/hide the bar as selection changes.
**Composes.** `MDCButton` + a small custom element.
**Ref.** `crudlfap:html.py:462`.

### `SearchBar`
**Purpose.** Inline free-text search over `search_fields`, auto-submitting as the
user types and refreshing only the table.
**Behavior to preserve.** `up-autosubmit` + `up-delay≈200ms`; preserve other
query params (sort/filters) as hidden inputs.
**Composes.** `InlineForm`.
**Ref.** `crudlfap:html.py:683`.

### `FilterDrawer`
**Purpose.** A dismissible side drawer holding the filter form derived from
`filter_fields`; auto-submits and refreshes the table content.
**Composes.** `MDCFilterField` + `Form` (`up-autosubmit`, targets the table
content region).
**Ref.** `crudlfap:html.py:640` (`drawer_component`).

### `FilterChips`
**Purpose.** Show each currently-active filter as a removable chip; clicking the
chip's "x" navigates to the same list with that one filter dropped.
**Composes.** `MDCChip`.
**Ref.** `crudlfap:html.py:591`.

### `Pagination`
**Purpose.** Data-bound pager: first/prev/next/last plus a rows-per-page select,
each control doing a partial table reload.
**Composes.** `MDCDataTablePagination` + `MDCSelectPerPage`.
**Ref.** `crudlfap:html.py:788`.

### `ObjectDetail`
**Purpose.** The read/detail page for one instance: a two-column field→value
table inside a card, plus an `ActionMenu` of object-level actions.
**Fed by.** the instance's display fields, `router.get_menu('object', ...,
object=obj)`.
**Behavior to preserve.** Render related objects as links via their
`get_absolute_url()`; pretty-print JSON fields.
**Composes.** `MDCDataTable` + `NarrowCard`.
**Ref.** `crudlfap:html.py:429`.

### `ModelForm`
**Purpose.** The create/update form page: a form generated from the model
(`modelform_factory` with the router/view's field list), MDC fields, a raised
submit, and `_next`/back navigation.
**Behavior to preserve.** Carry the `_next` param through to the success
redirect; support a JSON request/response path (validation errors as JSON);
honor per-view field include/exclude.
**Composes.** `SimpleForm`/`MDCField*` + `CSRFInput`.
**Ref.** `crudlfap:html.py:323` (`FormTemplate`), form derivation in
`crudlfap:mixins/modelform.py`.

---

## Tier 0 — App shell / chrome

### `App`
**Purpose.** Root document: `<!doctype>`, head, loads Unpoly JS/CSS, sets
`<title>` from the active view, injects the CSRF `<meta>` and configures
`up.protocol` CSRF headers.
**Composes.** `Html`.
**Ref.** `crudlfap:html.py:286`.

### `TopAppBar`
**Purpose.** Fixed top bar with a hamburger that toggles the nav drawer and a
title from the view/site.
**Composes.** `MDCIconButton`.
**Ref.** `crudlfap:html.py:888`.

### `NavDrawer`
**Purpose.** The dismissible main navigation drawer.
**Fed by.** `site.get_menu('main', request)`.
**Behavior to preserve.** Support pluggable menu hooks (login/logout injection)
and show the impersonation "back to your account" entry when active.
**Composes.** `MDCList`/`MDCListItem` + `MDCDrawerToggle`.
**Ref.** `crudlfap:html.py:944`.

### `Messages`
**Purpose.** Render Django flash messages as snackbars, one per message, with an
icon and color chosen by level.
**Fed by.** `messages.get_messages(request)`.
**Composes.** `MDCSnackBar`.
**Ref.** `crudlfap:html.py:138`.

### `Spinner`
**Purpose.** Global loading indicator shown during slow Unpoly requests.
**Behavior to preserve.** Show on `up:request:late`, hide on `up:request:recover`.
**Ref.** `crudlfap:html.py:237`.

### Layout wrappers — `Container` / `NarrowCard` / `FormContainer`
**Purpose.** Width/spacing wrappers (page max-width, centered card, narrow form
column) used by the screen components.
**Ref.** `crudlfap:html.py:32,51,308`.

---

## Tier 3 — Auth / domain extras (after the core CRUD loop works)

### `Home` / `LoggedOut` / login page
**Purpose.** Simple content pages. **Ref.** `crudlfap:html.py:392,415`.

### `ImpersonationBanner`
**Purpose.** While a staff user is impersonating ("become") another user, show a
"back to your account" control. **Ref.** `crudlfap:html.py:986` (drawer hook) +
`crudlfap:crudlfap_auth/views.py`.

### `HistoryList`
**Purpose.** A timeline of admin `LogEntry` records for one object.
**Ref.** `crudlfap:mixins/object.py` (`logentries`) + `HistoryMixin`.

### `ApiPage`
**Purpose.** Swagger UI page. **Likely drop** for the rewrite. **Ref.**
`crudlfap:html.py:359`.

---

## Suggested build order

1. **Tier 2** (`ActionButton`, `ActionMenu`, `ActionDropdown`, `ModalLayer`) —
   resolve the modal decision here.
2. **CRUD loop**: `ObjectList` (1.1) + `ModelForm` + `ObjectDetail` — minimal
   table/columns first, actions via Tier 2.
3. **Tier 0 shell** to host the screens.
4. **List refinements**: `SortableHeader`, `TableRow` selection, `BulkActionBar`,
   `SearchBar`, `FilterDrawer`, `FilterChips`, `Pagination`.
5. **Tier 3** extras.
