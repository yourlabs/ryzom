"""Client-pull (polling) transport tests (POLLING.md).

These exercise ``ryzom_django_channels.polling`` directly against the DB: build a
``ProductRows`` subscription, seed its stored window (as SSR would), then assert
that ``poll_client`` returns the right DDP messages as products are
created/edited/deleted — and crucially nothing on an idle poll.

Products are created without a group and the client is anonymous, so any
visibility facet admits every row.
"""
import pytest
from django.conf import settings
from django.utils import timezone

skip_reactive = pytest.mark.skipif(
    not settings.CHANNELS_ENABLE, reason='Reactive disabled')


def _kinds(messages):
    return [m['type'] for m in messages]


def _make_sub():
    from ryzom_django_channels.models import Client, Publication, Subscription

    pub, _ = Publication.objects.get_or_create(
        name='products',
        defaults=dict(
            model_module='ryzom_example_crud.models',
            model_class='Product',
        ),
    )
    client = Client.objects.create()  # anonymous
    sub = Subscription.objects.create(
        client=client, publication=pub,
        subscriber_id='tbody',
        subscriber_module='ryzom_example_crud.components',
        subscriber_class='ProductRows',
        options={},
    )
    sub.get_queryset()  # seed the stored window like the initial SSR render
    return client, sub


def _baseline(client):
    """First poll establishes the fingerprint baseline and must be empty."""
    from ryzom_django_channels.polling import poll_client
    assert poll_client(client) == []


@skip_reactive
@pytest.mark.django_db
def test_idle_poll_is_empty():
    from ryzom_example_crud.models import Product
    from ryzom_django_channels.polling import poll_client

    for n in ('Apple', 'Banana', 'Cherry'):
        Product.objects.create(name=n, stock_qty=3)
    client, _sub = _make_sub()
    _baseline(client)

    # Nothing changed since the baseline -> no messages, no flicker.
    assert poll_client(client) == []


@skip_reactive
@pytest.mark.django_db
def test_poll_detects_insert():
    from ryzom_example_crud.models import Product
    from ryzom_django_channels.polling import poll_client

    Product.objects.create(name='Apple', stock_qty=3)
    client, _sub = _make_sub()
    _baseline(client)

    Product.objects.create(name='Banana', stock_qty=3)
    messages = poll_client(client)
    assert _kinds(messages) == ['insert']


@skip_reactive
@pytest.mark.django_db
def test_poll_detects_change():
    from ryzom_example_crud.models import Product
    from ryzom_django_channels.polling import poll_client

    p = Product.objects.create(name='Apple', stock_qty=3)
    client, _sub = _make_sub()
    _baseline(client)

    p.stock_qty = 1
    p.save()
    messages = poll_client(client)
    assert _kinds(messages) == ['change']
    # the changed row is the one we edited
    assert messages[0]['params']['attrs']['id'] == f'product-{p.id}'


@skip_reactive
@pytest.mark.django_db
def test_poll_detects_remove():
    from ryzom_example_crud.models import Product
    from ryzom_django_channels.polling import poll_client

    a = Product.objects.create(name='Apple', stock_qty=3)
    Product.objects.create(name='Banana', stock_qty=3)
    client, _sub = _make_sub()
    _baseline(client)

    aid = a.id  # delete() nulls the in-memory pk
    a.delete()
    messages = poll_client(client)
    assert _kinds(messages) == ['remove']
    assert messages[0]['params']['id'] == f'product-{aid}'


@skip_reactive
@pytest.mark.django_db
def test_poll_reorder_replaces_window():
    from ryzom_example_crud.models import Product
    from ryzom_django_channels.polling import poll_client

    a = Product.objects.create(name='Apple', stock_qty=3)
    Product.objects.create(name='Banana', stock_qty=3)
    client, _sub = _make_sub()
    _baseline(client)

    # Rename Apple past Banana so the two in-window rows swap order.
    a.name = 'Zucchini'
    a.save()
    messages = poll_client(client)
    # full window replace: remove both, re-insert both in new order
    assert _kinds(messages) == ['remove', 'remove', 'insert', 'insert']


@skip_reactive
@pytest.mark.django_db
def test_ddp_poll_endpoint_returns_messages(client):
    """The HTTP view the browser actually hits: GET with the token, JSON back."""
    from ryzom_example_crud.models import Product

    Product.objects.create(name='Apple', stock_qty=3)
    cl, _sub = _make_sub()
    _baseline(cl)

    Product.objects.create(name='Banana', stock_qty=3)
    resp = client.get('/crud/products/poll/', {'token': cl.token})
    assert resp.status_code == 200
    assert resp['Cache-Control'] == 'no-store'
    data = resp.json()
    assert _kinds(data['messages']) == ['insert']


@skip_reactive
@pytest.mark.django_db
def test_ddp_poll_unknown_token_asks_reload(client):
    resp = client.get('/crud/products/poll/', {'token': 'nope'})
    assert resp.status_code == 200
    assert resp.json() == {'reload': True}


@skip_reactive
@pytest.mark.django_db
def test_sweep_reclaims_idle_pollers_only():
    from datetime import timedelta

    from ryzom_django_channels.models import Client
    from ryzom_django_channels.polling import sweep_stale_clients

    fresh = Client.objects.create(last_seen=timezone.now())
    stale = Client.objects.create(
        last_seen=timezone.now() - timedelta(seconds=120))
    push = Client.objects.create(last_seen=None)  # websocket client

    sweep_stale_clients(60)

    ids = set(Client.objects.values_list('id', flat=True))
    assert fresh.id in ids
    assert push.id in ids
    assert stale.id not in ids
