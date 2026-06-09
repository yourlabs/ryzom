import re
import json
import pytest
import functools
from datetime import timedelta
from django import http, views
from django.conf import settings
from django.test import RequestFactory
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from ryzom import html

if settings.CHANNELS_ENABLE:
    from asgiref.sync import sync_to_async
    from channels.auth import AuthMiddlewareStack
    from channels.testing import WebsocketCommunicator
    from ryzom_django_channels.consumers import Consumer
    from ryzom_django_channels.models import (
        Client, Subscription, Registration, Publication)
    from ryzom_django_channels.views import ReactiveMixin
    from ryzom_django_channels.components import (
        SubscribeComponentMixin,
        ReactiveComponentMixin
    )
    from ryzom_django_channels.views import register
    from ryzom_django_channels import ddp

    class RBase(html.Div):
        def __init__(self, *content, view=None, user=None):
            super().__init__(*content, view=view)

        def to_html(self, *content, view):
            self.view = view
            return super().to_html(content)


    class SubscribeComp(SubscribeComponentMixin, RBase):
        publication = 'test_pub'


    class RegisterComp(ReactiveComponentMixin, RBase):
        register = 'test_register'


skip_reactive = pytest.mark.skipif(not settings.CHANNELS_ENABLE, reason='Reactive disabled')


factory = RequestFactory()


def req(url='/', user=None):
    request = factory.get(url)
    request.user = user or AnonymousUser()
    return request


def db_reactive(func):
    @skip_reactive
    @pytest.mark.django_db
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper


def async_db_reactive(func):
    @skip_reactive
    @functools.wraps(func)
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def wrapper(*args, **kwargs):
        await func(*args, **kwargs)
    return wrapper


@pytest.fixture
def view():
    class MyView(ReactiveMixin, views.generic.View):
        pass

    view = MyView()
    view.setup(req())

    return view


@pytest.fixture
def pub():
    Publication.objects.create(name='test_pub')


def find_token(meta):
    return meta.attrs['content']


@pytest.fixture
def token(view):
    return view.get_token()


@pytest.fixture
async def async_token(view):
    t = await sync_to_async(view.get_token)()
    return t


@pytest.fixture
def sub_comp(view, token, pub):
    c = SubscribeComp()
    c.get_content = lambda *a, **kw : []

    return c


@pytest.fixture
def reg_comp(view, token):
    comp = RegisterComp(view)
    parent = html.Div(comp)

    return comp


@pytest.fixture
async def async_reg_comp(view, async_token):
    comp = RegisterComp(view)
    parent = html.Div(comp)

    return comp


@pytest.fixture
def ws_empty():
    communicator = WebsocketCommunicator(
        AuthMiddlewareStack(Consumer.as_asgi()),
        '/ws/ddp/')

    return communicator


@pytest.fixture
def ws_token(async_token):
    t = find_token(async_token)
    communicator = WebsocketCommunicator(
        AuthMiddlewareStack(Consumer.as_asgi()),
        f'ws/ddp/?{t}')

    return communicator


@pytest.fixture
async def ws(ws_token):
    await ws_token.connect()
    await ws_token.receive_json_from()
    return ws_token


@db_reactive
def test_get_token(view):
    assert not Client.objects.all().count()

    meta = view.get_token()
    # get_token now returns a meta Component instead of inline script
    assert meta.tag == 'meta'
    assert meta.attrs['name'] == 'ryzom-config'
    assert 'content' in meta.attrs  # token
    assert 'data-ws-host' in meta.attrs
    assert 'data-ws-port' in meta.attrs
    assert Client.objects.all().count()


@db_reactive
def test_subscription(sub_comp, view, token):
    assert not Subscription.objects.count()

    sub_comp.render(view=view)
    sub = Subscription.objects.first()
    assert sub
    assert sub.client.token == find_token(token)


@db_reactive
def test_registration(reg_comp, view, token):
    assert not Registration.objects.count()

    reg_comp.render(view=view)
    reg = Registration.objects.first()
    assert reg
    assert reg.subscriber_id == reg_comp.id
    assert reg.client.token == find_token(token)
    assert reg.subscriber_parent == reg_comp.parent.id


@async_db_reactive
async def test_ws_connect(ws_empty):
    connected, _ = await ws_empty.connect()
    assert connected
    await ws_empty.disconnect()


@async_db_reactive
async def test_ws_reload(ws_empty):
    await ws_empty.connect()
    res = await ws_empty.receive_json_from()
    assert res
    assert res['type'] == 'Reload'
    await ws_empty.disconnect()


