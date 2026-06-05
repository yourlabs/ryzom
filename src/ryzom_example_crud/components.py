"""
Reactive components for the Product demo.

The layout model: a subscribed <tbody> renders one ProductRow per object and is
kept in sync by the channels DDP push (insert/change/remove). The detail view is
a registered ReactiveComponent that the server re-renders on every change.

Mutations (create / sell) are issued with fetch() from small custom elements so
the page never reloads — the table and detail update purely from the server
push, which is the whole point of the demo.
"""
from django.contrib.auth.models import Group

from ryzom_django_channels.components import (
    ReactiveComponentMixin,
    SubscribeComponentMixin,
    model_template,
)
from ryzom_django_channels.facets import BooleanFacet, GroupFacet, SearchFacet
from ryzom_django_mdc.html import *

from ryzom_example_crud.actions import actions_for


def _opts(pairs, selected):
    """Build MDCSelectOutlined optgroups from (value, label) pairs."""
    choices = [dict(index=str(i), value=str(v), label=str(text),
                    selected=(str(v) == str(selected)))
               for i, (v, text) in enumerate(pairs)]
    return [(None, choices, 0)]


# --- pluggable action dialogs (confirm / input popups) ----------------------

def ActionDialog(act, dialog_cls):
    """A hidden Material dialog for one interactive action (confirm + inputs).

    Shared by the bulk toolbar and the per-row kebab menu. Rendered as plain
    ``mdc-dialog`` markup (no ``<mdc-dialog>`` custom element), so it carries no
    JS instance and survives the ``load`` event ryzom re-fires after every DDP
    patch; the client shows/hides it purely by toggling ``mdc-dialog--open``.
    Cancel closes it; Confirm collects the field inputs and POSTs to /bulk/
    (the same generic endpoint the toolbar uses). ``dialog_cls`` namespaces the
    dialog to its owner (``bulk-dialog`` / ``row-dialog``) so each element wires
    only its own; ``data-action-slug`` lets a trigger find the right one."""
    fields = [
        MDCTextFieldOutlined(
            Input(type=f.type, name=f.name, required=f.required),
            label=f.label,
        )
        for f in act.fields
    ]
    body = Div(
        P(act.confirm) if act.confirm else None,
        *fields,
        Div(
            MDCButton('Cancel', tag='button', type='button', cls='action-cancel'),
            MDCButtonRaised('Confirm', tag='button', type='button',
                            cls='action-confirm'),
            cls='mdc-dialog__actions',
            style='display:flex;justify-content:flex-end;gap:1em',
        ),
        style='min-width:280px',
    )
    return Div(
        MDCDialogContainer(MDCDialogSurface(act.label, body, actions=Span())),
        MDCDialogScrim(),
        cls=f'mdc-dialog {dialog_cls}',
        data_action_slug=act.slug,
    )


# --- one row, the unit the server pushes -----------------------------------

def group_badge(obj):
    """A small chip naming the row's visibility group (or 'public').

    Makes per-user visibility legible: with the badge you can see *why* a row is
    or isn't in a given user's list (GroupFacet, see LOGIN.md). Public rows are
    grey; grouped rows are coloured."""
    name = obj.group.name if obj.group_id else 'public'
    colour = ('var(--mdc-theme-primary, #1565c0)' if obj.group_id
              else 'var(--mdc-theme-text-secondary-on-background, #888)')
    return MDCChip(
        name,
        style=(f'background:{colour};color:#fff;border-radius:12px;'
               'padding:0 10px;height:22px;font-size:11px;'
               'display:inline-flex;align-items:center'),
    )


def row_actions_toggle(obj):
    """The trailing ⋮ kebab button for one row — just the trigger.

    The dropdown itself is a single shared menu owned by ProductRowActions at
    page level (reparented to <body>), so it's positioned relative to the
    viewport and never clipped by the data table's overflow; this button only
    carries the row's pk. Static markup, no per-row JS (rows are replaced on
    every DDP patch); ProductRowActions wires the click by delegation."""
    return Button(
        MDCIcon('more_vert'),
        cls='mdc-icon-button row-actions__toggle',
        type='button',
        aria_label='Actions',
        aria_haspopup='menu',
        data_product_id=str(obj.id),
    )


