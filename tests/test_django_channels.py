import re
import pytest
import functools
from django import http, views
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from ryzom import html

if settings.CHANNELS_ENABLE:
    from ryzom_django_channels.models import (
        Client, Subscription, Registration, Publication)
    from ryzom_django_channels.views import ReactiveMixin
    from ryzom_django_channels.components import (
        SubscribeComponentMixin,
        ReactiveComponentMixin
    )

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


class RBase(html.Div):
    def __init__(self, view):
        self.view = view
        super().__init__()


def find_token(js_str):
    s = re.search(r'token = "(?P<token>.*)";', js_str)
    return s.group(1)


@pytest.fixture
def token(view):
    return view.get_token()


@pytest.fixture
def sub_comp(view, token, pub):
    class SubscribeComp(SubscribeComponentMixin, RBase):
        publication = 'test_pub'

    c = SubscribeComp(view)
    c.get_content = lambda *a, **kw : []

    return c


@pytest.fixture
def reg_comp(view, token):
    class RegisterComp(ReactiveComponentMixin, RBase):
        register = 'test_register'

    comp = RegisterComp(view)
    parent = html.Div(comp)

    return comp


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