@async_db_reactive
@pytest.mark.skip(reason='Broken minor release of Django and Channels?')
async def test_ws_connected(ws_token):
    await ws_token.connect()
    res = await ws_token.receive_json_from()
    assert res
    assert res['type'] == 'Connected'
    await ws_token.disconnect()


@async_db_reactive
@pytest.mark.skip(reason='Broken minor release of Django and Channels?')
async def test_register_changed(ws, async_reg_comp, view):
    await sync_to_async(async_reg_comp.render)(view=view)

    reg = await sync_to_async(register)('test_register')
    await sync_to_async(reg.replace)(
        RegisterComp, 'changed'
    )
    res = await ws.receive_json_from()
    assert res['type'] == 'DDP'
    assert res['params']['type'] == 'change'
    assert ('changed'
            in res['params']['params']['content'][0]['content'])
    await ws.disconnect()


# ---------------------------------------------------------------------------
# Reconnect persistence: detach-don't-delete + dirty-flag resync.
# See docs/plans/reactive-subscription-persistence.md
#
# These drive the consumer/ddp logic directly and synchronously. The async
# WebsocketCommunicator + token path is unusable here: the async fixtures
# (async_token/ws_token/ws) yield unawaited coroutines under this repo's
# pytest config, which is why test_ws_connected/test_register_changed are
# skipped. connect()/disconnect() are sync methods, so we call them on a bare
# Consumer with a minimal scope and stubbed accept()/send().
# ---------------------------------------------------------------------------

def _make_consumer(channel_name='', token=''):
    consumer = Consumer()
    consumer.scope = {'session': {}, 'query_string': token.encode()}
    consumer.channel_name = channel_name
    sent = []
    consumer.accept = lambda *a, **k: None
    consumer.send = lambda payload: sent.append(json.loads(payload))
    return consumer, sent


def _subscription(client):
    publication = Publication.objects.create(name='resync_pub')
    return Subscription.objects.create(
        client=client,
        publication=publication,
        subscriber_id='sub-id',
        subscriber_module='x',
        subscriber_class='Y',
    )


@db_reactive
def test_disconnect_detaches_keeps_bindings():
    client = Client.objects.create(
        token='detach', channel='chan.detach.1', transport='ws')
    sub = _subscription(client)
    reg = Registration.objects.create(
        name='r', client=client, subscriber_id='s', subscriber_parent='p',
        subscriber_module='m', subscriber_class='C')

    consumer, _ = _make_consumer(channel_name='chan.detach.1')
    consumer.disconnect(None)

    client.refresh_from_db()
    assert client.channel == ''
    assert client.detached_at is not None
    # Bindings survive the disconnect (no CASCADE delete).
    assert Subscription.objects.filter(pk=sub.pk).exists()
    assert Registration.objects.filter(pk=reg.pk).exists()


@db_reactive
def test_grace_reaper_deletes_stale_keeps_fresh():
    now = timezone.now()
    stale = Client.objects.create(
        token='stale', channel='', transport='ws',
        detached_at=now - timedelta(seconds=1000))   # past 900s grace
    fresh = Client.objects.create(
        token='fresh', channel='', transport='ws',
        detached_at=now - timedelta(seconds=100))    # within grace
    zombie = Client.objects.create(
        token='zombie', channel='', transport='ws',
        created=now - timedelta(minutes=3))          # never attached, old
    newtab = Client.objects.create(
        token='newtab', channel='', transport='ws')  # never attached, recent
    active = Client.objects.create(
        token='active', channel='chan.reap', transport='ws')

    consumer, _ = _make_consumer(channel_name='chan.reap')
    consumer.disconnect(None)

    assert not Client.objects.filter(pk=stale.pk).exists()
    assert Client.objects.filter(pk=fresh.pk).exists()
    assert not Client.objects.filter(pk=zombie.pk).exists()
    assert Client.objects.filter(pk=newtab.pk).exists()
    # The disconnecting client is now detached within grace -> survives.
    active.refresh_from_db()
    assert active.channel == ''
    assert active.detached_at is not None


@db_reactive
def test_grace_reaper_honors_setting():
    now = timezone.now()
    # With a 10s grace, a client detached 30s ago must be reaped.
    short = Client.objects.create(
        token='short', channel='', transport='ws',
        detached_at=now - timedelta(seconds=30))
    trigger = Client.objects.create(
        token='trigger', channel='chan.grace', transport='ws')

    consumer, _ = _make_consumer(channel_name='chan.grace')
    from django.test import override_settings
    with override_settings(RYZOM_CLIENT_GRACE_SECONDS=10):
        consumer.disconnect(None)

    assert not Client.objects.filter(pk=short.pk).exists()
    assert Client.objects.filter(pk=trigger.pk).exists()