@model_template('product-row')
class ProductRow(MDCDataTableTr):
    def __init__(self, obj):
        self.obj = obj
        low = obj.stock_qty <= 5
        super().__init__(
            MDCDataTableTd(
                # Plain checkbox; the value carries the pk. Selection state lives
                # in ProductBulkBar's Set, not here — this <tr> is replaced on
                # every DDP patch, so its `checked` is re-projected after the swap.
                MDCCheckboxInput(addcls='row-select', value=str(obj.id)),
                data_label='Select',
            ),
            MDCDataTableTd(
                A(obj.name, href=f'/crud/products/{obj.id}/'),
                data_label='Name',
            ),
            MDCDataTableTd(group_badge(obj), data_label='Group'),
            MDCDataTableTd(f'${obj.price}', data_label='Price'),
            MDCDataTableTd(
                str(obj.stock_qty),
                Span('low', style=(
                    'margin-left:6px;background:var(--mdc-theme-error, #b00020);'
                    'color:#fff;border-radius:10px;padding:1px 8px;'
                    'font-size:10px;font-weight:600'))
                if low else None,
                data_label='Stock',
            ),
            MDCDataTableTd(
                SellButton(product_id=obj.id) if obj.stock_qty > 0
                else Span('out', style='opacity:.5'),
                data_label='',
                style='text-align:right',
            ),
            MDCDataTableTd(
                row_actions_toggle(obj),
                data_label='',
                style='width:48px;text-align:right',
            ),
            id=f'product-{obj.id}',
        )


# --- the subscribed tbody: rows are its direct children ---------------------

class ProductRows(SubscribeComponentMixin, MDCDataTableTbody):
    publication = 'products'
    model_template = 'product-row'

    # Pagination is opt-in: declaring paginate_by + a *total* order makes
    # Subscription.get_queryset store only the visible window and the signal
    # handler diff windows (with ripple) instead of the whole set. The id
    # tiebreak gives a total order so two equal names have a defined rank.
    paginate_by = 5
    order = ('name', 'id')

    # The filter, expressed once as facets: applied forward to build the window
    # (SubscribeComponentMixin.get_queryset) and reused in reverse by the signal
    # handler to route a change to only the subscriptions it can affect, instead
    # of re-running every standing query. `q` lives in opts as a search term,
    # `in_stock` as a bool — exactly what ProductFilter POSTs.
    facets = [
        SearchFacet('q', 'name'),
        BooleanFacet('in_stock', 'stock_qty'),  # "on" => stock_qty > 0
        GroupFacet('group'),  # filter AND can_see(user, row): group visibility
    ]


class ProductTable(MDCDataTableResponsive):
    def __init__(self, **attrs):
        super().__init__(
            thead=MDCDataTableThead(tr=MDCDataTableHeaderTr(
                MDCDataTableTh(
                    # "Select all on this page" — toggles every rendered row;
                    # ProductBulkBar wires it and keeps its indeterminate state.
                    MDCCheckboxInput(addcls='select-all-page'),
                ),
                MDCDataTableTh('Name'),
                MDCDataTableTh('Group'),
                MDCDataTableTh('Price'),
                MDCDataTableTh('Stock'),
                MDCDataTableTh(''),   # Sell column
                MDCDataTableTh(''),   # trailing ⋮ per-row action menu column
            )),
            tbody=ProductRows(),
            style={'min-width': '100%'},
            **attrs,
        )


# --- auto-updating detail view (registered, refreshed on every change) ------

class ProductDetail(ReactiveComponentMixin, Div):
    def __init__(self, product, **kwargs):
        self.register = f'product-detail-{product.pk}'
        low = product.stock_qty <= 5
        super().__init__(
            MDCCard(
                H2(product.name, cls='mdc-typography--headline6',
                   style='margin:0 0 .5em'),
                Div('Price: ', Strong(f'${product.price}')),
                Div(
                    'In stock: ',
                    Strong(str(product.stock_qty),
                           style='color:var(--mdc-theme-error, #b00020)'
                           if low else 'color:inherit'),
                ),
                Div('updates live ✓',
                    style=('color:var(--mdc-theme-text-secondary-on-background,'
                           ' #888);font-size:12px;margin-top:1em')),
                style='padding:1.25em',
            ),
            style='max-width:360px',
        )


# --- fetch-based mutate widgets (no page reload) ----------------------------

