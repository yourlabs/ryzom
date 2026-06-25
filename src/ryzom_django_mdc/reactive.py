"""
Generic, model-driven **reactive** CRUD for ryzom_django_mdc.

This is the reactive sibling of the classic ``Router`` in ``crud.py``: where that
one renders plain pages and reloads, ``ReactiveRouter`` builds a live table kept
in sync over the channels DDP push (or the polling fallback) — the machinery the
hand-written Product demo pioneered, lifted into one declarative class.

You describe a model once::

    class ProductCrud(ReactiveRouter):
        model = Product
        publication = 'products'          # the @publish method name
        order = ('name', 'id')
        paginate_by = 5
        facets = [SearchFacet('q', 'name'), BooleanFacet('in_stock', 'stock_qty')]
        columns = [
            Column('name', link_detail=True),
            Column('price', cell=lambda o: f'${o.price}'),
        ]
        actions = [Action('delete', 'Delete', delete_fn, scopes=('bulk', 'row'))]

    urlpatterns, app_name = ProductCrud.get_urls()

and get the live list (filter + click-to-sort + pager + bulk toolbar + per-row ⋮
menu + toast), an auto-updating detail card, and a create form — all generic.

How the genericity works (the three constraints the reactive core imposes, see
the design notes): (1) a subscription is reconstructed in another process from a
stored ``module``/``class`` name, so the per-model ``Rows``/``Row`` classes must
be *importable* — ``ReactiveRouter.__init_subclass__`` generates them and injects
them into the router's own module; (2) filter facets / order / pagination are
read off the subscriber *class*, so each model gets its own generated subscriber
class (not a shared one); (3) the custom-element JS bakes its endpoint URL in at
transpile time, so every widget reads its base from a ``data-endpoint`` attribute
set at render instead of a literal path.
"""
import sys

from django.db import transaction
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.views import View

from ryzom_django_channels.components import (
    ReactiveComponentMixin,
    SubscribeComponentMixin,
    model_template,
)
from ryzom_django_channels.facets import BooleanFacet, SearchFacet
from ryzom_django_channels.models import Client, Subscription
from ryzom_django_channels.views import ReactiveMixin, ddp_poll
from ryzom_django_mdc.crud import App, _field_label, _field_value
from ryzom_django_mdc.html import *

from dataclasses import dataclass
from typing import Callable


def _opts(pairs, selected):
    """Build MDCSelectOutlined optgroups from (value, label) pairs."""
    choices = [dict(index=str(i), value=str(v), label=str(text),
                    selected=(str(v) == str(selected)))
               for i, (v, text) in enumerate(pairs)]
    return [(None, choices, 0)]


# ---------------------------------------------------------------------------
# Declarative column + action specs
# ---------------------------------------------------------------------------

@dataclass
class Column:
    """One table column.

    ``name`` is the model field (used for the default cell value, the
    ``data-label`` and the sort field). ``cell(obj)`` overrides the rendered
    content (a chip, a button, a formatted string); ``link_detail`` wraps the
    default value in a link to the object's detail page. ``sortable`` is a bool
    or the *real* column to order by when it differs from ``name`` (e.g. a FK
    rendered as ``group`` sorts by ``group_id``); ``False`` makes a plain,
    unclickable header (action/widget columns). ``td_style`` is applied to the
    ``<td>`` (e.g. right-aligned action cells).
    """
    name: str = ''
    label: str = None                 # None -> capfirst(name)
    cell: Callable = None             # cell(obj) -> component / str
    link_detail: bool = False
    sortable: object = True           # True | False | 'real_sort_field'
    td_style: str = None

    @property
    def header_label(self):
        return self.label if self.label is not None else _field_label(self.name)

    @property
    def sort_field(self):
        """The model field to order by, or None when the column isn't sortable."""
        if self.sortable is False:
            return None
        return self.sortable if isinstance(self.sortable, str) else self.name


@dataclass
class Field:
    """One input rendered inside an action's confirmation dialog."""
    name: str
    label: str
    type: str = 'text'
    required: bool = False


@dataclass
class Action:
    """A pluggable bulk / per-row action.

    ``fn(queryset, request)`` mutates the resolved rows **per object** so the
    Publishable signals fire and every live table refreshes (never ``.update()``
    / bulk delete — those skip the per-row signals). ``confirm``/``fields`` make
    it *interactive*: the client opens a dialog before running it, and the field
    inputs arrive as ordinary POST params. ``scopes`` picks where it appears:
    ``'bulk'`` (selection toolbar) and/or ``'row'`` (per-row ⋮ menu).
    """
    slug: str
    label: str
    fn: Callable
    confirm: str = None
    fields: tuple = ()
    scopes: tuple = ('bulk',)

    @property
    def interactive(self):
        return bool(self.confirm or self.fields)


def actions_for(actions, scope):
    """The subset of ``actions`` available in ``scope`` ('bulk' or 'row')."""
    return [a for a in actions if scope in a.scopes]


# ---------------------------------------------------------------------------
# Pluggable action dialog (confirm + inputs) — shared by bulk bar and row menu
# ---------------------------------------------------------------------------

def ActionDialog(act, dialog_cls):
    """A hidden Material dialog for one interactive action (confirm + inputs).

    Rendered as plain ``mdc-dialog`` markup (no ``<mdc-dialog>`` custom element),
    so it carries no JS instance and survives the ``load`` event ryzom re-fires
    after every DDP patch; the client shows/hides it by toggling
    ``mdc-dialog--open``. ``dialog_cls`` namespaces it to its owner
    (``bulk-dialog`` / ``row-dialog``); ``data-action-slug`` lets a trigger find
    the right one. Confirm collects the inputs and POSTs to the bulk endpoint.
    """
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


