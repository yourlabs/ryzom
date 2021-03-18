import re
import pytest
from django import http, views
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from ryzom import html


skip_reactive = pytest.mark.skipif(not settings.CHANNELS_ENABLE, reason='Reactive disabled')


factory = RequestFactory()


def req(url='/', user=None):
    request = factory.get(url)
    request.user = user or AnonymousUser()
    return request


def db_reactive(func):
    @skip_reactive
    @pytest.mark.django_db
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper


@pytest.fixture(autouse=True)
def imports():
    from ryzom_django_channels.models import (
        Client, Subscription, Registration, Publication)
    from ryzom_django_channels.views import ReactiveMixin
    from ryzom_django_channels.components import (
        SubscribeComponentMixin,
        ReactiveComponentMixin
    )
    class MyView(ReactiveMixin, views.generic.View):
        pass
    view = MyView()
    view.setup(req())

    Publication.objects.create(name='test_pub')

    class RBase(html.Div):
        def __init__(self, view):
            self.view = view
            super().__init__()

    class ReactiveComp(SubscribeComponentMixin, RBase):
        publication = 'test_pub'

    class RegisterComp(ReactiveComponentMixin, RBase):
        register = 'test_register'

    globals().update(locals())


def find_token(js_str):
    s = re.search(r'token = "(?P<token>.*)";', js_str)
    return s.group(1)


@db_reactive
def test_get_token():
    js_string = view.get_token()
    assert 'window.token =' in js_string
    assert 'ws_connect()' in js_string


@db_reactive
def test_client_created():
    assert not Client.objects.all().count()

    view.get_token()
    assert Client.objects.all().count()


@db_reactive
def test_subscription_created():
    view.get_token()

    c = ReactiveComp(view)
    c.get_content = lambda *a, **kw : []

    assert not Subscription.objects.count()

    html_str = c.render()
    assert Subscription.objects.count()


@db_reactive
def test_subscription_token():
    token = view.get_token()

    c = ReactiveComp(view)
    c.get_content = lambda *a, **kw : []
    c.render()

    sub = Subscription.objects.first()
    assert sub.client.token == find_token(token)


@db_reactive
def test_registration_created():
    view.get_token()

    c = RegisterComp(view)
    cp = html.Div(c)

    assert not Registration.objects.count()

    c.render()
    assert Registration.objects.count()


@db_reactive
def test_registration_id():
    token = view.get_token()

    c = RegisterComp(view)
    cp = html.Div(c)
    cp.render()

    reg = Registration.objects.first()
    assert reg.subscriber_id == c.id


@db_reactive
def test_registration_token():
    token = view.get_token()

    c = RegisterComp(view)
    cp = html.Div(c)
    cp.render()

    reg = Registration.objects.first()
    assert reg.client.token == find_token(token)


@db_reactive
def test_registration_parent():
    token = view.get_token()

    c = RegisterComp(view)
    cp = html.Div(c)
    cp.render()

    reg = Registration.objects.first()
    assert reg.subscriber_parent == cp.id