class ProductToast(Component):
    """Page-level MDC snackbar host.

    The mutate widgets (sell / create / bulk / row actions) fetch and rely on the
    DDP push for the visible table update, which leaves the action itself without
    any acknowledgement. This host exposes ``window.ryzomToast(msg)`` so each
    handler can pop a one-line confirmation. A single reused MDC snackbar instance
    (not the stock ``MDCSnackBar``, which auto-opens on load) is driven on demand.
    """
    tag = 'product-toast'

    def __init__(self, **attrs):
        super().__init__(
            Div(
                Div(
                    Div('', cls='mdc-snackbar__label', role='status',
                        aria_live='polite'),
                    cls='mdc-snackbar__surface',
                ),
                cls='mdc-snackbar',
            ),
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires 'load' after every DDP patch; build the instance
            # once and keep window.ryzomToast pointing at it.
            if this.wired:
                return
            this.wired = True
            this.bar = new.mdc.snackbar.MDCSnackbar(
                this.querySelector('.mdc-snackbar'))
            this.label = this.querySelector('.mdc-snackbar__label')
            window.ryzomToast = this.show.bind(this)

        def show(self, msg):
            this.label.textContent = msg
            this.bar.open()


class SellButton(Component):
    tag = 'sell-button'

    def __init__(self, product_id=None, **attrs):
        super().__init__(
            MDCButton('Sell 1', tag='span'),
            data_product_id=str(product_id),
            style='cursor:pointer',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.sell.bind(this))

        async def sell(self, event):
            pid = this.dataset.productId
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            await fetch('/crud/products/' + pid + '/sell/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
            })
            if window.ryzomToast:
                window.ryzomToast('Sold 1')


