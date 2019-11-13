import pytest
import unittest

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.test import TestCase

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.backends.base import SessionBase
from django.test.client import RequestFactory as drf

from ryzom.components import component_html

from todos.crudlfap import TaskRouter


class RequestFactory(drf):
    def __init__(self, user=None):
        self.user = user or AnonymousUser()
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


@pytest.mark.django_db
def test_render_input_field(router, srf):
    view = router.views['create']()
    view.request = srf.get('/task/create')
    form = view.form
    rendered = component_html('ryzom.components.django.Form', form)
    assert 'User' in rendered
    assert 'About' in rendered


class FormTest(TestCase):

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

    @pytest.mark.django_db
    def test_form_display(self):
        response = self.client.get("/task/create")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_render_ryzom(self):
        response = self.client.get("/task/create")
        assert response.status_code == 200
        resp = response.content.decode()
        # DEBUG:
        print(resp)
        assert 'User' in resp
        assert 'About' in resp