# ---------------------------------------------------------------------------
# One row — the unit the server pushes
# ---------------------------------------------------------------------------

def row_actions_toggle(obj, model_name):
    """The trailing ⋮ kebab trigger for one row.

    The dropdown itself is a single shared menu owned by ReactiveRowActions at
    page level (reparented to <body>), so it's positioned relative to the
    viewport and never clipped by the data table's overflow; this button only
    carries the row's pk. Static markup, no per-row JS (rows are replaced on
    every DDP patch); ReactiveRowActions wires the click by delegation."""
    return MDCIconButton(
        'more_vert',
        addcls='row-actions__toggle',
        aria_label='Actions',
        aria_haspopup='menu',
        data_obj_id=str(obj.pk),
    )


class ReactiveRow(MDCDataTableTr):
    """One data-table row built from the router's column spec.

    Subclassed (per model) by ``ReactiveRouter`` with ``columns`` / ``router`` /
    ``show_select`` / ``show_kebab`` bound as class attributes, then registered
    as a ``model_template`` so the push/poll layer can re-render a single row.
    The deterministic ``id=f'{model_name}-{pk}'`` is what change/remove target.
    """
    columns = []
    router = None
    show_select = False
    show_kebab = False

    def __init__(self, obj):
        self.obj = obj
        model_name = self.router.model._meta.model_name
        cells = []
        if self.show_select:
            # Plain checkbox; the value carries the pk. Selection state lives in
            # ReactiveBulkBar's Set, not here — this <tr> is replaced on every DDP
            # patch, so its `checked` is re-projected after the swap.
            cells.append(MDCDataTableTd(
                MDCCheckboxInput(addcls='row-select', value=str(obj.pk)),
                data_label='Select',
            ))
        for col in self.columns:
            td_attrs = {}
            if col.td_style:
                td_attrs['style'] = col.td_style
            cells.append(MDCDataTableTd(
                self.render_cell(col, obj),
                data_label=col.header_label,
                **td_attrs,
            ))
        if self.show_kebab:
            cells.append(MDCDataTableTd(
                row_actions_toggle(obj, model_name),
                data_label='', style='width:48px;text-align:right',
            ))
        super().__init__(*cells, id=f'{model_name}-{obj.pk}')

    def render_cell(self, col, obj):
        if col.cell is not None:
            return col.cell(obj)
        value = _field_value(obj, col.name)
        if col.link_detail:
            return MDCLink(value, href=self.router.reverse_url('detail', obj.pk))
        return value


# ---------------------------------------------------------------------------
# The subscribed <tbody>: rows are its direct children
# ---------------------------------------------------------------------------

class ReactiveRows(SubscribeComponentMixin, MDCDataTableTbody):
    """Base for the subscribed table body.

    The per-model subclass (generated by ``ReactiveRouter``) sets ``publication``
    / ``model_template`` / ``facets`` / ``order`` / ``paginate_by``. Pagination
    is opt-in: declaring ``paginate_by`` + a total ``order`` makes the
    subscription store only the visible window and diff windows on change.
    """
    facets = []


def sortable_th(label, field):
    """A clickable, sortable column header.

    Carries the model field in ``data-sort-field`` and a ``.sort-arrow`` slot;
    ReactiveSort delegates the click and sets the ▲/▼ indicator. ``addcls`` keeps
    the MDC header-cell class (``cls`` would replace it)."""
    return MDCDataTableTh(
        label,
        Span(cls='sort-arrow'),
        addcls='sortable',
        data_sort_field=field,
        style='cursor:pointer;user-select:none',
    )


class ReactiveTable(MDCDataTableResponsive):
    """thead (sortable headers from the columns) + the subscribed tbody."""

    def __init__(self, router, **attrs):
        columns = router.columns
        header_cells = []
        if router.has_bulk:
            # "Select all on this page" — toggles every rendered row;
            # ReactiveBulkBar wires it and keeps its indeterminate state.
            header_cells.append(MDCDataTableTh(
                MDCCheckboxInput(addcls='select-all-page'),
            ))
        for col in columns:
            field = col.sort_field
            if field and col.header_label:
                header_cells.append(sortable_th(col.header_label, field))
            else:
                header_cells.append(MDCDataTableTh(col.header_label))
        if router.has_row:
            header_cells.append(MDCDataTableTh(''))   # trailing ⋮ column

        super().__init__(
            thead=MDCDataTableThead(tr=MDCDataTableHeaderTr(*header_cells)),
            tbody=router.rows_class(),
            style={'min-width': '100%'},
            **attrs,
        )