class ProductCreateForm(Component):
    tag = 'product-create-form'

    def __init__(self, request=None, **attrs):
        super().__init__(
            Form(
                MDCTextFieldOutlined(
                    Input(type='text', name='name', required=True),
                    label='Name',
                ),
                MDCTextFieldOutlined(
                    Input(type='number', name='price', value='0', step='0.01'),
                    label='Price',
                ),
                MDCTextFieldOutlined(
                    Input(type='number', name='stock_qty', value='0'),
                    label='Stock',
                ),
                MDCSelectOutlined(
                    name='group', label='Group', value=['public'],
                    optgroups=_opts([('public', 'public'),
                                     *[(g.id, g.name)
                                       for g in Group.objects.all()]],
                                    selected='public'),
                ),
                CSRFInput(request) if request is not None else None,
                MDCButtonRaised('Add product', tag='button', type='submit'),
                method='post',
                action='/crud/products/create/',
                style='display:flex;gap:8px;align-items:center;flex-wrap:wrap',
            ),
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            # connectedCallback can fire before the child <form> is parsed.
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            if this.wired:
                return
            this.wired = True
            this.form = this.querySelector('form')
            if this.form:
                this.form.addEventListener('submit', this.submit.bind(this))

        async def submit(self, event):
            event.preventDefault()
            form = this.form
            await fetch(form.action, {
                method: 'POST',
                body: new.FormData(form),
            })
            form.reset()
            if window.ryzomToast:
                window.ryzomToast('Product added')


class ProductFilter(Component):
    """Live search + filter: re-filters the subscribed table over the websocket
    (debounced), so the table narrows as you type with no page reload."""
    tag = 'product-filter'

    def __init__(self, **attrs):
        super().__init__(
            MDCTextFieldOutlined(
                Input(type='search', name='q'),
                label='Search name',
            ),
            Label(
                MDCCheckboxInput(name='in_stock'),
                ' in stock only',
                style='display:flex;align-items:center;gap:4px',
            ),
            style='display:flex;gap:1.5em;align-items:center;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            # connectedCallback can fire before child <input>s are parsed, so
            # defer wiring until the document is ready.
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires window 'load' after every DDP patch, so guard
            # against re-wiring (which would stack listeners → duplicate POSTs).
            if this.wired:
                return
            this.wired = True
            this.q = this.querySelector('input[name="q"]')
            this.in_stock = this.querySelector('input[name="in_stock"]')
            this.timer = None
            this.inflight = False
            this.again = False
            this.q.addEventListener('input', this.schedule.bind(this))
            this.in_stock.addEventListener('change', this.apply.bind(this))

        def schedule(self, event):
            if this.timer:
                clearTimeout(this.timer)
            this.timer = setTimeout(this.apply.bind(this), 250)

        async def apply(self):
            # Serialize: only one filter request in flight at a time. The server
            # diffs the new filter against the subscription's stored queryset, so
            # overlapping requests would interleave that read-modify-write and
            # desync it from the DOM. If toggled mid-request, re-send the latest
            # state once the current one returns.
            if this.inflight:
                this.again = True
                return
            this.inflight = True
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            in_stock = ''
            if this.in_stock.checked:
                in_stock = '1'
            body = new.FormData()
            body.append('token', meta.content)
            body.append('q', this.q.value)
            body.append('in_stock', in_stock)
            response = await fetch('/crud/products/filter/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            # Poll mode answers with the row delta so the table narrows instantly
            # (no wait for the next poll). Push mode returns an empty list — its
            # delta arrives over the websocket. handleDDP is a no-op on [].
            data = await response.json()
            msgs = data.messages or []
            msgs.forEach(window.handleDDP)
            this.inflight = False
            if this.again:
                this.again = False
                this.apply()


class ProductPager(Component):
    """Numbered-page pager (first / prev / next / last + rows-per-page),
    reproducing the CRUDLFAP pager UX.

    Navigation POSTs the action to ProductPagerView; the visible rows update via
    the websocket push (same path as the filter), and this element refreshes its
    own indicator + button states from the JSON response. All arithmetic is done
    server-side, so the client only renders strings/booleans."""
    tag = 'product-pager'

    # MDC's select-menu options carry both the new `mdc-list-item` and the
    # deprecated classes; the GA rule wins and drops the flex centering, so the
    # option label sits at the top of its line. Restore vertical centering for
    # every MDC select menu on the page (global rule, declared here).
    sass = '''
.mdc-select__menu .mdc-deprecated-list-item
    display: flex
    align-items: center
'''

    def __init__(self, offset=0, per_page=5, total=0, **attrs):
        start = offset + 1 if total else 0
        end = min(offset + per_page, total)
        no_prev = offset <= 0
        no_next = offset + per_page >= total

        def btn(label, action, disabled):
            kw = dict(disabled=True) if disabled else {}
            return MDCButton(label, tag='button', type='button',
                             data_action=action, **kw)

        super().__init__(
            Span(f'{start}-{end} / {total}', cls='pager-status',
                 style='margin-right:1em;min-width:7em;display:inline-block'),
            btn('« first', 'first', no_prev),
            btn('‹ prev', 'prev', no_prev),
            btn('next ›', 'next', no_next),
            btn('last »', 'last', no_next),
            Div(
                MDCSelectOutlined(
                    name='per_page', label='Rows', value=[str(per_page)],
                    optgroups=_opts([(3, '3'), (5, '5'), (10, '10'), (25, '25')],
                                    selected=per_page),
                ),
                style='margin-left:1em',
            ),
            data_offset=str(offset),
            data_per_page=str(per_page),
            style='display:flex;align-items:center;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            # connectedCallback can fire before children are parsed; defer.
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires 'load' after every DDP patch; guard re-wiring.
            if this.wired:
                return
            this.wired = True
            this.status = this.querySelector('.pager-status')
            this.perPage = this.querySelector('input[name="per_page"]')
            this.inflight = False
            # Scroll anchoring (see apply): re-assert the saved position whenever
            # the rows change within a short window after a nav, so the page
            # doesn't jump to the top when the table collapses + refills.
            this.pinUntil = 0
            this.tbody = document.querySelector('.mdc-data-table__content')
            if this.tbody:
                obs = new.MutationObserver(this.repin.bind(this))
                obs.observe(this.tbody, {'childList': True})
            this.querySelector('button[data-action="first"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="prev"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="next"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="last"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('mdc-select-outlined').addEventListener(
                'MDCSelect:change', this.changePer.bind(this))

        async def nav(self, event):
            await this.apply(event.currentTarget.dataset.action,
                             this.perPage.value)

        async def changePer(self, event):
            # Changing the page size resets to the first page (server-side).
            await this.apply('per_page', event.detail.value)

        async def apply(self, action, per_page):
            # One request in flight: the server does a read-modify-write of the
            # subscription's offset, so overlapping requests would race it.
            if this.inflight:
                return
            this.inflight = True
            # Keep the viewport where it is across the row swap: removing the old
            # rows collapses the table height and the browser would jump to the
            # top. The new rows arrive a beat later (async over the websocket, or
            # inline in poll mode), so open a short window during which the tbody
            # MutationObserver (see init) re-asserts the saved position on every
            # row change — robust to either transport's timing.
            this.pinY = window.scrollY
            this.pinUntil = Date.now() + 1200
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            body.append('action', action)
            body.append('offset', this.dataset.offset)
            body.append('per_page', per_page)
            response = await fetch('/crud/products/page/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            data = await response.json()
            # Poll mode ships the new page's rows here so they swap instantly;
            # push mode returns [] (rows arrive over the websocket).
            msgs = data.messages or []
            msgs.forEach(window.handleDDP)
            this.dataset.offset = data.offset
            this.dataset.per_page = data.per_page
            this.status.textContent = data.label
            this.setDisabled('first', data.no_prev)
            this.setDisabled('prev', data.no_prev)
            this.setDisabled('next', data.no_next)
            this.setDisabled('last', data.no_next)
            this.inflight = False

        def repin(self):
            # Re-assert the scroll position saved at nav time (see apply), but
            # only while the post-nav window is open, so we never fight the user's
            # own scrolling at rest.
            if Date.now() < this.pinUntil:
                window.scrollTo(0, this.pinY)

        def setDisabled(self, action, disabled):
            this.querySelector(
                'button[data-action="' + action + '"]').disabled = disabled


class ProductBulkBar(Component):
    """Generic selection toolbar for the live table.

    The selection itself is generic; the *actions* are pluggable — each entry in
    ``actions`` is an ``Action`` from the registry (ryzom_example_crud.actions).
    Applying one POSTs the selected pks (or ``scope=all`` for "select all
    matching") to ProductBulkView, which runs the registered handler; the table
    then updates over the usual DDP push/poll. An *interactive* action (one with
    a confirm message and/or input fields) first opens its ActionDialog — the
    POST fires from the dialog's Confirm, carrying the field inputs.

    The hard part is that rows are server-rendered and *replaced* on every DDP
    patch, so a row checkbox's `checked` is lost on each swap. Selection state
    therefore lives in ``this.selected`` (a Set of id strings) — the source of
    truth — and is re-projected onto the rows by a MutationObserver after every
    swap, with ``this.allMatching`` tracking the "all matching" scope."""
    tag = 'product-bulk'

    def __init__(self, actions=None, **attrs):
        actions = actions or []
        super().__init__(
            Span('', cls='bulk-count',
                 style='min-width:8em;display:inline-block'),
            MDCSelectOutlined(
                name='bulk-action', label='Action', value=['__choose__'],
                optgroups=_opts([('__choose__', '— choose —'),
                                 *[(a.slug, a.label) for a in actions]],
                                selected='__choose__'),
            ),
            MDCButton('Apply', tag='button', type='button', data_action='apply'),
            MDCButton('Select all matching', tag='button', type='button',
                      cls='select-all-matching',
                      style='display:none'),
            Span('All matching selected. ', cls='all-matching-note',
                 style='margin-left:1em;display:none'),
            MDCButton('Clear', tag='button', type='button',
                      cls='clear-selection', style='display:none'),
            # One hidden dialog per interactive bulk action (confirm + inputs).
            *[ActionDialog(a, 'bulk-dialog') for a in actions if a.interactive],
            style='display:flex;align-items:center;gap:6px;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            # connectedCallback can fire before children are parsed; defer.
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires 'load' after every DDP patch; guard re-wiring.
            if this.wired:
                return
            this.wired = True
            this.selected = new.Set()        # id strings; survives row swaps
            this.allMatching = False         # "select all matching" scope
            this.tbody = document.querySelector('.mdc-data-table__content')
            this.selectAll = document.querySelector('.select-all-page')
            this.actionSelect = this.querySelector('input[name="bulk-action"]')
            this.countEl = this.querySelector('.bulk-count')
            this.matchBtn = this.querySelector('.select-all-matching')
            this.matchNote = this.querySelector('.all-matching-note')
            this.clearBtn = this.querySelector('.clear-selection')
            this.querySelector('button[data-action="apply"]').addEventListener(
                'click', this.apply.bind(this))
            this.matchBtn.addEventListener(
                'click', this.selectAllMatching.bind(this))
            this.clearBtn.addEventListener('click', this.clear.bind(this))
            if this.tbody:
                # Delegate row toggles (rows come and go) and re-project checked
                # state whenever the server swaps the row set.
                this.tbody.addEventListener('change', this.onRowChange.bind(this))
                obs = new.MutationObserver(this.render.bind(this))
                obs.observe(this.tbody, {'childList': True})
            if this.selectAll:
                this.selectAll.addEventListener(
                    'change', this.onSelectAll.bind(this))
            # Wire each interactive action's dialog (Cancel closes, Confirm runs).
            for dlg in this.querySelectorAll('.bulk-dialog'):
                dlg.querySelector('.action-cancel').addEventListener(
                    'click', this.cancelDialog.bind(this))
                dlg.querySelector('.action-confirm').addEventListener(
                    'click', this.confirmDialog.bind(this))
                # Scrim click dismisses, like a real MD dialog.
                dlg.querySelector('.mdc-dialog__scrim').addEventListener(
                    'click', this.cancelDialog.bind(this))
            # Escape closes whichever dialog is open.
            document.addEventListener('keydown', this.onDialogKey.bind(this))
            this.render()

        def onRowChange(self, event):
            cb = event.target
            if not cb.matches('.row-select'):
                return
            if this.allMatching:
                # Exiting "all matching" by un/checking a row: seed the explicit
                # Set from what is currently checked (the DOM already reflects
                # this toggle), then fall back to explicit selection.
                this.allMatching = False
                this.selected.clear()
                for row in this.tbody.querySelectorAll('.row-select'):
                    if row.checked:
                        this.selected.add(row.value)
                this.render()
                return
            if cb.checked:
                this.selected.add(cb.value)
            else:
                this.selected.delete(cb.value)
            this.render()

        def onSelectAll(self, event):
            # Header checkbox selects/deselects every row on the current page.
            check = this.selectAll.checked
            this.allMatching = False
            for cb in this.tbody.querySelectorAll('.row-select'):
                cb.checked = check
                if check:
                    this.selected.add(cb.value)
                else:
                    this.selected.delete(cb.value)
            this.render()

        def selectAllMatching(self, event):
            this.allMatching = True
            this.render()

        def clear(self, event):
            this.allMatching = False
            this.selected.clear()
            this.render()

        def render(self):
            # Re-project selection onto the rows currently in the DOM and refresh
            # the chrome (count, header tri-state, banner). Setting `checked`
            # programmatically does not fire 'change', so this never re-enters.
            if not this.tbody:
                return
            rows = this.tbody.querySelectorAll('.row-select')
            n = 0
            for cb in rows:
                if this.allMatching:
                    cb.checked = True
                else:
                    cb.checked = this.selected.has(cb.value)
                if cb.checked:
                    n += 1
            if this.selectAll:
                this.selectAll.checked = rows.length > 0 and n == rows.length
                this.selectAll.indeterminate = n > 0 and n < rows.length
            # Total matching rows, read off the pager indicator ("start-end / N").
            total = rows.length
            status = document.querySelector('.pager-status')
            if status:
                parts = status.textContent.split('/')
                if parts.length > 1:
                    total = parseInt(parts[1])
            label = ''
            if this.allMatching:
                label = 'All ' + total + ' matching selected'
            elif this.selected.size:
                label = this.selected.size + ' selected'
            this.countEl.textContent = label
            # Offer "select all matching" only when the whole page is selected
            # and more rows match beyond it.
            page_full = rows.length > 0 and n == rows.length
            # Reveal with '' (not 'inline') so each element falls back to its own
            # stylesheet display — the MDCButtons keep their inline-flex layout and
            # render like the Apply button instead of a squashed inline box.
            show_match = 'none'
            if page_full and not this.allMatching and total > rows.length:
                show_match = ''
            this.matchBtn.style.display = show_match
            note = 'none'
            if this.allMatching:
                note = ''
            this.matchNote.style.display = note
            this.clearBtn.style.display = note

        async def apply(self, event):
            action = this.actionSelect.value
            if not action or action == '__choose__':
                return
            # Need a selection before doing anything (explicit or "all matching").
            if not this.allMatching and this.selected.size == 0:
                return
            # Interactive action? Open its dialog and let Confirm fire the POST.
            dlg = this.querySelector(
                '.bulk-dialog[data-action-slug="' + action + '"]')
            if dlg:
                dlg.classList.add('mdc-dialog--open')
                first = dlg.querySelector('input[name]')
                if first:
                    first.focus()
                return
            await this.submit(action, None)

        async def confirmDialog(self, event):
            dlg = event.currentTarget.closest('.bulk-dialog')
            # Block on empty required inputs (rename needs a name).
            for el in dlg.querySelectorAll('input[name]'):
                if el.required and not el.value:
                    el.focus()
                    return
            dlg.classList.remove('mdc-dialog--open')
            await this.submit(dlg.dataset.actionSlug, dlg)

        def cancelDialog(self, event):
            event.currentTarget.closest('.bulk-dialog').classList.remove(
                'mdc-dialog--open')

        def onDialogKey(self, event):
            if event.key != 'Escape':
                return
            for dlg in this.querySelectorAll('.bulk-dialog.mdc-dialog--open'):
                dlg.classList.remove('mdc-dialog--open')

        async def submit(self, action, dlg):
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            body.append('action', action)
            if this.allMatching:
                body.append('scope', 'all')
            else:
                ids = []
                for v in this.selected:
                    ids.push(v)
                body.append('ids', ids.join(','))
            # Carry the dialog's field inputs (e.g. the new name) as POST params.
            if dlg:
                for el in dlg.querySelectorAll(
                        'input[name], select[name], textarea[name]'):
                    body.append(el.name, el.value)
            response = await fetch('/crud/products/bulk/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            data = await response.json()
            if window.ryzomToast:
                window.ryzomToast(data.count + ' updated')
            # Selection is consumed; the rows update via the DDP push/poll, the
            # same path the Sell button relies on.
            this.selected.clear()
            this.allMatching = False
            # Reset the select to "— choose —": drive the MDC instance so the
            # visible anchor text resets too (its change handler re-syncs the
            # hidden input). mdc.autoInit attaches the instance to the custom
            # element under its data-mdc-auto-init name.
            sel = this.querySelector('mdc-select-outlined')
            if sel and sel.MDCSelect:
                sel.MDCSelect.selectedIndex = 0
            else:
                this.actionSelect.value = '__choose__'
            this.render()


class ProductRowActions(Component):
    """Page-level host for the per-row ⋮ kebab menus and their dialogs.

    Renders one hidden ActionDialog per interactive *row* action (rename,
    delete) and drives every per-row menu by **delegation** on the subscribed
    tbody — opening/closing menus and running actions — so it survives the row
    swaps each DDP patch performs without any per-row wiring (the same discipline
    ProductBulkBar follows for selection). A non-interactive row action (restock)
    POSTs straight to /bulk/ with the single row's pk; an interactive one stashes
    the pk on its dialog and opens it, and Confirm POSTs with the field inputs."""
    tag = 'product-row-actions'

    # MD menu polish: subtle hover/focus state (ripple-ish) + typography. The
    # elevation/rounding live inline on the menu (JS also toggles its display).
    sass = '''
.row-actions__menu .row-action
    font-size: 14px
    transition: background .15s
.row-actions__menu .row-action:hover, .row-actions__menu .row-action:focus
    background: rgba(0, 0, 0, .06)
    outline: none
'''

    def __init__(self, **attrs):
        menu = Ul(
            *[Li(
                act.label,
                cls='row-action',
                role='menuitem',
                tabindex='-1',
                data_action=act.slug,
                style='display:block;padding:8px 16px;cursor:pointer;'
                      'white-space:nowrap;list-style:none',
              ) for act in actions_for('row')],
            cls='row-actions__menu',
            role='menu',
            style='display:none;position:fixed;z-index:1000;margin:0;padding:4px 0;'
                  'background:#fff;border-radius:4px;min-width:160px;'
                  # MD elevation-8 (the standard menu shadow).
                  'box-shadow:0 3px 5px -1px rgba(0,0,0,.2),'
                  '0 6px 10px 0 rgba(0,0,0,.14),0 1px 18px 0 rgba(0,0,0,.12)',
        )
        super().__init__(
            menu,
            *[ActionDialog(a, 'row-dialog')
              for a in actions_for('row') if a.interactive],
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            # connectedCallback can fire before the tbody is parsed; defer.
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires 'load' after every DDP patch; guard re-wiring.
            if this.wired:
                return
            this.wired = True
            # The shared menu lives at page level; move it onto <body> so its
            # position:fixed is measured from the viewport (not a transformed /
            # overflow-clipping ancestor like the data table) and right-aligns
            # under whichever row's ⋮ opened it. activeId holds that row's pk.
            this.menu = this.querySelector('.row-actions__menu')
            this.activeId = None
            document.body.appendChild(this.menu)
            this.menu.addEventListener('click', this.onMenuClick.bind(this))
            this.menu.addEventListener('keydown', this.onMenuKey.bind(this))
            this.tbody = document.querySelector('.mdc-data-table__content')
            if this.tbody:
                # Delegate: rows come and go, the listener on the tbody stays.
                this.tbody.addEventListener('click', this.onToggleClick.bind(this))
            # A click anywhere else dismisses the open menu.
            document.addEventListener('click', this.onDocClick.bind(this))
            for dlg in this.querySelectorAll('.row-dialog'):
                dlg.querySelector('.action-cancel').addEventListener(
                    'click', this.cancelDialog.bind(this))
                dlg.querySelector('.action-confirm').addEventListener(
                    'click', this.confirmDialog.bind(this))
                # Scrim click dismisses, like a real MD dialog.
                dlg.querySelector('.mdc-dialog__scrim').addEventListener(
                    'click', this.cancelDialog.bind(this))
            # Escape closes whichever row dialog is open.
            document.addEventListener('keydown', this.onDialogKey.bind(this))

        def onToggleClick(self, event):
            toggle = event.target.closest('.row-actions__toggle')
            if not toggle:
                return
            event.preventDefault()
            event.stopPropagation()  # don't let onDocClick immediately close it
            # Same button re-clicked => toggle closed; a different row => move it.
            sameOpen = (this.menu.style.display == 'block'
                        and this.activeId == toggle.dataset.productId)
            this.closeMenu()
            if not sameOpen:
                this.openMenu(toggle)

        def openMenu(self, toggle):
            this.activeId = toggle.dataset.productId
            this.activeToggle = toggle
            rect = toggle.getBoundingClientRect()
            this.menu.style.top = rect.bottom + 'px'
            this.menu.style.left = 'auto'
            this.menu.style.right = (window.innerWidth - rect.right) + 'px'
            this.menu.style.display = 'block'
            # Move focus into the menu so it's keyboard-navigable (MD behaviour).
            first = this.menu.querySelector('.row-action')
            if first:
                first.focus()

        def closeMenu(self):
            this.menu.style.display = 'none'

        def onMenuClick(self, event):
            item = event.target.closest('.row-action')
            if not item:
                return
            event.preventDefault()
            this.closeMenu()
            this.runRowAction(item.dataset.action, this.activeId)

        def onMenuKey(self, event):
            # Arrow/Home/End move focus, Enter/Space activate, Escape closes and
            # returns focus to the ⋮ toggle (standard MD menu keyboard model).
            items = this.menu.querySelectorAll('.row-action')
            if not items.length:
                return
            idx = -1
            i = 0
            while i < items.length:
                if items[i] == document.activeElement:
                    idx = i
                i = i + 1
            key = event.key
            if key == 'Escape':
                event.preventDefault()
                this.closeMenu()
                if this.activeToggle:
                    this.activeToggle.focus()
            elif key == 'ArrowDown':
                event.preventDefault()
                nxt = idx + 1
                if nxt >= items.length:
                    nxt = 0
                items[nxt].focus()
            elif key == 'ArrowUp':
                event.preventDefault()
                prv = idx - 1
                if prv < 0:
                    prv = items.length - 1
                items[prv].focus()
            elif key == 'Home':
                event.preventDefault()
                items[0].focus()
            elif key == 'End':
                event.preventDefault()
                items[items.length - 1].focus()
            elif key == 'Enter' or key == ' ':
                event.preventDefault()
                if idx >= 0:
                    this.closeMenu()
                    this.runRowAction(items[idx].dataset.action, this.activeId)

        def onDocClick(self, event):
            # The menu lives on <body>, so an outside click is never inside the
            # menu; close on any click that isn't on the menu itself (menu-item
            # clicks are handled + closed by onMenuClick before this fires).
            if not event.target.closest('.row-actions__menu'):
                this.closeMenu()

        def runRowAction(self, slug, pid):
            dlg = this.querySelector(
                '.row-dialog[data-action-slug="' + slug + '"]')
            if dlg:
                # Stash the row's pk and clear any leftover input from last time.
                dlg.dataset.ids = pid
                for el in dlg.querySelectorAll('input[name], textarea[name]'):
                    el.value = ''
                dlg.classList.add('mdc-dialog--open')
                first = dlg.querySelector('input[name]')
                if first:
                    first.focus()
            else:
                this.submit(slug, pid, None)

        async def confirmDialog(self, event):
            dlg = event.currentTarget.closest('.row-dialog')
            for el in dlg.querySelectorAll('input[name]'):
                if el.required and not el.value:
                    el.focus()
                    return
            dlg.classList.remove('mdc-dialog--open')
            await this.submit(dlg.dataset.actionSlug, dlg.dataset.ids, dlg)

        def cancelDialog(self, event):
            event.currentTarget.closest('.row-dialog').classList.remove(
                'mdc-dialog--open')

        def onDialogKey(self, event):
            if event.key != 'Escape':
                return
            for dlg in this.querySelectorAll('.row-dialog.mdc-dialog--open'):
                dlg.classList.remove('mdc-dialog--open')

        async def submit(self, slug, ids, dlg):
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            body.append('action', slug)
            body.append('ids', ids)
            if dlg:
                for el in dlg.querySelectorAll(
                        'input[name], select[name], textarea[name]'):
                    body.append(el.name, el.value)
            # The visible update arrives over the DDP push/poll, like SellButton.
            await fetch('/crud/products/bulk/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            if window.ryzomToast:
                window.ryzomToast('Done')
