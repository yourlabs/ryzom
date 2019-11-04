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
        # Avoid 302 Redirect to the login page
        TaskCreateView.authenticate = False

    def test_form_display(self):
        response = self.client.get("/task/create")
        assert response.status_code == 200

    def test_render_ryzom(self):
        Task.Project.ryzom = True
        response = self.client.get("/task/create")
        assert response.status_code == 200
        assert 'MUI Form' in response.content.decode()
        Task.Project.ryzom = False

    @classmethod
    def tearDownClass(cls):
        TaskCreateView.authenticate = True
        super().tearDownClass()
