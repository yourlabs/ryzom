from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.backends.base import SessionBase
from django.db import models
from django.test.client import RequestFactory as drf
from django.urls import resolve, reverse
from django.views import generic

import pytest

from crudlfap import shortcuts as crudlfap
from crudlfap.route import Route
from crudlfap.router import Router
from todos.models import Task


# DEBUG: remove later
pytest.skip("skip crudlfap tests", allow_module_level=True)


class RequestFactory(drf):
    def __init__(self, user=None):
        self.user = user or AnonymousUser()
        super().__init__()

    def generic(self, *args, **kwargs):
        request = super().generic(*args, **kwargs)
        request.session = SessionBase()
        request.user = self.user
        request._messages = default_storage(request)
        return request


@pytest.fixture
def request_factory():
    return RequestFactory


@pytest.fixture
def srf():
    return RequestFactory(AnonymousUser())


class SimpleRouter(Router):
    fields = '__all__'


def test_views():
    router = SimpleRouter()
    view = crudlfap.TemplateView.clone(urlname='home')
    router.views = [view]
    assert router.views['home'] == view
    assert router.views[0].urlname == 'home'

    router.views['home'] = router.views['home'].clone(template_name='lol')
    assert router.views['home'].template_name == 'lol'

    del router.views['home']
    assert len(router.views) == 0


def test_urlfield():
    assert Router().urlfield is None


def test_urlfield_with_model():
    class TestModelUrl(models.Model):
        pass

        class Meta:
            app_label = 'todos'
            managed = False
    assert Router(model=TestModelUrl).urlfield == 'pk'


def test_urlfield_with_slug():
    class TestModel(models.Model):
        slug = models.CharField(max_length=100)

        class Meta:
            app_label = 'todos'
            managed = False
    assert Router(model=TestModel).urlfield == 'slug'


def test_namespace_none():
    assert Router().namespace is None


def test_namespace_with_model():
    assert Router(model=Task).namespace == 'task'


def test_path_with_model():
    assert Router(model=Task).urlpath == 'task'


def test_app_name_with_model():
    assert Router(model=Task).app_name == 'todos'


def test_registry_default():
    assert Router().registry == crudlfap.site


def test_registry():
    site = dict()
    assert Router(registry=site).registry == site


class DetailView(Route, generic.DetailView):
    menus = ['object']

    # Not setting this would require
    # request.user.has_perm('Task.detail_Task', obj) to pass
    allowed = True

    # This is done by crudlfap generic ObjectView, but here tests django
    # generic views
    def get_urlargs(self):
        # This may be executed with just the class context (self.object
        # resolving to type(self).object, as from
        # Route.clone(object=something).url
        return [self.object.about]


@pytest.fixture
def router():
    return Router(model=Task, views=[DetailView])


def test_getitem(router):
    assert issubclass(router['detail'], DetailView)


def test_urlpatterns(router):
    assert len(router.urlpatterns) == 1
    assert router.urlpatterns[0].name == 'detail'


def test_urlpattern(router):
    assert reverse('detail', router) == '/detail'
    assert resolve('/detail', router).func.view_class == router.views[0]


@pytest.mark.django_db
def test_get_menu(router, srf):
    a = Task(about='a')
    # Task object not saved so 'pk' is None. See get_urlargs().
    a_urlargs = a.about
    User = get_user_model()
    srf.user = User.objects.create(is_superuser=True)
    req = srf.get('/')
    result = router.get_menu('object', req, object=a)
    assert len(result) == 1
    assert isinstance(result[0], DetailView)
    assert result[0].urlargs == [a_urlargs]
    assert type(result[0]).urlargs == [a_urlargs]
    assert str(result[0].url) == f'/task/{a_urlargs}'

    b = type(result[0]).clone(object=a)
    assert str(b.url) == f'/task/{a_urlargs}'
