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

from ryzom_django_channels.views import ReactiveMixin, ddp_poll
from ryzom_django_mdc.crudlfap import App
from ryzom_django_mdc.html import *

from ryzom_example_crud.actions import ACTIONS, actions_for
from ryzom_example_crud.components import (
    ProductBulkBar,
    ProductCreateForm,
    ProductDetail,
    ProductFilter,
    ProductPager,
    ProductRowActions,
    ProductRows,
    ProductTable,
)
from ryzom_example_crud.models import Product

_NAV = [
    {'label': 'Home', 'url': '/home/'},
    {'label': 'Users', 'url': '/crud/users/'},
    {'label': 'Products (live)', 'url': '/crud/products/'},
]


def _ryzom_js():
    # The DDP websocket client, injected into <head> via extra_head per-render.
    # Built inside the view (not at module level) so the bundle component
    # scanner doesn't pick up a stray Script instance.
    return Script(src='/static/ryzom.js')


def _push_window_replace(sub, old_window, new_rows):
    """Push the row delta between two windows over the websocket.

    Shared by the filter and pager views: both do a read-modify-write of the
    subscription's window and then need to bring the DOM in line. Removes go
    first, then inserts in ascending window position so each insert(position)
    lands at the right child index. Removed rows usually still exist (they
    moved to another page / were filtered out), so we send the live instance.
    """
    from ryzom_django_channels.components import model_templates
    from ryzom_django_channels.ddp import send_insert, send_remove

    tmpl = model_templates[sub.subscriber.model_template]
    new_window = [obj.id for obj in new_rows]
    rows = {obj.pk: obj for obj in new_rows}
    old_set, new_set = set(old_window), set(new_window)

    for pk in old_set - new_set:
        obj = Product.objects.filter(pk=pk).first() or Product(pk=pk)
        send_remove(sub, tmpl, obj)
    for pk in sorted(new_set - old_set, key=new_window.index):
        send_insert(sub, tmpl, rows[pk])


def _deliver_window_change(sub, opts):
    """Apply a filter/pager change to one subscription, per its transport.

    Returns the DDP messages the *originating* client should apply now (empty
    for a push client, whose delta goes over the channel layer instead).

    A **push** client has a live channel: deliver the row delta now over the
    channel layer, advancing the stored window (`qs`) with it — the original
    behaviour; nothing comes back in the HTTP response.

    A **poll** client has no channel (POLLING.md). The request is itself
    client-initiated, so we may answer it with the delta directly: record the
    new intent (`options`), then compute the window diff against the old `qs`
    via the same engine the poll loop uses — advancing `qs`/fingerprints and
    returning the insert/change/remove messages. The client applies them
    immediately (no wait for the next poll), and that next poll, now diffing the
    advanced `qs`, correctly returns nothing.

    Either way ``options`` ends with the clamped ``offset``/``per_page``/``total``
    the caller needs for its pager chrome response.
    """
    if sub.client and sub.client.channel:
        old_window = list(sub.queryset)
        new_rows = list(sub.get_queryset(opts))      # advances + persists qs
        _push_window_replace(sub, old_window, new_rows)
        return []

    from ryzom_django_channels.polling import subscription_delta

    sub.options = dict(opts)                          # new intent; qs untouched
    return subscription_delta(sub)                    # diff old qs vs new window


