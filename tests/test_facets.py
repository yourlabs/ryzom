"""Facet reverse-matching unit tests (PROBLEM.md step 3 / MATCHING.md).

These are pure-Python (no DB) and pin the regression where a freshly created
instance holds raw form strings (e.g. stock_qty="5"), which BooleanFacet then
compared against an int.
"""
import pytest
from django.conf import settings

skip_reactive = pytest.mark.skipif(
    not settings.CHANNELS_ENABLE, reason='Reactive disabled')


@skip_reactive
def test_snapshot_coerces_form_strings():
    from ryzom_django_channels.signals import _snapshot
    from ryzom_example_crud.models import Product

    # ProductCreateView builds the instance from request.POST strings; the
    # snapshot used for reverse matching must coerce to the field's type.
    snap = _snapshot(Product(name='X', price='1.50', stock_qty='5'))
    assert snap['stock_qty'] == 5 and isinstance(snap['stock_qty'], int)


@skip_reactive
def test_boolean_facet_candidate_handles_string_instance():
    from ryzom_django_channels.facets import BooleanFacet
    from ryzom_django_channels.signals import _snapshot
    from ryzom_example_crud.models import Product

    facet = BooleanFacet('in_stock', 'stock_qty')  # "on" => stock_qty > 0
    # Regression: must not raise on a string-valued (uncoerced) instance.
    _a, q_in = facet.candidate(_snapshot(Product(stock_qty='5')))
    _a, q_out = facet.candidate(_snapshot(Product(stock_qty='0')))
    # in range => no constraint (every sub admits it); out of range => only
    # subs that did not switch the flag on.
    assert not q_in.children
    assert q_out.children


@skip_reactive
def test_search_facet_candidate_builds_reverse_predicate():
    from ryzom_django_channels.facets import SearchFacet

    ann, q = SearchFacet('q', 'name').candidate({'name': 'Widget'})
    assert '_match_q' in ann
    assert ('_match_q__gt', 0) in q.children


# --- GroupFacet: per-user object visibility (filter AND can_see) ------------

@skip_reactive
def test_group_facet_public_row_admits_every_subscription():
    from ryzom_django_channels.facets import GroupFacet

    # A public row (group is NULL) is visible to everyone -> no constraint.
    _ann, q = GroupFacet('group').candidate({'group_id': None})
    assert not q.children


@skip_reactive
def test_group_facet_private_row_routes_to_staff_or_members():
    from ryzom_django_channels.facets import GroupFacet

    # A private row only reaches staff subscriptions or subscriptions whose
    # user belongs to the row's group: staff OR member, over client__user.
    _ann, q = GroupFacet('group').candidate({'group_id': 7})
    assert q.connector == 'OR'
    assert ('client__user__is_staff', True) in q.children
    assert ('client__user__groups', 7) in q.children


@skip_reactive
def test_snapshot_carries_group_fk():
    from ryzom_django_channels.signals import _snapshot
    from ryzom_example_crud.models import Product

    # The visibility key must land in the reverse-matching snapshot as the
    # concrete FK column, so a regroup routes via both old and new group.
    snap = _snapshot(Product(name='X', group_id=7))
    assert snap['group_id'] == 7


@skip_reactive
@pytest.mark.django_db
def test_group_facet_routes_change_to_only_visible_subscriptions():
    """End-to-end reverse routing: a change to a product in group G must be
    routed (via the real Subscription-table query) to staff + members of G
    only, never to other-group members or anonymous clients."""
    from django.contrib.auth.models import Group, User

    from ryzom_django_channels.models import Client, Publication, Subscription
    from ryzom_django_channels.signals import _candidate_ids, _snapshot
    from ryzom_example_crud.models import Product

    g_sales = Group.objects.create(name='sales')
    g_ops = Group.objects.create(name='ops')

    staff = User.objects.create(username='boss', is_staff=True)
    member = User.objects.create(username='alice')
    member.groups.add(g_sales)
    outsider = User.objects.create(username='bob')
    outsider.groups.add(g_ops)

    pub = Publication.objects.create(
        name='products',
        model_module='ryzom_example_crud.models',
        model_class='Product',
    )

    def subscribe(user):
        client = Client.objects.create(user=user)
        return Subscription.objects.create(
            client=client, publication=pub,
            subscriber_id='x',
            subscriber_module='ryzom_example_crud.components',
            subscriber_class='ProductRows',
            options={},
        )

    staff_sub = subscribe(staff)
    member_sub = subscribe(member)
    outsider_sub = subscribe(outsider)
    anon_sub = subscribe(None)

    # A non-public product in the sales group, in stock.
    product = Product.objects.create(name='Widget', stock_qty=5, group=g_sales)
    ids = _candidate_ids(
        'ryzom_example_crud.models', 'Product',
        None, _snapshot(product),
    )

    assert staff_sub.id in ids        # staff sees everything
    assert member_sub.id in ids       # member of the row's group
    assert outsider_sub.id not in ids  # other group -> not a candidate
    assert anon_sub.id not in ids      # anonymous -> only public rows


@skip_reactive
@pytest.mark.django_db
def test_group_facet_forward_scopes_queryset_per_user():
    """The forward direction (rendering) must match the reverse routing: staff
    see all, a member sees their group + public, anonymous sees only public."""
    from django.contrib.auth.models import Group, User

    from ryzom_example_crud.models import Product

    g_sales = Group.objects.create(name='sales')
    g_ops = Group.objects.create(name='ops')
    member = User.objects.create(username='alice')
    member.groups.add(g_sales)
    staff = User.objects.create(username='boss', is_staff=True)

    Product.objects.create(name='Public', group=None)
    Product.objects.create(name='Sales', group=g_sales)
    Product.objects.create(name='Ops', group=g_ops)

    from ryzom_example_crud.components import ProductRows

    def visible(user):
        qs = ProductRows.get_queryset(user, Product.objects.all(), {})
        return set(qs.values_list('name', flat=True))

    assert visible(staff) == {'Public', 'Sales', 'Ops'}
    assert visible(member) == {'Public', 'Sales'}
    assert visible(None) == {'Public'}
