"""End-to-end check of the demo's per-user visibility (LOGIN.md scenario).

Runs the ``seed_demo`` management command, then asserts the seeded data + the
GroupFacet produce exactly the visibility matrix the demo promises: staff and a
both-groups user see everything, a single-group user sees their group + public,
an anonymous visitor sees only public — and a change to a grouped product is
routed only to the subscriptions entitled to see it.
"""
import pytest
from django.conf import settings

skip_reactive = pytest.mark.skipif(
    not settings.CHANNELS_ENABLE, reason='Reactive disabled')

PUBLIC = {'Public Widget', 'Public Bolt', 'Public Hinge'}
SALES = {'Sales Cog', 'Sales Gear', 'Sales Lever', 'Sales Pulley'}
OPS = {'Ops Gadget', 'Ops Sprocket', 'Ops Valve', 'Ops Flange'}


def _visible_to(username):
    """Product names a given user (None = anonymous) sees, via the real facet
    pipeline ProductRows.get_queryset uses for the forward render."""
    from django.contrib.auth.models import User

    from ryzom_example_crud.components import ProductRows
    from ryzom_example_crud.models import Product

    user = User.objects.get(username=username) if username else None
    qs = ProductRows.get_queryset(user, Product.objects.all(), {})
    return set(qs.values_list('name', flat=True))


@skip_reactive
@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    from django.contrib.auth.models import User
    from django.core.management import call_command

    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    call_command('seed_demo')  # second run must not duplicate

    assert Product.objects.count() == len(PUBLIC | SALES | OPS)
    assert set(User.objects.values_list('username', flat=True)) >= {
        'alice', 'bob', 'carol', 'boss'}


@skip_reactive
@pytest.mark.django_db
def test_visibility_matrix_matches_the_demo():
    from django.core.management import call_command
    call_command('seed_demo')

    assert _visible_to(None) == PUBLIC                  # anonymous: public only
    assert _visible_to('alice') == PUBLIC | SALES       # one group + public
    assert _visible_to('bob') == PUBLIC | OPS
    assert _visible_to('carol') == PUBLIC | SALES | OPS  # both groups
    assert _visible_to('boss') == PUBLIC | SALES | OPS   # staff: all


@skip_reactive
@pytest.mark.django_db
def test_change_to_grouped_product_routes_to_entitled_subscriptions_only():
    from django.contrib.auth.models import User
    from django.core.management import call_command

    from ryzom_django_channels.models import Client, Publication, Subscription
    from ryzom_django_channels.signals import _candidate_ids, _snapshot
    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    pub = Publication.objects.create(
        name='products',
        model_module='ryzom_example_crud.models',
        model_class='Product',
    )

    def subscribe(username):
        user = User.objects.get(username=username) if username else None
        client = Client.objects.create(user=user)
        return Subscription.objects.create(
            client=client, publication=pub, subscriber_id='x',
            subscriber_module='ryzom_example_crud.components',
            subscriber_class='ProductRows', options={},
        )

    subs = {name: subscribe(name)
            for name in ('alice', 'bob', 'carol', 'boss')}
    subs[None] = subscribe(None)

    # A sale on a sales-group product: route to sales members + staff only.
    sales_product = Product.objects.get(name='Sales Cog')
    ids = _candidate_ids(
        'ryzom_example_crud.models', 'Product', None, _snapshot(sales_product))

    assert subs['alice'].id in ids
    assert subs['carol'].id in ids
    assert subs['boss'].id in ids
    assert subs['bob'].id not in ids     # ops only -> not entitled
    assert subs[None].id not in ids      # anonymous -> public only


@skip_reactive
@pytest.mark.django_db
def test_list_page_renders_selection_ui():
    """The live list ships the row checkboxes, the select-all header box, a
    bulk toolbar offering every bulk action, and the per-row ⋮ menu + its
    interactive dialogs (delete confirm, rename input)."""
    from django.core.management import call_command
    from django.test import RequestFactory

    from ryzom_example_crud.actions import actions_for
    from ryzom_example_crud.views import ProductListView

    from django.contrib.auth.models import AnonymousUser

    from ryzom_django_channels.models import Publication

    call_command('seed_demo')
    Publication.objects.get_or_create(
        name='products', defaults=dict(
            model_module='ryzom_example_crud.models', model_class='Product'))
    req = RequestFactory().get('/crud/products/')
    req.user = AnonymousUser()
    resp = ProductListView.as_view()(req)
    html = resp.content.decode()

    assert 'row-select' in html                   # per-row checkbox (MDC native-control class)
    assert 'select-all-page' in html              # header select-all
    assert '<product-bulk' in html                # toolbar element
    for a in actions_for('bulk'):                 # one MDC select option per bulk action
        assert f'data-value="{a.slug}"' in html   # the option element
        assert f'>{a.label}<' in html             # carrying its label

    # Per-row ⋮ kebab menu + its host element.
    assert 'row-actions__toggle' in html
    assert '<product-row-actions' in html
    assert 'data-action="rename"' in html         # rename is a row menu item

    # Interactive dialogs are pre-rendered (hidden) for confirm/input actions.
    assert 'data-action-slug="delete"' in html    # delete confirm dialog
    assert 'Permanently delete' in html           # its confirm message
    assert 'data-action-slug="rename"' in html    # rename input dialog
    assert 'New name' in html                     # its input field label


