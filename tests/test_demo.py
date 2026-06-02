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