class ReactiveSort(Component):
    """Click-to-sort driver for the table headers.

    Renders nothing itself; it delegates clicks on the static ``.sortable`` thead
    cells (which live outside the swapped tbody, so wiring survives DDP patches).
    Clicking a new column sorts ascending; re-clicking the active column toggles
    direction. It POSTs the column + direction to the sort endpoint and applies
    the returned row delta (poll mode) — push mode returns [] and the rows arrive
    over the socket, exactly like the filter. ``data-endpoint`` + ``data-default``
    carry the base URL and the column reflecting the subscription's initial order.
    """
    tag = 'reactive-sort'

    def __init__(self, endpoint='', default_field='', **attrs):
        super().__init__(data_endpoint=endpoint, data_default=default_field,
                         **attrs)

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # Bind exactly one document-level listener even if this element is
            # re-created by a DDP patch — the active column + direction live in
            # the DOM (each header's data-sort-dir + arrow), so a fresh element
            # must NOT re-bind or reset anything.
            if window.ryzomSortWired:
                return
            window.ryzomSortWired = True
            this.endpoint = this.dataset.endpoint
            document.addEventListener('click', this.onClick.bind(this))
            # Reflect the subscription's default order.
            field = this.dataset.default
            if field:
                head = document.querySelector(
                    '.sortable[data-sort-field="' + field + '"]')
                if head:
                    this.mark(head, 'asc')

        def mark(self, th, direction):
            for h in document.querySelectorAll('.sortable'):
                h.dataset.sortDir = ''
                old = h.querySelector('.sort-arrow')
                if old:
                    old.textContent = ''
            th.dataset.sortDir = direction
            arrow = th.querySelector('.sort-arrow')
            if arrow:
                if direction == 'asc':
                    arrow.textContent = ' ▲'
                else:
                    arrow.textContent = ' ▼'

        async def onClick(self, event):
            th = event.target.closest('.sortable')
            if not th:
                return
            if th.dataset.sortDir == 'asc':
                direction = 'desc'
            else:
                direction = 'asc'
            this.mark(th, direction)
            await this.apply(th.dataset.sortField, direction)

        async def apply(self, field, direction):
            if window.ryzomSortInflight:
                return
            window.ryzomSortInflight = True
            if window.ryzomPin:
                window.ryzomPin()
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            body.append('col', field)
            body.append('dir', direction)
            response = await fetch(this.endpoint + 'sort/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            data = await response.json()
            msgs = data.messages or []
            msgs.forEach(window.handleDDP)
            window.ryzomSortInflight = False


# ---------------------------------------------------------------------------
# Auto-updating detail view (registered, refreshed on every change)
# ---------------------------------------------------------------------------

class ReactiveDetail(ReactiveComponentMixin, Div):
    """Single-object card kept live: re-rendered + pushed whenever it changes.

    Renders ``detail_fields`` as a label/value card; a router may override
    ``detail_cell(obj, field)`` to customise any value (e.g. colour a low-stock
    figure). ``register`` names the registration the model's ``post_save``
    refresh targets. ``router`` is bound on the generated per-model subclass so
    the registration can be reconstructed (``content_class(obj, user=…)``) in the
    worker / poll process from just the instance.
    """
    router = None

    def __init__(self, obj, **kwargs):
        router = self.router
        model_name = router.model._meta.model_name
        self.register = f'{model_name}-detail-{obj.pk}'
        fields = router.get_detail_fields()
        rows = []
        for fname in fields:
            value = router.detail_cell(obj, fname)
            if value is None:
                value = _field_value(obj, fname)
            rows.append(Div(
                Span(_field_label(fname) + ': ',
                     style='color:var(--mdc-theme-text-secondary-on-background,'
                           ' #888)'),
                Strong(value),
                style='margin:.25em 0',
            ))
        super().__init__(
            MDCCard(
                H2(str(obj), cls='mdc-typography--headline6',
                   style='margin:0 0 .5em'),
                *rows,
                Div('updates live ✓',
                    style=('color:var(--mdc-theme-text-secondary-on-background,'
                           ' #888);font-size:12px;margin-top:1em')),
                style='padding:1.25em',
            ),
            style='max-width:360px',
        )


# ---------------------------------------------------------------------------
# Page-level snackbar host: window.ryzomToast(msg)
# ---------------------------------------------------------------------------

class ReactiveToast(Component):
    """Page-level MDC snackbar host.

    The mutate widgets fetch and rely on the DDP push for the visible update,
    which leaves the action without acknowledgement. This host embeds a shared
    ``MDCSnackBar`` in imperative mode and points ``window.ryzomToast(msg)`` at
    its ``show()`` so each handler can pop a one-line confirmation. It survives
    the ``load`` ryzom re-fires after each DDP patch.
    """
    tag = 'reactive-toast'

    def __init__(self, **attrs):
        super().__init__(MDCSnackBar(auto_open=False, action=None), **attrs)

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            if this.wired:
                return
            this.wired = True
            this.bar = this.querySelector('.mdc-snackbar')
            window.ryzomToast = this.bar.show.bind(this.bar)


# ---------------------------------------------------------------------------
# Live search + filter (built from the router's UI facets)
# ---------------------------------------------------------------------------

class ReactiveFilter(Component):
    """Live search + filter: re-filters the subscribed table over the websocket
    (debounced), so the table narrows as you type with no page reload.

    The inputs are built from the router's facets that carry a UI: a
    ``SearchFacet`` renders a search box, a ``BooleanFacet`` a checkbox (labelled
    via the router's ``filter_labels``). Other facets (e.g. the user-scoped
    ``GroupFacet``) drive the queryset but render nothing. Reads ``data-endpoint``
    to POST ``…/filter/``.
    """
    tag = 'reactive-filter'

    def __init__(self, router, endpoint='', **attrs):
        labels = router.filter_labels or {}
        inputs = []
        search_keys = []
        bool_keys = []
        for facet in router.facets:
            if isinstance(facet, SearchFacet):
                search_keys.append(facet.key)
                inputs.append(MDCTextFieldOutlined(
                    Input(type='search', name=facet.key),
                    label=labels.get(facet.key, f'Search {facet.field}'),
                ))
            elif isinstance(facet, BooleanFacet):
                bool_keys.append(facet.key)
                inputs.append(MDCCheckboxField(
                    MDCCheckboxInput(name=facet.key),
                    name=facet.key,
                    label=labels.get(facet.key, _field_label(facet.key)),
                ))
        super().__init__(
            *inputs,
            data_endpoint=endpoint,
            data_search=','.join(search_keys),
            data_bools=','.join(bool_keys),
            style='display:flex;gap:1.5em;align-items:center;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            # ryzom.js re-fires window 'load' after every DDP patch, so guard
            # against re-wiring (which would stack listeners -> duplicate POSTs).
            if this.wired:
                return
            this.wired = True
            this.endpoint = this.dataset.endpoint
            this.searchKeys = this.dataset.search.split(',')
            this.boolKeys = this.dataset.bools.split(',')
            this.timer = None
            this.inflight = False
            this.again = False
            for key in this.searchKeys:
                if not key:
                    continue
                el = this.querySelector('input[name="' + key + '"]')
                if el:
                    el.addEventListener('input', this.schedule.bind(this))
            for key in this.boolKeys:
                if not key:
                    continue
                el = this.querySelector('input[name="' + key + '"]')
                if el:
                    el.addEventListener('change', this.apply.bind(this))

        def schedule(self, event):
            if this.timer:
                clearTimeout(this.timer)
            this.timer = setTimeout(this.apply.bind(this), 250)

        async def apply(self):
            # Serialize: only one filter request in flight at a time. The server
            # diffs the new filter against the subscription's stored queryset, so
            # overlapping requests would interleave that read-modify-write and
            # desync it from the DOM. If toggled mid-request, re-send once.
            if this.inflight:
                this.again = True
                return
            this.inflight = True
            if window.ryzomPin:
                window.ryzomPin()
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            for key in this.searchKeys:
                if not key:
                    continue
                el = this.querySelector('input[name="' + key + '"]')
                if el:
                    body.append(key, el.value)
            for key in this.boolKeys:
                if not key:
                    continue
                el = this.querySelector('input[name="' + key + '"]')
                val = ''
                if el and el.checked:
                    val = '1'
                body.append(key, val)
            response = await fetch(this.endpoint + 'filter/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            # Poll mode answers with the row delta so the table narrows instantly;
            # push mode returns []. handleDDP is a no-op on [].
            data = await response.json()
            msgs = data.messages or []
            msgs.forEach(window.handleDDP)
            this.inflight = False
            if this.again:
                this.again = False
                this.apply()


# ---------------------------------------------------------------------------
# Numbered-page pager
# ---------------------------------------------------------------------------

class ReactivePager(Component):
    """Numbered-page pager (first / prev / next / last + rows-per-page).

    Navigation POSTs the action to the page endpoint; the visible rows update via
    the push (same path as the filter), and this element refreshes its own
    indicator + button states from the JSON response. All arithmetic is
    server-side. Reads ``data-endpoint`` to POST ``…/page/``.
    """
    tag = 'reactive-pager'

    sass = '''
.mdc-select__menu .mdc-deprecated-list-item
    display: flex
    align-items: center
'''

    def __init__(self, offset=0, per_page=5, total=0, endpoint='', **attrs):
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
            data_endpoint=endpoint,
            style='display:flex;align-items:center;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            if this.wired:
                return
            this.wired = True
            this.endpoint = this.dataset.endpoint
            this.status = this.querySelector('.pager-status')
            this.perPage = this.querySelector('input[name="per_page"]')
            this.inflight = False
            this.pinUntil = 0
            this.tbody = document.querySelector('.mdc-data-table__content')
            this.tableBox = document.querySelector('.mdc-data-table__table-container')
            if this.tbody:
                obs = new.MutationObserver(this.repin.bind(this))
                obs.observe(this.tbody, {'childList': True})
            window.ryzomPin = this.pinScroll.bind(this)
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
            await this.apply('per_page', event.detail.value)

        async def apply(self, action, per_page):
            if this.inflight:
                return
            this.inflight = True
            this.pinScroll()
            meta = document.querySelector('meta[name="ryzom-config"]')
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            body = new.FormData()
            body.append('token', meta.content)
            body.append('action', action)
            body.append('offset', this.dataset.offset)
            body.append('per_page', per_page)
            response = await fetch(this.endpoint + 'page/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            data = await response.json()
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

        def pinScroll(self):
            this.pinY = window.scrollY
            this.pinUntil = Date.now() + 1200
            if this.tableBox:
                this.tableBox.style.minHeight = this.tableBox.offsetHeight + 'px'
                setTimeout(this.releaseBox.bind(this), 1200)

        def releaseBox(self):
            if this.tableBox:
                this.tableBox.style.minHeight = ''

        def repin(self):
            if Date.now() < this.pinUntil:
                window.scrollTo(0, this.pinY)

        def setDisabled(self, action, disabled):
            this.querySelector(
                'button[data-action="' + action + '"]').disabled = disabled


# ---------------------------------------------------------------------------
# Selection toolbar (bulk actions)
# ---------------------------------------------------------------------------

class ReactiveBulkBar(Component):
    """Generic selection toolbar for the live table.

    Selection is generic; the *actions* are the router's ``Action`` entries.
    Applying one POSTs the selected pks (or ``scope=all`` for "select all
    matching") to the bulk endpoint, which runs the handler; the table updates
    over the usual push/poll. An interactive action opens its ActionDialog first.

    Rows are server-rendered and replaced on every DDP patch, so a checkbox's
    ``checked`` is lost on each swap. Selection state lives in ``this.selected``
    (a Set of id strings) and is re-projected onto the rows by a MutationObserver
    after every swap, with ``this.allMatching`` tracking the "all matching" scope.
    """
    tag = 'reactive-bulk'

    def __init__(self, actions=None, endpoint='', **attrs):
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
                      addcls='select-all-matching',
                      style='display:none'),
            Span('All matching selected. ', cls='all-matching-note',
                 style='margin-left:1em;display:none'),
            MDCButton('Clear', tag='button', type='button',
                      addcls='clear-selection', style='display:none'),
            *[ActionDialog(a, 'bulk-dialog') for a in actions if a.interactive],
            data_endpoint=endpoint,
            style='display:flex;align-items:center;gap:6px;margin:1em 0',
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            if this.wired:
                return
            this.wired = True
            this.endpoint = this.dataset.endpoint
            this.selected = new.Set()
            this.allMatching = False
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
                this.tbody.addEventListener('change', this.onRowChange.bind(this))
                obs = new.MutationObserver(this.render.bind(this))
                obs.observe(this.tbody, {'childList': True})
            if this.selectAll:
                this.selectAll.addEventListener(
                    'change', this.onSelectAll.bind(this))
            for dlg in this.querySelectorAll('.bulk-dialog'):
                dlg.querySelector('.action-cancel').addEventListener(
                    'click', this.cancelDialog.bind(this))
                dlg.querySelector('.action-confirm').addEventListener(
                    'click', this.confirmDialog.bind(this))
                dlg.querySelector('.mdc-dialog__scrim').addEventListener(
                    'click', this.cancelDialog.bind(this))
            document.addEventListener('keydown', this.onDialogKey.bind(this))
            this.render()

        def onRowChange(self, event):
            cb = event.target
            if not cb.matches('.row-select'):
                return
            if this.allMatching:
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
            page_full = rows.length > 0 and n == rows.length
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
            if not this.allMatching and this.selected.size == 0:
                return
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
            if dlg:
                for el in dlg.querySelectorAll(
                        'input[name], select[name], textarea[name]'):
                    body.append(el.name, el.value)
            response = await fetch(this.endpoint + 'bulk/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            data = await response.json()
            if window.ryzomToast:
                window.ryzomToast(data.count + ' updated')
            this.selected.clear()
            this.allMatching = False
            sel = this.querySelector('mdc-select-outlined')
            if sel and sel.MDCSelect:
                sel.MDCSelect.selectedIndex = 0
            else:
                this.actionSelect.value = '__choose__'
            this.render()


# ---------------------------------------------------------------------------
# Per-row ⋮ kebab menus + their dialogs
# ---------------------------------------------------------------------------

class ReactiveRowActions(Component):
    """Page-level host for the per-row ⋮ kebab menus and their dialogs.

    Renders one hidden ActionDialog per interactive *row* action and drives every
    per-row menu by delegation on the subscribed tbody, so it survives the row
    swaps each DDP patch performs without any per-row wiring. A non-interactive
    row action POSTs straight to the bulk endpoint with the single row's pk; an
    interactive one stashes the pk on its dialog and opens it, and Confirm POSTs
    with the field inputs. Reads ``data-endpoint`` to POST ``…/bulk/``.
    """
    tag = 'reactive-row-actions'

    sass = '''
.row-actions__menu .row-action
    font-size: 14px
    cursor: pointer
    white-space: nowrap
    transition: background .15s
.row-actions__menu .row-action:hover, .row-actions__menu .row-action:focus
    background: rgba(0, 0, 0, .06)
    outline: none
'''

    def __init__(self, actions=None, endpoint='', **attrs):
        actions = actions or []
        menu = Ul(
            *[MDCListItem(
                act.label,
                addcls='row-action',
                role='menuitem',
                tabindex='-1',
                data_action=act.slug,
                ripple=False,
              ) for act in actions],
            cls='row-actions__menu',
            role='menu',
            style='display:none;position:fixed;z-index:1000;margin:0;padding:4px 0;'
                  'background:#fff;border-radius:4px;min-width:160px;'
                  'box-shadow:0 3px 5px -1px rgba(0,0,0,.2),'
                  '0 6px 10px 0 rgba(0,0,0,.14),0 1px 18px 0 rgba(0,0,0,.12)',
        )
        super().__init__(
            menu,
            *[ActionDialog(a, 'row-dialog') for a in actions if a.interactive],
            data_endpoint=endpoint,
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            if this.wired:
                return
            this.wired = True
            this.endpoint = this.dataset.endpoint
            this.menu = this.querySelector('.row-actions__menu')
            this.activeId = None
            document.body.appendChild(this.menu)
            this.menu.addEventListener('click', this.onMenuClick.bind(this))
            this.menu.addEventListener('keydown', this.onMenuKey.bind(this))
            this.tbody = document.querySelector('.mdc-data-table__content')
            if this.tbody:
                this.tbody.addEventListener('click', this.onToggleClick.bind(this))
            document.addEventListener('click', this.onDocClick.bind(this))
            for dlg in this.querySelectorAll('.row-dialog'):
                dlg.querySelector('.action-cancel').addEventListener(
                    'click', this.cancelDialog.bind(this))
                dlg.querySelector('.action-confirm').addEventListener(
                    'click', this.confirmDialog.bind(this))
                dlg.querySelector('.mdc-dialog__scrim').addEventListener(
                    'click', this.cancelDialog.bind(this))
            document.addEventListener('keydown', this.onDialogKey.bind(this))

        def onToggleClick(self, event):
            toggle = event.target.closest('.row-actions__toggle')
            if not toggle:
                return
            event.preventDefault()
            event.stopPropagation()
            sameOpen = (this.menu.style.display == 'block'
                        and this.activeId == toggle.dataset.objId)
            this.closeMenu()
            if not sameOpen:
                this.openMenu(toggle)

        def openMenu(self, toggle):
            this.activeId = toggle.dataset.objId
            this.activeToggle = toggle
            rect = toggle.getBoundingClientRect()
            this.menu.style.top = rect.bottom + 'px'
            this.menu.style.left = 'auto'
            this.menu.style.right = (window.innerWidth - rect.right) + 'px'
            this.menu.style.display = 'block'
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
            if not event.target.closest('.row-actions__menu'):
                this.closeMenu()

        def runRowAction(self, slug, pid):
            dlg = this.querySelector(
                '.row-dialog[data-action-slug="' + slug + '"]')
            if dlg:
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
            await fetch(this.endpoint + 'bulk/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            if window.ryzomToast:
                window.ryzomToast('Done')


# ---------------------------------------------------------------------------
# Create form (fetch-POSTs a ModelForm, no reload)
# ---------------------------------------------------------------------------

class ReactiveCreateForm(Component):
    """Inline create form that fetch-POSTs a Django ModelForm.

    The visible update is the insert push, not the HTTP response (like every
    mutate widget here): on submit it POSTs the form, resets it, and toasts.
    """
    tag = 'reactive-create-form'

    def __init__(self, form, action='', request=None, submit_label='Add', **attrs):
        super().__init__(
            Form(
                form,
                CSRFInput(request) if request is not None else None,
                MDCButtonRaised(submit_label, tag='button', type='submit'),
                method='post',
                action=action,
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
                window.ryzomToast('Added')


# ---------------------------------------------------------------------------
# Shared server helpers (window delta delivery — generic over the model)
# ---------------------------------------------------------------------------

def _ryzom_js():
    # The DDP websocket / poll client, injected into <head> per render.
    return Script(src='/static/ryzom.js')


def _sub_id(client, publication):
    """The id of this client's subscription to ``publication`` (or None)."""
    return (
        Subscription.objects
        .filter(client=client, publication__name=publication)
        .values_list('id', flat=True)
        .last()
    )


def _push_window_replace(sub, old_window, new_rows):
    """Push the row delta between two windows over the websocket.

    Shared by the filter, pager and sort views: each does a read-modify-write of
    the subscription's window and then brings the DOM in line. Removes first,
    then inserts in ascending window position. A pure *reorder* of the surviving
    rows can't be expressed with position ops, so replace the whole window then.
    Generic over the model via ``sub.publication.model``.
    """
    from ryzom_django_channels.components import model_templates
    from ryzom_django_channels.ddp import send_insert, send_remove

    model = sub.publication.model
    tmpl = model_templates[sub.subscriber.model_template]
    new_window = [obj.pk for obj in new_rows]
    rows = {obj.pk: obj for obj in new_rows}
    old_set, new_set = set(old_window), set(new_window)

    stayed_old_order = [pk for pk in old_window if pk in new_set]
    stayed_new_order = [pk for pk in new_window if pk in old_set]
    if stayed_old_order != stayed_new_order:
        for pk in old_window:
            obj = model.objects.filter(pk=pk).first() or model(pk=pk)
            send_remove(sub, tmpl, obj)
        for pk in new_window:
            send_insert(sub, tmpl, rows[pk])
        return

    for pk in old_set - new_set:
        obj = model.objects.filter(pk=pk).first() or model(pk=pk)
        send_remove(sub, tmpl, obj)
    for pk in sorted(new_set - old_set, key=new_window.index):
        send_insert(sub, tmpl, rows[pk])


def _deliver_window_change(sub, opts):
    """Apply a filter/pager/sort change to one subscription, per its transport.

    Returns the DDP messages the *originating* client should apply now (empty for
    a push client, whose delta goes over the channel layer instead). A push
    client gets the delta now over the channel layer (advancing its stored
    window); a poll client records the new intent and gets the window diff
    computed by the same engine the poll loop uses (see POLLING.md).
    """
    if sub.client and sub.client.channel:
        old_window = list(sub.queryset)
        new_rows = list(sub.get_queryset(opts))      # advances + persists qs
        _push_window_replace(sub, old_window, new_rows)
        return []

    from ryzom_django_channels.polling import subscription_delta

    sub.options = dict(opts)                          # new intent; qs untouched
    return subscription_delta(sub)


# ---------------------------------------------------------------------------
# The generic reactive Router
# ---------------------------------------------------------------------------

class ReactiveRouter:
    """Declarative, model-driven reactive CRUD. Subclass and set ``model`` +
    ``publication`` to get a live list/detail/create suite. See the module
    docstring for the full example."""

    model = None
    publication = None
    namespace = None              # URL namespace; defaults to the model name

    columns = []
    facets = []
    order = None                  # total order, e.g. ('name', 'id')
    paginate_by = None            # opt-in pagination window size
    filter_labels = None          # {facet_key: 'Search name', ...}

    create_fields = None          # None -> no create form
    detail_fields = None          # None -> column fields
    actions = []                  # bulk + row Action entries

    site_title = None             # nav/app-bar title; default verbose_name_plural
    list_heading = None           # H1 on the list page; default verbose_name_plural
    nav_items = []

    # Derived in __init_subclass__:
    has_bulk = False
    has_row = False
    sort_fields = frozenset()
    rows_class = None
    row_class = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.model is None or cls.publication is None:
            return

        cls.has_bulk = bool(actions_for(cls.actions, 'bulk'))
        cls.has_row = bool(actions_for(cls.actions, 'row'))
        cls.sort_fields = frozenset(
            c.sort_field for c in cls.columns if c.sort_field
        )

        model_name = cls.model._meta.model_name
        model_object_name = cls.model._meta.object_name   # e.g. 'Product'
        tmpl_name = f'{model_name}-row'

        # The per-model row renderer, registered as a model_template so the
        # push/poll layer can re-render a single row.
        row_cls = type(f'{model_object_name}Row', (ReactiveRow,), dict(
            __module__=cls.__module__,
            columns=cls.columns,
            router=cls,
            show_select=cls.has_bulk,
            show_kebab=cls.has_row,
        ))
        model_template(tmpl_name)(row_cls)

        # The subscribed <tbody>: per-model facets/order/pagination live here,
        # read off the class by the subscription machinery.
        rows_attrs = dict(
            __module__=cls.__module__,
            publication=cls.publication,
            model_template=tmpl_name,
            facets=cls.facets,
        )
        if cls.order:
            rows_attrs['order'] = cls.order
        if cls.paginate_by:
            rows_attrs['paginate_by'] = cls.paginate_by
        rows_cls = type(f'{model_object_name}Rows', (ReactiveRows,), rows_attrs)

        # The live detail card. Its registration is reconstructed (in the worker
        # / poll process) as ``content_class(obj, user=…)``, so the router is
        # bound here as a class attribute rather than passed at call time.
        detail_cls = type(f'{model_object_name}Detail', (ReactiveDetail,), dict(
            __module__=cls.__module__,
            router=cls,
        ))

        # Inject all three as importable attributes of the router's own module:
        # a Subscription/Registration is reconstructed in another process from a
        # stored module+class name, so these classes must resolve there.
        mod = sys.modules[cls.__module__]
        setattr(mod, row_cls.__name__, row_cls)
        setattr(mod, rows_cls.__name__, rows_cls)
        setattr(mod, detail_cls.__name__, detail_cls)
        cls.row_class = row_cls
        cls.rows_class = rows_cls
        cls.detail_class = detail_cls

    # --- config helpers -----------------------------------------------------

    @classmethod
    def get_namespace(cls):
        return cls.namespace or cls.model._meta.model_name

    @classmethod
    def reverse_url(cls, name, *args):
        return reverse(f'{cls.get_namespace()}:{name}', args=args)

    @classmethod
    def get_title(cls):
        return cls.site_title or str(cls.model._meta.verbose_name_plural).capitalize()

    @classmethod
    def get_heading(cls):
        return cls.list_heading or str(cls.model._meta.verbose_name_plural).capitalize()

    @classmethod
    def get_detail_fields(cls):
        if cls.detail_fields is not None:
            return cls.detail_fields
        return [c.name for c in cls.columns if c.name]

    @classmethod
    def get_form_class(cls):
        return modelform_factory(cls.model, fields=cls.create_fields)

    @classmethod
    def get_nav_items(cls, request):
        return cls.nav_items

    # --- overridable rendering hooks ---------------------------------------

    @classmethod
    def list_extra(cls, request):
        """Components inserted between the heading and the create form (intro,
        banners, …). Default: nothing."""
        return []

    @classmethod
    def detail_cell(cls, obj, field):
        """Override to customise a detail field's value (return a component), or
        return None to use the default formatted value."""
        return None

    # --- page assembly ------------------------------------------------------

    @classmethod
    def render_list(cls, request, view):
        base = cls.reverse_url('list')
        body = [
            H1(cls.get_heading(), cls='mdc-typography--headline5',
               style='margin:0 0 .25em'),
            *cls.list_extra(request),
        ]
        if cls.create_fields:
            body.append(ReactiveCreateForm(
                cls.get_form_class()(), action=cls.reverse_url('create'),
                request=request,
                submit_label=f'Add {cls.model._meta.verbose_name}',
                style='margin:1em 0',
            ))
        if cls.facets:
            body.append(ReactiveFilter(cls, endpoint=base))
        if cls.has_bulk:
            body.append(ReactiveBulkBar(actions_for(cls.actions, 'bulk'),
                                        endpoint=base))
        body.append(ReactiveTable(cls))
        if cls.sort_fields:
            default = cls.order[0] if cls.order else ''
            body.append(ReactiveSort(endpoint=base, default_field=default))
        if cls.has_row:
            body.append(ReactiveRowActions(actions_for(cls.actions, 'row'),
                                           endpoint=base))
        if cls.paginate_by:
            body.append(ReactivePager(
                offset=0, per_page=cls.paginate_by,
                total=cls.model.objects.count(), endpoint=base,
            ))
        body.append(ReactiveToast())
        return Div(*body, style='max-width:1100px;margin:0 auto')

    # --- URLs ---------------------------------------------------------------

    @classmethod
    def get_urls(cls):
        router = cls
        model = cls.model
        publication = cls.publication

        class ListView(ReactiveMixin, View):
            def get(self, request):
                token = self.get_token()   # sets self.client (before render)
                doc = App(
                    router.render_list(request, self),
                    request=request,
                    title=router.get_title(),
                    nav_items=router.get_nav_items(request),
                    extra_head=[token, _ryzom_js()],
                )
                return HttpResponse(doc.to_html(view=self))

        class DetailView(ReactiveMixin, View):
            def get(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                token = self.get_token()
                doc = App(
                    Div(
                        MDCTextButton('← back', tag='a',
                                      href=router.reverse_url('list')),
                        router.detail_class(obj),
                        style='max-width:960px;margin:0 auto;padding:0 1em',
                    ),
                    request=request,
                    title=str(obj),
                    nav_items=router.get_nav_items(request),
                    extra_head=[token, _ryzom_js()],
                )
                return HttpResponse(doc.to_html(view=self))

        class CreateView(View):
            def post(self, request):
                form = router.get_form_class()(request.POST)
                if form.is_valid():
                    form.save()       # post_save -> insert push
                return HttpResponse(status=204)

        class FilterView(View):
            def post(self, request):
                client = Client.objects.filter(
                    token=request.POST.get('token', '')).last()
                if client is None:
                    return JsonResponse({'messages': []})
                sid = _sub_id(client, publication)
                if sid is None:
                    return JsonResponse({'messages': []})
                with transaction.atomic():
                    sub = Subscription.objects.select_for_update().get(pk=sid)
                    opts = dict(sub.options or {})
                    for facet in router.facets:
                        if isinstance(facet, SearchFacet):
                            opts[facet.key] = request.POST.get(facet.key, '')
                        elif isinstance(facet, BooleanFacet):
                            opts[facet.key] = request.POST.get(facet.key) == '1'
                    opts['offset'] = 0    # a new filter lands on page 1
                    messages = _deliver_window_change(sub, opts)
                return JsonResponse({'messages': messages})

        class SortView(View):
            def post(self, request):
                col = request.POST.get('col', '')
                if col not in router.sort_fields:
                    return JsonResponse({'messages': []})
                if request.POST.get('dir') == 'desc':
                    col = '-' + col
                client = Client.objects.filter(
                    token=request.POST.get('token', '')).last()
                if client is None:
                    return JsonResponse({'messages': []})
                sid = _sub_id(client, publication)
                if sid is None:
                    return JsonResponse({'messages': []})
                with transaction.atomic():
                    sub = Subscription.objects.select_for_update().get(pk=sid)
                    opts = dict(sub.options or {})
                    # Column + id tiebreak keeps a total order; land on page 1.
                    opts.update(order=[col, 'id'], offset=0)
                    messages = _deliver_window_change(sub, opts)
                return JsonResponse({'messages': messages})

        class PageView(View):
            def post(self, request):
                empty = {'offset': 0, 'per_page': 0, 'total': 0, 'label': '',
                         'no_prev': True, 'no_next': True, 'messages': []}
                client = Client.objects.filter(
                    token=request.POST.get('token', '')).last()
                if client is None:
                    return JsonResponse(empty)
                sid = _sub_id(client, publication)
                if sid is None:
                    return JsonResponse(empty)
                action = request.POST.get('action', '')
                with transaction.atomic():
                    sub = Subscription.objects.select_for_update().get(pk=sid)
                    opts = dict(sub.options or {})
                    cur_offset = int(opts.get('offset') or 0)
                    try:
                        per_page = max(1, int(request.POST.get('per_page')))
                    except (TypeError, ValueError):
                        per_page = int(opts.get('per_page') or router.paginate_by)
                    if action == 'first' or action == 'per_page':
                        offset = 0
                    elif action == 'prev':
                        offset = max(0, cur_offset - per_page)
                    elif action == 'next':
                        offset = cur_offset + per_page
                    elif action == 'last':
                        offset = 10 ** 15        # clamped by get_queryset
                    else:
                        offset = cur_offset
                    opts.update(offset=offset, per_page=per_page)
                    messages = _deliver_window_change(sub, opts)
                    offset = sub.options['offset']
                    per_page = sub.options['per_page']
                    total = sub.options['total']
                start = offset + 1 if total else 0
                end = min(offset + per_page, total)
                return JsonResponse({
                    'offset': offset, 'per_page': per_page, 'total': total,
                    'label': f'{start}-{end} / {total}',
                    'no_prev': offset <= 0,
                    'no_next': offset + per_page >= total,
                    'messages': messages,
                })

        class BulkView(View):
            def post(self, request):
                actions = {a.slug: a for a in router.actions}
                act = actions.get(request.POST.get('action', ''))
                if act is None:
                    return JsonResponse({'count': 0})
                client = Client.objects.filter(
                    token=request.POST.get('token', '')).last()
                if client is None:
                    return JsonResponse({'count': 0})
                sub = (
                    Subscription.objects
                    .filter(client=client, publication__name=publication)
                    .last()
                )
                if sub is None:
                    return JsonResponse({'count': 0})
                ids = [i for i in request.POST.get('ids', '').split(',') if i]
                scope_all = request.POST.get('scope') == 'all'
                # A row-only action must never be mass-applied.
                if 'bulk' not in act.scopes and (scope_all or len(ids) != 1):
                    return JsonResponse({'count': 0})
                visible = sub.row_queryset()
                queryset = visible if scope_all else visible.filter(pk__in=ids)
                count = queryset.count()
                act.fn(queryset, request)   # per-object save/delete -> push
                return JsonResponse({'count': count})

        for view_cls in [ListView, DetailView, CreateView, FilterView,
                          SortView, PageView, BulkView]:
            view_cls.model = model

        # Expose the generated view classes (e.g. for tests or custom wiring).
        cls.views = dict(
            list=ListView, detail=DetailView, create=CreateView,
            filter=FilterView, sort=SortView, page=PageView, bulk=BulkView,
        )

        patterns = [
            path('', ListView.as_view(), name='list'),
            path('create/', CreateView.as_view(), name='create'),
            path('filter/', FilterView.as_view(), name='filter'),
            path('sort/', SortView.as_view(), name='sort'),
            path('page/', PageView.as_view(), name='page'),
            path('bulk/', BulkView.as_view(), name='bulk'),
            path('poll/', ddp_poll, name='poll'),   # client-pull (POLLING.md)
            path('<int:pk>/', DetailView.as_view(), name='detail'),
            *cls.extra_urls(),
        ]
        return patterns, cls.get_namespace()

    @classmethod
    def extra_urls(cls):
        """Hook for custom member/collection endpoints (e.g. a ``sell/`` route).
        Default: none."""
        return []
