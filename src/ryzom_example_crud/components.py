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


# --- one row, the unit the server pushes -----------------------------------

def group_badge(obj):
    """A small chip naming the row's visibility group (or 'public').

    Makes per-user visibility legible: with the badge you can see *why* a row is
    or isn't in a given user's list (GroupFacet, see LOGIN.md). Public rows are
    grey; grouped rows are coloured."""
    name = obj.group.name if obj.group_id else 'public'
    colour = '#1565c0' if obj.group_id else '#888'
    return Span(
        name,
        style=(f'background:{colour};color:#fff;border-radius:10px;'
               'padding:1px 9px;font-size:11px'),
    )


@model_template('product-row')
class ProductRow(MDCDataTableTr):
    def __init__(self, obj):
        self.obj = obj
        low = obj.stock_qty <= 5
        super().__init__(
            MDCDataTableTd(
                A(obj.name, href=f'/crud/products/{obj.id}/'),
                data_label='Name',
            ),
            MDCDataTableTd(group_badge(obj), data_label='Group'),
            MDCDataTableTd(f'${obj.price}', data_label='Price'),
            MDCDataTableTd(
                str(obj.stock_qty),
                Span(' low', style='color:#c00;font-size:11px;font-weight:600')
                if low else None,
                data_label='Stock',
            ),
            MDCDataTableTd(
                SellButton(product_id=obj.id) if obj.stock_qty > 0
                else Span('out', style='opacity:.5'),
                data_label='',
                style='text-align:right',
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
                MDCDataTableTh('Name'),
                MDCDataTableTh('Group'),
                MDCDataTableTh('Price'),
                MDCDataTableTh('Stock'),
                MDCDataTableTh(''),
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
            H2(product.name, style='margin:0 0 .5em'),
            Div('Price: ', Strong(f'${product.price}')),
            Div(
                'In stock: ',
                Strong(str(product.stock_qty),
                       style='color:#c00' if low else 'color:inherit'),
            ),
            Div('updates live ✓', style='color:#888;font-size:12px;margin-top:1em'),
            style=('padding:1.25em;border:1px solid #ddd;border-radius:8px;'
                   'max-width:360px'),
        )


# --- fetch-based mutate widgets (no page reload) ----------------------------

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
                Label(
                    'Group ',
                    Select(
                        Option('public', value=''),
                        *[Option(g.name, value=str(g.id))
                          for g in Group.objects.all()],
                        name='group',
                    ),
                    style='display:flex;align-items:center;gap:4px',
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
                Input(type='checkbox', name='in_stock'),
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

    def __init__(self, offset=0, per_page=5, total=0, **attrs):
        start = offset + 1 if total else 0
        end = min(offset + per_page, total)
        no_prev = offset <= 0
        no_next = offset + per_page >= total

        def btn(label, action, disabled):
            kw = dict(disabled=True) if disabled else {}
            return Button(label, tag='button', type='button',
                          data_action=action,
                          style='margin:0 2px;cursor:pointer', **kw)

        super().__init__(
            Span(f'{start}-{end} / {total}', cls='pager-status',
                 style='margin-right:1em;min-width:7em;display:inline-block'),
            btn('« first', 'first', no_prev),
            btn('‹ prev', 'prev', no_prev),
            btn('next ›', 'next', no_next),
            btn('last »', 'last', no_next),
            Label(
                ' Rows: ',
                Select(
                    *[Option(str(i), value=str(i), selected=(i == per_page))
                      for i in (3, 5, 10, 25)],
                    name='per_page',
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
            this.select = this.querySelector('select[name="per_page"]')
            this.inflight = False
            this.querySelector('button[data-action="first"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="prev"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="next"]').addEventListener(
                'click', this.nav.bind(this))
            this.querySelector('button[data-action="last"]').addEventListener(
                'click', this.nav.bind(this))
            this.select.addEventListener('change', this.changePer.bind(this))

        async def nav(self, event):
            await this.apply(event.currentTarget.dataset.action, this.select.value)

        async def changePer(self, event):
            # Changing the page size resets to the first page (server-side).
            await this.apply('per_page', this.select.value)

        async def apply(self, action, per_page):
            # One request in flight: the server does a read-modify-write of the
            # subscription's offset, so overlapping requests would race it.
            if this.inflight:
                return
            this.inflight = True
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

        def setDisabled(self, action, disabled):
            this.querySelector(
                'button[data-action="' + action + '"]').disabled = disabled