def _identity_banner(request):
    """Show which user this page (hence this subscription) is scoped to.

    Visibility is bound to the Client created at page load from request.user
    (see LOGIN.md), so this banner is the ground truth for *why* the list below
    shows what it shows: staff see all, a user sees their groups + public, an
    anonymous visitor sees only public rows."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        groups = ', '.join(g.name for g in user.groups.all()) or 'none'
        suffix = ' — staff, sees all' if user.is_staff else ''
        text = f'Logged in as {user.username} — groups: {groups}{suffix}'
        background = '#e8f0fe'
    else:
        text = 'Not logged in — showing public products only.'
        background = '#fdecea'
    return Div(text, style=(f'background:{background};padding:6px 12px;'
                            'border-radius:6px;margin:0 0 1em;font-size:14px'))


class ProductListView(ReactiveMixin, View):
    def get(self, request):
        token = self.get_token()  # sets self.client, returns the config <meta>
        doc = App(
            H1('Products — live', style='margin:0 0 .25em'),
            P('Add or sell below: the table updates over a websocket, no reload. '
              'Open this page in two tabs to see it.'),
            _identity_banner(request),
            ProductCreateForm(request, style='margin:1em 0'),
            ProductFilter(),
            ProductBulkBar(actions=actions_for('bulk')),
            ProductTable(),
            ProductRowActions(),  # per-row ⋮ menu dialogs + delegated wiring
            ProductPager(offset=0, per_page=ProductRows.paginate_by,
                         total=Product.objects.count()),
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
                # blank -> public; otherwise the chosen group's visibility
                group_id=request.POST.get('group') or None,
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
        from django.db import transaction
        from django.http import JsonResponse

        from ryzom_django_channels.models import Client, Subscription

        client = Client.objects.filter(token=request.POST.get('token', '')).last()
        if client is None:
            return JsonResponse({'messages': []})

        sub_id = (
            Subscription.objects
            .filter(client=client, publication__name='products')
            .values_list('id', flat=True)
            .last()
        )
        if sub_id is None:
            return JsonResponse({'messages': []})

        with transaction.atomic():
            # Lock only the subscription row for the whole read-modify-write so
            # a concurrent Product.save() push can't interleave with this
            # filter update and desync the stored id list from the DOM. We lock
            # by pk (no joins) to avoid FOR UPDATE on the nullable client join.
            sub = Subscription.objects.select_for_update().get(pk=sub_id)

            # Merge into the stored window opts and reset to the first page;
            # changing the filter changes the result set, so page 1 is the
            # sensible landing (preserves the chosen per_page).
            opts = dict(sub.options or {})
            opts.update(
                q=request.POST.get('q', ''),
                in_stock=request.POST.get('in_stock') == '1',
                offset=0,
            )

            messages = _deliver_window_change(sub, opts)
        return JsonResponse({'messages': messages})


class ProductPagerView(View):
    """Numbered-page navigation for the live table.

    Computes the new offset server-side from the pager action, updates the
    client's products subscription window, pushes the row delta over the same
    DDP channel the filter uses, and returns the new pager state as JSON so the
    pager element can refresh its indicator and button states.
    """
    def post(self, request):
        from django.db import transaction
        from django.http import JsonResponse

        from ryzom_django_channels.models import Client, Subscription

        empty = {'offset': 0, 'per_page': 0, 'total': 0,
                 'label': '', 'no_prev': True, 'no_next': True}

        client = Client.objects.filter(token=request.POST.get('token', '')).last()
        if client is None:
            return JsonResponse(empty)
        sub_id = (
            Subscription.objects
            .filter(client=client, publication__name='products')
            .values_list('id', flat=True)
            .last()
        )
        if sub_id is None:
            return JsonResponse(empty)

        action = request.POST.get('action', '')
        with transaction.atomic():
            sub = Subscription.objects.select_for_update().get(pk=sub_id)
            opts = dict(sub.options or {})
            cur_offset = int(opts.get('offset') or 0)
            try:
                per_page = max(1, int(request.POST.get('per_page')))
            except (TypeError, ValueError):
                per_page = int(opts.get('per_page') or ProductRows.paginate_by)

            if action == 'first' or action == 'per_page':
                offset = 0
            elif action == 'prev':
                offset = max(0, cur_offset - per_page)
            elif action == 'next':
                offset = cur_offset + per_page
            elif action == 'last':
                offset = 10 ** 15  # clamped to the last page by get_queryset
            else:
                offset = cur_offset
            opts.update(offset=offset, per_page=per_page)

            messages = _deliver_window_change(sub, opts)

            # Re-read the clamped offset/total the windowing settled on.
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
            'messages': messages,  # rows the originating poll client applies now
        })


class ProductBulkView(View):
    """Run a registered action over the selected rows.

    Generic endpoint for both surfaces: the bulk toolbar (ProductBulkBar) and
    the per-row ⋮ menu (ProductRowActions) POST here; the action is whatever the
    client picked from the registry (ryzom_example_crud.actions). Two scopes:

    - explicit ``ids`` — intersected with the subscription's *visible* queryset
      so a client can never act on rows it can't see (a per-row action sends the
      single row's pk here);
    - ``scope=all`` — every row matching the subscription's current filter, via
      ``Subscription.row_queryset`` (the unsliced, filtered, visibility-scoped
      queryset), so "select all matching" honours the live filter + GroupFacet
      visibility with no extra query logic.

    A row-only action (one without ``'bulk'`` in its scopes, e.g. rename) is
    refused unless it targets exactly one row, so it can't be mass-applied.

    Each handler mutates per object, firing the Publishable signals; the visible
    update is the resulting DDP push/poll, not this response (like SellButton).
    """
    def post(self, request):
        from django.http import JsonResponse

        from ryzom_django_channels.models import Client, Subscription

        action = request.POST.get('action', '')
        act = ACTIONS.get(action)
        if act is None:
            return JsonResponse({'count': 0})

        client = Client.objects.filter(token=request.POST.get('token', '')).last()
        if client is None:
            return JsonResponse({'count': 0})
        sub = (
            Subscription.objects
            .filter(client=client, publication__name='products')
            .last()
        )
        if sub is None:
            return JsonResponse({'count': 0})

        ids = [i for i in request.POST.get('ids', '').split(',') if i]
        scope_all = request.POST.get('scope') == 'all'

        # A row-only action (e.g. rename) must never be mass-applied: refuse
        # "select all matching" and anything but a single row.
        if 'bulk' not in act.scopes and (scope_all or len(ids) != 1):
            return JsonResponse({'count': 0})

        # The full filtered, visibility-scoped queryset this client can see.
        visible = sub.row_queryset()
        if scope_all:
            queryset = visible
        else:
            queryset = visible.filter(pk__in=ids)

        count = queryset.count()
        act.fn(queryset, request)  # per-object save()/delete() -> DDP push/poll
        return JsonResponse({'count': count})


urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('create/', ProductCreateView.as_view(), name='create'),
    path('filter/', ProductFilterView.as_view(), name='filter'),
    path('page/', ProductPagerView.as_view(), name='page'),
    path('bulk/', ProductBulkView.as_view(), name='bulk'),
    path('poll/', ddp_poll, name='poll'),  # client-pull transport (POLLING.md)
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/sell/', ProductSellView.as_view(), name='sell'),
]
