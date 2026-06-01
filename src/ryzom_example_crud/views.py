"""
Reactive Product demo views.

The list and detail pages are rendered server-side (with the initial queryset)
and then kept live over the channels websocket. ReactiveMixin.get_token() mints
a Client and emits the <meta name="ryzom-config"> the client JS reads to open
the socket; ryzom.js (the DDP client) is injected into <head> via extra_head.

Mutations are plain endpoints returning 204 — the visible update is the server
push, not the HTTP response.
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.views import View

from ryzom_django_channels.views import ReactiveMixin
from ryzom_django_mdc.crudlfap import App
from ryzom_django_mdc.html import *

from ryzom_example_crud.components import (
    ProductCreateForm,
    ProductDetail,
    ProductFilter,
    ProductTable,
)
from ryzom_example_crud.models import Product

_NAV = [
    {'label': 'Users', 'url': '/crud/users/'},
    {'label': 'Products (live)', 'url': '/crud/products/'},
]


def _ryzom_js():
    # The DDP websocket client, injected into <head> via extra_head per-render.
    # Built inside the view (not at module level) so the bundle component
    # scanner doesn't pick up a stray Script instance.
    return Script(src='/static/ryzom.js')


class ProductListView(ReactiveMixin, View):
    def get(self, request):
        token = self.get_token()  # sets self.client, returns the config <meta>
        doc = App(
            H1('Products — live', style='margin:0 0 .25em'),
            P('Add or sell below: the table updates over a websocket, no reload. '
              'Open this page in two tabs to see it.'),
            ProductCreateForm(request, style='margin:1em 0'),
            ProductFilter(),
            ProductTable(),
            request=request,
            title='Products (live)',
            nav_items=_NAV,
            extra_head=[token, _ryzom_js()],
        )
        return HttpResponse(doc.to_html(view=self))


class ProductDetailView(ReactiveMixin, View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        token = self.get_token()
        doc = App(
            A('← all products', href='/crud/products/'),
            ProductDetail(product),
            request=request,
            title=str(product),
            nav_items=_NAV,
            extra_head=[token, _ryzom_js()],
        )
        return HttpResponse(doc.to_html(view=self))


class ProductCreateView(View):
    def post(self, request):
        name = (request.POST.get('name') or '').strip()
        if name:
            Product.objects.create(
                name=name,
                price=request.POST.get('price') or 0,
                stock_qty=request.POST.get('stock_qty') or 0,
            )
        return HttpResponse(status=204)


class ProductSellView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.stock_qty > 0:
            product.stock_qty -= 1
            product.save()  # post_save -> DDP push to the table + detail
        return HttpResponse(status=204)


class ProductFilterView(View):
    """Re-filter a client's live table without a reload.

    Updates the client's products Subscription options, recomputes the
    queryset, and pushes the membership delta (insert/remove) over the same
    DDP channel the publication signals use.
    """
    def post(self, request):
        from ryzom_django_channels.components import model_templates
        from ryzom_django_channels.ddp import send_insert, send_remove
        from ryzom_django_channels.models import Client, Subscription

        client = Client.objects.filter(token=request.POST.get('token', '')).last()
        if client is None:
            return HttpResponse(status=204)
        sub = Subscription.objects.filter(
            client=client, publication__name='products',
        ).last()
        if sub is None:
            return HttpResponse(status=204)

        opts = {
            'q': request.POST.get('q', ''),
            'in_stock': request.POST.get('in_stock') == '1',
        }
        old = set(sub.queryset)
        new_qs = sub.get_queryset(opts)   # updates stored opts + qs, returns qs
        new = set(sub.queryset)

        tmpl = model_templates[sub.subscriber.model_template]
        for pk in old - new:
            send_remove(sub, tmpl, Product(id=pk))
        for pk in new - old:
            send_insert(sub, tmpl, new_qs.get(pk=pk))
        return HttpResponse(status=204)


urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('create/', ProductCreateView.as_view(), name='create'),
    path('filter/', ProductFilterView.as_view(), name='filter'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/sell/', ProductSellView.as_view(), name='sell'),
]
