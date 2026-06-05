# Material Design compliance — `ryzom_example_crud` (Product demo)

A review of how far the **Product CRUD demo** (`src/ryzom_example_crud/`) is from
Material Design norms, and the steps to close the gap. Scope is the hand-built
reactive demo — `components.py` + `views.py` — not the generic `Router` path
(`crud.py` → `ryzom_django_mdc/crudlfap.py`), which is already MD-aligned because
it composes the MDC widgets directly.

The point of this doc: almost every raw control in the demo has a **drop-in MDC
widget that already ships** in `ryzom_mdc/html.py` / `ryzom_django_mdc/html.py`
(see the inventory in `CRUDLFAP_COMPONENTS.md` § "Already exists"). The gap is
mechanical — swap hand-rolled markup + inline styles for widgets we already own —
except for two spots that deviate *on purpose* (the row menu and the dialogs) to
survive DDP patching.

## Verdict

**~50–60% compliant.** A "tale of two CRUDs": the page **shell is genuinely
Material**, the interactive **content inside it is mostly raw HTML with inline
styles**. The User CRUD (generic `Router`) is far more MD-aligned than this
demo, which predates / sidesteps the widget library.

## Already compliant ✅

- **App shell** — `ProductListView` renders through `App(...)`, giving a real
  `TopAppBar`, slide-in `NavDrawer` + backdrop, Roboto, and Django messages.
- **Data-table skeleton** — `MDCDataTableResponsive` / `Thead` / `Tbody` / `Tr` /
  `Td` used correctly.
- **Create-form text fields** — `MDCTextFieldOutlined` with proper labels.
- **Row kebab trigger** — `mdc-icon-button` + `MDCIcon('more_vert')`.
- **Dialog primitives** — `ActionDialog` builds on `MDCDialogContainer/Surface/
  Scrim` (partial — see Medium gaps).

---

## Gaps & steps to close

### High — raw controls with a drop-in MDC equivalent

Low-risk, mechanical swaps. Each closes a visible piece of the gap.

| # | Where (`components.py`) | Currently | Swap to |
|---|---|---|---|
| H1 | `ProductPager` buttons (`« first`…) | raw `Button` + inline `margin/cursor` | `MDCButton` / `MDCTextButton` |
| H2 | `ProductBulkBar` `Apply`/`Clear`/`Select all matching` | raw `Button` | `MDCButton` family |
| H3 | `ProductCreateForm` group select; `ProductBulkBar` action select | raw `<Select>`/`<Option>` in a `<Label>` | `MDCSelectOutlined` / `MDCSelect` |
| H4 | `ProductPager` per-page select | raw `<Select>` | `MDCSelectPerPage` (purpose-built) |
| H5 | row-select / select-all / `in_stock` checkboxes | raw `Input(type=checkbox)` | `MDCCheckbox` / `MDCCheckboxInput` |
| H6 | `ProductDetail` container | plain `Div` + inline border/radius | `MDCCard` |
| H7 | `group_badge` | `Span` + inline `background/border-radius` | `MDCChip` (it *is* a chip) |

**Steps**

1. **Buttons (H1, H2).** Replace `Button(label, …)` with `MDCButton(label,
   tag='button', type='button', …)`. Keep the `data-action` / `data-action="apply"`
   attributes — the JS wiring keys off them, so behavior is unchanged. Drop the
   inline `margin/cursor` styles (MD buttons carry their own spacing/affordance).
2. **Selects (H3, H4).** Replace the `Label(Select(Option…))` pattern with the MDC
   select widgets. Keep the `name=` and `selected=` on the options. For the pager,
   `MDCSelectPerPage` already emits the `MDCSelect:change` event — confirm the
   pager JS listens for that instead of the native `change` (it currently does
   `select.addEventListener('change', …)`), or keep `MDCSelect` and wire `change`.