# reattach() carries the new reconnect decision/mutation; connect() only wraps
# it with auth + I/O. We call it directly: connect()'s async_to_sync(get_user)
# closes the test transaction's DB connection (Channels' database_sync_to_async
# runs close_old_connections), the same async+DB issue that skips the WS tests.

@db_reactive
def test_clean_reconnect_returns_connected():
    now = timezone.now()
    client = Client.objects.create(
        token='tok-clean', channel='', transport='ws',
        detached_at=now - timedelta(seconds=30), needs_resync=False)

    consumer, _ = _make_consumer(channel_name='new.chan.clean')
    assert consumer.reattach(client, AnonymousUser()) == 'Connected'

    client.refresh_from_db()
    assert client.channel == 'new.chan.clean'
    assert client.detached_at is None
    assert client.needs_resync is False


@db_reactive
def test_dirty_reconnect_returns_reload_and_clears_flag():
    now = timezone.now()
    client = Client.objects.create(
        token='tok-dirty', channel='', transport='ws',
        detached_at=now - timedelta(seconds=30), needs_resync=True)

    consumer, _ = _make_consumer(channel_name='new.chan.dirty')
    assert consumer.reattach(client, AnonymousUser()) == 'Reload'

    client.refresh_from_db()
    assert client.channel == 'new.chan.dirty'
    assert client.detached_at is None
    assert client.needs_resync is False


@db_reactive
def test_first_connect_existing_client_returns_connected():
    # A freshly get_token()'d client (never attached) connecting the first time.
    client = Client.objects.create(
        token='tok-first', channel='', transport='ws')

    consumer, _ = _make_consumer(channel_name='new.chan.first')
    assert consumer.reattach(client, AnonymousUser()) == 'Connected'

    client.refresh_from_db()
    assert client.channel == 'new.chan.first'
    assert client.detached_at is None
    assert client.needs_resync is False


@db_reactive
def test_unknown_token_returns_reload():
    # connect() resolves an unknown token to client=None.
    consumer, _ = _make_consumer(channel_name='new.chan.x')
    assert consumer.reattach(None, AnonymousUser()) == 'Reload'


@db_reactive
def test_stale_channel_reconnect_returns_reload():
    # Ungraceful death (SIGKILL/crash/partition): disconnect() never ran, so
    # the client still has a non-empty (dead) channel. Pushes during that gap
    # were dropped without marking resync, so the DOM may have drifted ->
    # reattach must force one Reload even though needs_resync is False.
    client = Client.objects.create(
        token='tok-stale', channel='dead.chan.old', transport='ws',
        detached_at=None, needs_resync=False)

    consumer, _ = _make_consumer(channel_name='new.chan.fresh')
    assert consumer.reattach(client, AnonymousUser()) == 'Reload'

    client.refresh_from_db()
    assert client.channel == 'new.chan.fresh'
    assert client.detached_at is None
    assert client.needs_resync is False


@db_reactive
def test_skipped_push_marks_resync():
    client = Client.objects.create(
        token='push', channel='', transport='ws', needs_resync=False)
    sub = _subscription(client)
    # tmpl/instance are None on purpose: a working detached-guard returns
    # before touching them, so the call is safe; a regression would raise.
    ddp.send_change(sub, None, None)

    client.refresh_from_db()
    assert client.needs_resync is True


@db_reactive
def test_mark_needs_resync_sets_flag_for_detached_ws():
    client = Client.objects.create(
        token='m1', channel='', transport='ws', needs_resync=False)
    ddp._mark_needs_resync(client)
    client.refresh_from_db()
    assert client.needs_resync is True


@db_reactive
def test_mark_needs_resync_ignores_poll():
    client = Client.objects.create(
        token='m2', channel='', transport='poll', needs_resync=False)
    ddp._mark_needs_resync(client)
    client.refresh_from_db()
    assert client.needs_resync is False


@db_reactive
def test_mark_needs_resync_none_is_noop():
    ddp._mark_needs_resync(None)  # must not raise


@db_reactive
def test_mark_needs_resync_idempotent():
    client = Client.objects.create(
        token='m3', channel='', transport='ws', needs_resync=True)
    ddp._mark_needs_resync(client)
    client.refresh_from_db()
    assert client.needs_resync is True


@db_reactive
def test_available_client_not_marked_resync():
    # Counter to test_skipped_push_marks_resync: an attached client skips the
    # detached-guard, so send_change proceeds to build the template (our boom
    # proves we got past the guard) and must NOT mark resync.
    client = Client.objects.create(
        token='avail', channel='live.chan', transport='ws', needs_resync=False)
    sub = _subscription(client)

    def boom(instance):
        raise RuntimeError('past-guard')

    with pytest.raises(RuntimeError, match='past-guard'):
        ddp.send_change(sub, boom, object())

    client.refresh_from_db()
    assert client.needs_resync is False


