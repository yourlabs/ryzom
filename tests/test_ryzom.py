import pytest

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.context import Context
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase
from django.test.client import RequestFactory as drf
from django.test.utils import override_settings

from ryzom.backends.ryzom import Ryzom
from ryzom.components import component_html, Div, Text
from ryzom.components.django import Form

from todos.crudlfap import TaskRouter


pytestmark = pytest.mark.skipif(getattr(settings, 'PYTEST_SKIP', True),
                                reason="skip tests in this module")


class RequestFactory(drf):
    def __init__(self, user_=None):
        self.user = user_ or AnonymousUser()
        self.user = authenticate(username=self.user.username,
                                 password=self.user.username)
        super().__init__()

    def generic(self, *args, **kwargs):
        request = super().generic(*args, **kwargs)
        request.session = SessionBase()
        request.user = self.user
        request._messages = default_storage(request)
        return request


@pytest.fixture
def user():
    user = get_user_model().objects.create(username='dev',
                                           is_superuser=True,
                                           is_staff=True)
    user.set_password('dev')
    user.save()
    return user


@pytest.fixture
def srf(user):
    return RequestFactory(user)


@pytest.fixture
def router():
    return TaskRouter()


@pytest.fixture
def form(router, srf):
    view = router.views['create']()
    view.request = srf.get('/task/create', )
    return view.form


# @pytest.mark.skip
@pytest.mark.django_db
def test_render_field_input(form):
    rendered = component_html(
        'ryzom.components.django.Field', form['about'])
    assert '<input' in rendered
    assert 'type="text"' in rendered
    assert '<label ' in rendered
    assert 'About' in rendered  # label


# @pytest.mark.skip
@pytest.mark.django_db
def test_render_field_select(form):
    rendered = component_html(
        'ryzom.components.django.Field', form['user'])
    assert 'select' in rendered
    assert 'dev' in rendered  # user name
    assert 'User' in rendered  # label


@pytest.mark.django_db
def test_get_template(form):
    from django.template import engines
    ryzom_backend = engines['ryzom']
    context = dict(form=form)
    tmpl = get_template(
        'ryzom.components.django.Form',
    )
    assert tmpl.template == Form
    assert tmpl.backend == ryzom_backend


@pytest.mark.django_db
def test_render_template(form):
    context = dict(form=form)
    tmpl = get_template(
        'ryzom.components.django.Form',
    )
    rendered = tmpl.render(context)
    assert 'User' in rendered
    assert 'About' in rendered


def test_missing_template():
    with pytest.raises(TemplateDoesNotExist):
        tmpl = get_template(
            'ryzom.components.non.existent',
        )

def test_callable_template():
    # Jinja2 chokes on non-string templates, so requires 'using'
    tmpl = get_template(
        lambda x: Div([Text('test_text')]),
        using='ryzom',
    )
    rendered = tmpl.render()
    assert 'test_text</div>' in rendered


@pytest.mark.django_db
def test_context_processor_request(srf):
    class DivUser(Div):
        def __init__(self, context):
            content = [Text(f"User: {context['request'].user}"),
                       Text("|"),
                       Text(f"Test: {context['test_key']}"),
                       ]
            super().__init__(content)
            
    tmpl = get_template(
        DivUser,
        using='ryzom',
    )
    context = {
        'test_key': "test_value",
    }
    rendered = tmpl.render(context, srf)
    assert f"User: {srf.user}|Test: {context['test_key']}" in rendered


class TestRyzomBackendSettings(SimpleTestCase):

    def setUp(self):
        # Clear functools.lru_cache.
        Ryzom.get_default.cache_clear()

    def test_engine_options(self):
        from django.template import engines
        ryzom_backend = engines['ryzom']
        assert isinstance(ryzom_backend, Ryzom)
        assert ryzom_backend.components_module == "ryzom.components.muicss"
        assert ryzom_backend.components_prefix == "Mui"
    
    def test_engine_default(self):
        ryzom_backend = Ryzom.get_default()
        assert isinstance(ryzom_backend, Ryzom)
    
    @override_settings(TEMPLATES=[])
    def test_engine_default_missing(self):
        msg = "No Ryzom backend is configured."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            ryzom_backend = Ryzom.get_default()

    @override_settings(TEMPLATES=[{
            'NAME': 'ryzom',
            'BACKEND': 'ryzom.backends.ryzom.Ryzom',
            'OPTIONS': {'components_prefix': 'Abc'},
        }, {
            'NAME': 'ryzom_2',
            'BACKEND': 'ryzom.backends.ryzom.Ryzom',
            'OPTIONS': {'components_prefix': 'Xyz'},
        }])
    def test_engine_default_multiple(self):
        msg = "Multiple Ryzom backends are configured."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            ryzom_backend = Ryzom.get_default()


# @pytest.mark.skip
class TestTaskCreateView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Avoid 302 Redirect to the login page.
        # 'user' is required for the Task model.
        User = get_user_model()
        user = User.objects.create(username='dev',
                                   is_superuser=True)
        cls.user = user

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.user)

    def test_page_display(self):
        response = self.client.get("/task/create")
        assert response.status_code == 200

    def test_ryzom_form(self):
        response = self.client.get("/task/create")
        resp = response.content.decode()
        assert 'User' in resp
        assert 'About' in resp
