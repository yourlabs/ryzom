"""
Reactive components for the Product demo.

The layout model: a subscribed <tbody> renders one ProductRow per object and is
kept in sync by the channels DDP push (insert/change/remove). The detail view is
a registered ReactiveComponent that the server re-renders on every change.

Mutations (create / sell) are issued with fetch() from small custom elements so
the page never reloads — the table and detail update purely from the server
push, which is the whole point of the demo.
"""
from ryzom_django_channels.components import (
    ReactiveComponentMixin,
    SubscribeComponentMixin,
    model_template,
)
from ryzom_django_mdc.html import *


# --- one row, the unit the server pushes -----------------------------------

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

    @classmethod
    def get_queryset(cls, user, qs, opts):
        # opts is stored on the Subscription and re-applied on every push, so
        # the live diff is filter-aware: a product edited to match/unmatch this
        # filter is inserted/removed live, not just on the next page load.
        opts = opts or {}
        q = (opts.get('q') or '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if opts.get('in_stock'):
            qs = qs.filter(stock_qty__gt=0)
        return qs.order_by('name')


class ProductTable(MDCDataTableResponsive):
    def __init__(self, **attrs):
        super().__init__(
            thead=MDCDataTableThead(tr=MDCDataTableHeaderTr(
                MDCDataTableTh('Name'),
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
            await fetch('/crud/products/filter/', {
                method: 'POST',
                headers: {'X-CSRFTOKEN': csrf.value},
                body: body,
            })
            this.inflight = False
            if this.again:
                this.again = False
                this.apply()