def _bulk_post(token, **data):
    """Drive ProductBulkView with a POST, as the client element does."""
    from django.test import RequestFactory

    from ryzom_example_crud.views import ProductBulkView

    req = RequestFactory().post('/crud/products/bulk/', dict(token=token, **data))
    return ProductBulkView.as_view()(req)


@skip_reactive
@pytest.mark.django_db
def test_bulk_scope_all_only_touches_visible_rows():
    """`scope=all` deletes exactly the caller's visible set — not others' rows."""
    from django.contrib.auth.models import User
    from django.core.management import call_command

    from ryzom_django_channels.models import Client, Publication, Subscription
    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    pub = Publication.objects.create(
        name='products', model_module='ryzom_example_crud.models',
        model_class='Product')

    alice = Client.objects.create(user=User.objects.get(username='alice'))
    Subscription.objects.create(
        client=alice, publication=pub, subscriber_id='x',
        subscriber_module='ryzom_example_crud.components',
        subscriber_class='ProductRows', options={})

    # alice sees public + sales; ops rows are invisible to her.
    _bulk_post(alice.token, action='delete', scope='all')

    remaining = set(Product.objects.values_list('name', flat=True))
    assert remaining == OPS                    # only the rows alice couldn't see


@skip_reactive
@pytest.mark.django_db
def test_bulk_explicit_ids_are_clamped_to_visible_rows():
    """Explicit ids a client can't see are ignored (can't act on hidden rows)."""
    from django.contrib.auth.models import User
    from django.core.management import call_command

    from ryzom_django_channels.models import Client, Publication, Subscription
    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    pub = Publication.objects.create(
        name='products', model_module='ryzom_example_crud.models',
        model_class='Product')

    bob = Client.objects.create(user=User.objects.get(username='bob'))
    Subscription.objects.create(
        client=bob, publication=pub, subscriber_id='x',
        subscriber_module='ryzom_example_crud.components',
        subscriber_class='ProductRows', options={})

    sales = Product.objects.get(name='Sales Cog')   # invisible to bob (ops only)
    public = Product.objects.get(name='Public Widget')
    resp = _bulk_post(bob.token, action='delete',
                      ids=f'{sales.id},{public.id}')

    import json
    assert json.loads(resp.content)['count'] == 1   # only the public row counted
    assert Product.objects.filter(pk=sales.id).exists()      # hidden row untouched
    assert not Product.objects.filter(pk=public.id).exists()  # visible row deleted


def _boss_client():
    """A staff client + products subscription (boss sees every row)."""
    from django.contrib.auth.models import User

    from ryzom_django_channels.models import Client, Publication, Subscription

    pub, _ = Publication.objects.get_or_create(
        name='products', defaults=dict(
            model_module='ryzom_example_crud.models', model_class='Product'))
    client = Client.objects.create(user=User.objects.get(username='boss'))
    Subscription.objects.create(
        client=client, publication=pub, subscriber_id='x',
        subscriber_module='ryzom_example_crud.components',
        subscriber_class='ProductRows', options={})
    return client


@skip_reactive
@pytest.mark.django_db
def test_rename_action_renames_a_single_product():
    """The per-row rename action applies the dialog's `name` to that one row."""
    from django.core.management import call_command

    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    client = _boss_client()
    widget = Product.objects.get(name='Public Widget')

    resp = _bulk_post(client.token, action='rename',
                      ids=str(widget.id), name='Renamed Widget')

    import json
    assert json.loads(resp.content)['count'] == 1
    widget.refresh_from_db()
    assert widget.name == 'Renamed Widget'


@skip_reactive
@pytest.mark.django_db
def test_rename_is_rejected_for_multiple_ids():
    """A row-only action can't be mass-applied: many ids => no-op."""
    from django.core.management import call_command

    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    client = _boss_client()
    a = Product.objects.get(name='Public Widget')
    b = Product.objects.get(name='Public Bolt')

    resp = _bulk_post(client.token, action='rename',
                      ids=f'{a.id},{b.id}', name='Nope')

    import json
    assert json.loads(resp.content)['count'] == 0
    a.refresh_from_db(); b.refresh_from_db()
    assert a.name == 'Public Widget'    # untouched
    assert b.name == 'Public Bolt'


@skip_reactive
@pytest.mark.django_db
def test_rename_is_rejected_for_scope_all():
    """A row-only action refuses 'select all matching'."""
    from django.core.management import call_command

    from ryzom_example_crud.models import Product

    call_command('seed_demo')
    client = _boss_client()
    before = set(Product.objects.values_list('name', flat=True))

    resp = _bulk_post(client.token, action='rename', scope='all', name='Nope')

    import json
    assert json.loads(resp.content)['count'] == 0
    assert set(Product.objects.values_list('name', flat=True)) == before
