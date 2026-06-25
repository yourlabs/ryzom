"""
The reactive Product demo, expressed with the generic ``ReactiveRouter``.

What used to be ~1200 lines of hand-written reactive components is now a single
declarative ``ProductCrud`` (the generic machinery lives in
``ryzom_django_mdc.reactive``). Only the genuinely Product-specific bits stay
here: the custom cell renderers (group badge, low-stock chip, inline Sell
button), the action handlers, the sell endpoint, and the identity banner.

``ReactiveRouter.__init_subclass__`` generates the importable ``ProductRow`` /
``ProductRows`` classes (named after the model) into this module and registers
the ``product-row`` template, so the channels push/poll layer reconstructs them
exactly as before.
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.views import View

from ryzom_django_channels.facets import BooleanFacet, GroupFacet, SearchFacet
from ryzom_django_mdc.html import *
from ryzom_django_mdc.reactive import (
    Action,
    Column,
    Field,
    ReactiveRouter,
)

from ryzom_example_crud.models import Product

_NAV = [
    {'label': 'Home', 'url': '/home/'},
    {'label': 'Users', 'url': '/crud/users/'},
    {'label': 'Products (live)', 'url': '/crud/products/'},
]


# --- Product-specific cell renderers ---------------------------------------

def group_badge(obj):
    """A small chip naming the row's visibility group (or 'public').

    Makes per-user visibility legible (GroupFacet, see LOGIN.md): public rows
    are grey, grouped rows coloured."""
    name = obj.group.name if obj.group_id else 'public'
    colour = ('var(--mdc-theme-primary, #1565c0)' if obj.group_id
              else 'var(--mdc-theme-text-secondary-on-background, #888)')
    return MDCChip(
        name,
        style=(f'background:{colour};color:#fff;border-radius:12px;'
               'padding:0 10px;height:22px;font-size:11px;'
               'display:inline-flex;align-items:center'),
    )


def price_cell(obj):
    return f'${obj.price}'


def stock_cell(obj):
    low = obj.stock_qty <= 5
    return Span(
        str(obj.stock_qty),
        MDCChip('low', style=(
            'margin-left:6px;background:var(--mdc-theme-error, #b00020);'
            'color:#fff;border-radius:10px;padding:0 8px;height:20px;'
            'font-size:10px;font-weight:600;display:inline-flex;'
            'align-items:center')) if low else None,
    )


def sell_or_out(obj):
    if obj.stock_qty > 0:
        return SellButton(product_id=obj.id)
    return MDCChip('out', style=(
        'opacity:.5;border-radius:10px;padding:0 8px;height:20px;'
        'font-size:11px;display:inline-flex;align-items:center'))


def _identity_banner(request):
    """Show which user this page (hence this subscription) is scoped to."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        groups = ', '.join(g.name for g in user.groups.all()) or 'none'
        suffix = ' — staff, sees all' if user.is_staff else ''
        text = f'Logged in as {user.username} — groups: {groups}{suffix}'
        icon = 'account_circle'
    else:
        text = 'Not logged in — showing public products only.'
        icon = 'info'
    return MDCBanner(text, icon=icon, style='margin:0 0 1em')


# --- inline mutate widget + sell endpoint (no reload) ----------------------

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


class ProductSellView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.stock_qty > 0:
            product.stock_qty -= 1
            product.save()  # post_save -> DDP push to the table + detail
        return HttpResponse(status=204)


# --- pluggable action handlers ---------------------------------------------

def _delete(queryset, request):
    # Per-object delete so each fires post_delete -> a DDP remove on every list.
    for obj in queryset:
        obj.delete()


def _rename(queryset, request):
    # Row-only: the dialog ships a single new name; apply it to the one row.
    name = (request.POST.get('name') or '').strip()
    if not name:
        return
    for obj in queryset:
        obj.name = name
        obj.save()  # post_save -> DDP change push


def _restock(queryset, request):
    for obj in queryset:
        obj.stock_qty += 10
        obj.save()


def _out_of_stock(queryset, request):
    for obj in queryset:
        obj.stock_qty = 0
        obj.save()


# --- the router: everything above wired into one declarative CRUD ----------

class ProductCrud(ReactiveRouter):
    model = Product
    publication = 'products'
    namespace = 'product'

    order = ('name', 'id')
    paginate_by = 5
    site_title = 'Products (live)'
    list_heading = 'Products — live'
    nav_items = _NAV

    # Express the filter once as facets: applied forward to window the list and
    # reused in reverse by the signal handler to route a change.
    facets = [
        SearchFacet('q', 'name'),
        BooleanFacet('in_stock', 'stock_qty'),  # "on" => stock_qty > 0
        GroupFacet('group'),                     # per-user visibility
    ]
    filter_labels = {'q': 'Search name', 'in_stock': 'in stock only'}

    columns = [
        Column('name', link_detail=True),
        Column('group', label='Group', cell=group_badge, sortable='group_id'),
        Column('price', cell=price_cell),
        Column('stock_qty', label='Stock', cell=stock_cell),
        Column('', label='', cell=sell_or_out, sortable=False,
               td_style='text-align:right'),
    ]

    create_fields = ['name', 'price', 'stock_qty', 'group']
    detail_fields = ['price', 'stock_qty']

    actions = [
        Action('delete', 'Delete', _delete, scopes=('bulk', 'row'),
               confirm='Permanently delete the selected product(s)? '
                       'This cannot be undone.'),
        Action('rename', 'Rename', _rename, scopes=('row',),
               fields=(Field('name', 'New name', required=True),)),
        Action('restock', 'Restock (+10)', _restock, scopes=('bulk', 'row')),
        Action('out_of_stock', 'Mark out of stock', _out_of_stock,
               scopes=('bulk',)),
    ]

    @classmethod
    def list_extra(cls, request):
        return [
            P('Add or sell below: the table updates over a websocket, no '
              'reload. Open this page in two tabs to see it.',
              cls='mdc-typography--body2'),
            _identity_banner(request),
        ]

    @classmethod
    def extra_urls(cls):
        return [
            path('<int:pk>/sell/', ProductSellView.as_view(), name='sell'),
        ]