# connect() end-to-end: patch get_user with a plain async stub so it does not
# run Channels' database_sync_to_async (which closes the test transaction's DB
# connection). This covers the connect() -> reattach() -> send(json.dumps())
# wiring and the token resolution that the direct reattach() tests skip.

def _patch_get_user(monkeypatch):
    async def fake_get_user(scope):
        return AnonymousUser()
    monkeypatch.setattr(
        'ryzom_django_channels.consumers.get_user', fake_get_user)


@db_reactive
def test_connect_clean_reconnect_sends_connected(monkeypatch):
    _patch_get_user(monkeypatch)
    now = timezone.now()
    Client.objects.create(
        token='ctok-clean', channel='', transport='ws',
        detached_at=now - timedelta(seconds=30), needs_resync=False)

    consumer, sent = _make_consumer(
        channel_name='conn.chan.clean', token='ctok-clean')
    consumer.connect()

    assert sent == [{'type': 'Connected'}]
    client = Client.objects.get(token='ctok-clean')
    assert client.channel == 'conn.chan.clean'
    assert client.detached_at is None
    assert client.needs_resync is False


@db_reactive
def test_connect_dirty_reconnect_sends_reload(monkeypatch):
    _patch_get_user(monkeypatch)
    Client.objects.create(
        token='ctok-dirty', channel='', transport='ws', needs_resync=True)

    consumer, sent = _make_consumer(
        channel_name='conn.chan.dirty', token='ctok-dirty')
    consumer.connect()

    assert sent == [{'type': 'Reload'}]
    assert Client.objects.get(token='ctok-dirty').needs_resync is False


@db_reactive
def test_connect_unknown_token_sends_reload(monkeypatch):
    _patch_get_user(monkeypatch)
    consumer, sent = _make_consumer(
        channel_name='conn.chan.x', token='nope-not-here')
    consumer.connect()
    assert sent == [{'type': 'Reload'}]


@db_reactive
def test_connect_no_token_sends_reload(monkeypatch):
    _patch_get_user(monkeypatch)
    consumer, sent = _make_consumer(channel_name='conn.chan.y', token='')
    consumer.connect()
    assert sent == [{'type': 'Reload'}]


@db_reactive
def test_register_replace_on_detached_marks_resync(monkeypatch):
    from ryzom_django_channels.views import RegisterManager
    client = Client.objects.create(
        token='regtok', channel='', transport='ws', needs_resync=False)
    reg = Registration.objects.create(
        name='test_register', client=client, subscriber_id='s',
        subscriber_parent='p', subscriber_module=RegisterComp.__module__,
        subscriber_class='RegisterComp')

    mgr = RegisterManager(Registration.objects.filter(pk=reg.pk))
    # Skip the best-effort defer thread; we only assert the resync flag here.
    monkeypatch.setattr(RegisterManager, 'defer', lambda self, c, content: None)
    mgr._replace(reg, RegisterComp)

    client.refresh_from_db()
    assert client.needs_resync is True


@db_reactive
def test_reap_stale_classmethod():
    now = timezone.now()
    stale = Client.objects.create(
        token='rs-stale', channel='', transport='ws',
        detached_at=now - timedelta(seconds=1000))
    fresh = Client.objects.create(
        token='rs-fresh', channel='', transport='ws',
        detached_at=now - timedelta(seconds=100))
    zombie = Client.objects.create(
        token='rs-zombie', channel='', transport='ws',
        created=now - timedelta(minutes=3))
    poll = Client.objects.create(
        token='rs-poll', channel='', transport='poll',
        detached_at=now - timedelta(seconds=1000))

    Client.reap_stale()

    assert not Client.objects.filter(pk=stale.pk).exists()
    assert Client.objects.filter(pk=fresh.pk).exists()
    assert not Client.objects.filter(pk=zombie.pk).exists()
    # Poll clients are never ws-detached and must be left alone by the reaper.
    assert Client.objects.filter(pk=poll.pk).exists()


@db_reactive
def test_reap_ryzom_clients_command():
    from django.core.management import call_command
    now = timezone.now()
    stale = Client.objects.create(
        token='rc-stale', channel='', transport='ws',
        detached_at=now - timedelta(seconds=1000))
    fresh = Client.objects.create(
        token='rc-fresh', channel='', transport='ws',
        detached_at=now - timedelta(seconds=100))

    call_command('reap_ryzom_clients')

    assert not Client.objects.filter(pk=stale.pk).exists()
    assert Client.objects.filter(pk=fresh.pk).exists()
