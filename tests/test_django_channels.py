import re
import pytest
import functools
from django import http, views
from django.conf import settings
from django.test import RequestFactory
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

    class RBase(html.Div):
        def __init__(self, view, content='initial'):
            self.view = view
            super().__init__(content)


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


def find_token(js_str):
    s = re.search(r'token = "(?P<token>.*)";', js_str)
    return s.group(1)


@pytest.fixture
def token(view):
    return view.get_token()


@pytest.fixture
async def async_token(view):
    t = await sync_to_async(view.get_token)()
    return t


@pytest.fixture
def sub_comp(view, token, pub):
    c = SubscribeComp(view)
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

    js_string = view.get_token()
    assert 'window.token =' in js_string
    assert 'ws_connect()' in js_string
    assert Client.objects.all().count()


@db_reactive
def test_subscription(sub_comp, token):
    assert not Subscription.objects.count()

    sub_comp.render()
    sub = Subscription.objects.first()
    assert sub
    assert sub.client.token == find_token(token)


@db_reactive
def test_registration(reg_comp, token):
    assert not Registration.objects.count()

    reg_comp.render()
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
async def test_ws_connected(ws_token):
    await ws_token.connect()
    res = await ws_token.receive_json_from()
    assert res
    assert res['type'] == 'Connected'
    await ws_token.disconnect()


@async_db_reactive
async def test_register_changed(ws, async_reg_comp):
    await sync_to_async(async_reg_comp.render)()

    reg = await sync_to_async(register)('test_register')
    await sync_to_async(reg.update)(
        RegisterComp(async_reg_comp.view, 'changed')
    )
    res = await ws.receive_json_from()
    assert res['type'] == 'DDP'
    assert res['params']['type'] == 'change'
    assert ('changed'
            in res['params']['params']['content'][0]['content'])
    await ws.disconnect()