3. **Checkboxes (H5).** Swap raw checkboxes for the MDC checkbox markup. The
   row checkbox keeps `cls='row-select'` + `value=pk`; the header keeps
   `cls='select-all-page'`. All selection logic in `ProductBulkBar` is delegated
   and reads those classes/values, so it survives the swap untouched. Verify the
   MutationObserver re-projection still finds `.row-select` after the swap.
4. **Detail card (H6).** Wrap `ProductDetail`'s body in `MDCCard`; drop the inline
   border/radius/padding. Keep the `ReactiveComponentMixin` `register` id.
5. **Group chip (H7).** Replace `group_badge`'s hand-styled `Span` with `MDCChip`;
   map public→neutral, grouped→themed color via MD theme tokens (see L1).

### Medium — MD behaviors that are absent or deviate on purpose

- **M1 — No snackbar feedback.** Create / sell / bulk actions are silent (the
  table push is the only signal). MD expects an `MDCSnackBar` confirmation —
  already exists. *Step:* on a successful mutate `fetch`, show an `MDCSnackBar`
  ("Product added", "Sold 1", "3 deleted"). Server endpoints already return
  204/JSON; trigger the snackbar client-side in each custom element's handler.
- **M2 — Row context menu is non-MD.** `ProductRowActions` hand-rolls `Ul`/`Li`
  with inline `box-shadow`/`position:fixed`/manual positioning. `MDCMenu` +
  `MDCListItem` exist (proper elevation, ripple, keyboard nav). **Caveat —
  deliberate deviation:** the menu is hand-rolled because it must survive the
  row-swap on every DDP patch and be reparented to `<body>` to escape the table's
  overflow clip. *Step:* if tackled, adopt `MDCListItem` markup + MD elevation
  tokens for the surface while keeping the body-reparenting + delegation; do **not**
  blindly swap in the `MDCMenu` custom element (its JS instance won't survive the
  re-fired `load`). Lowest-risk partial win: keep the structure, apply MD
  surface/elevation/ripple styling and `role`/keyboard handling.
- **M3 — Dialogs skip real MD behavior.** `ActionDialog` toggles `mdc-dialog--open`
  by class and carries no JS instance — **deliberate**, so it survives the
  re-fired `load` after each DDP patch. Trade-off: no focus trap, no
  scrim-click-to-close, no ESC. *Step:* either accept and document (recommended),
  or add minimal JS (ESC + scrim click) without instantiating `mdc.dialog`.

### Low — theming & layout polish

- **L1 — Inline hex colors** (`#1565c0`, `#c00`, `#888`, banner backgrounds)
  instead of MD theme tokens. The shell already uses `var(--mdc-theme-primary)`.
  *Step:* replace with `--mdc-theme-primary` / `--mdc-theme-error` / surface tokens
  so theming is consistent and re-themeable.
- **L2 — Inline flex/margin layout** instead of `MDCLayoutGrid` and the MD
  typography scale; `H1`/`H2`/`P` are raw. *Step:* move toolbar/filter/pager rows
  into `MDCLayoutGrid` cells; apply MD typography classes to headings/body.
- **L3 — Ad-hoc status markers** (identity banner, "low" stock label) as inline
  colored spans/divs. *Step:* express as themed chips / an MD banner.

---

## Suggested order of work

1. **H1–H7** in one pass (buttons → selects → checkboxes → card → chip), verifying
   against the running demo after each (`run-demo` skill; both push and poll
   transports, since the JS wiring is shared). These are independent and low-risk.
2. **M1** (snackbars) — small, high perceived-quality win.
3. **L1** (theme tokens) — cheap, makes the rest look intentional.
4. **L2 / L3** — polish.
5. **M2 / M3** last, and only as **deliberate, documented** decisions — both
   deviate for a real reason (surviving DDP patching). Don't regress that to chase
   purity.

## Acceptance check per item

- Renders correctly in **both** transports (push + poll) — the row swap is the
  thing most likely to break a widget that relies on a JS instance.
- Selection / pager / filter / bulk / row-action behavior unchanged (they key off
  `data-*` attrs and CSS classes, which the swaps must preserve).
- `ruff check src` clean; demo verified live (`run-demo` → `verify` skills).
