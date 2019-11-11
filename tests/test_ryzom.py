import pytest
import unittest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from todos.models import Task
from todos.crudlfap import TaskCreateView


class FormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Avoid 302 Redirect to the login page.
        # 'user' is required for the Task model.
        User = get_user_model()
        user = User(username='dev',
                    password='dev',
                    is_superuser=True)
        user.save()
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
