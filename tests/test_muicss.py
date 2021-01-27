import pytest

from django.forms.widgets import PasswordInput, TextInput
from django.test import SimpleTestCase, override_settings

from ryzom.backends.ryzom import Ryzom
from ryzom.components.django import Factory, ClearableFileInput
from ryzom.components.muicss import PasswordInput as MuiPasswordInput
from ryzom.components.muicss import TextInput as MuiTextInput

from .test_django import NonModelFormTest


@override_settings(TEMPLATES=[
    {
        "BACKEND": "ryzom.backends.ryzom.Ryzom",
        "OPTIONS": {
            "app_dirname": "components",
            "components_module": "ryzom.components.muicss",
        },
    },
])
class TestMuiNonModelForm(NonModelFormTest, SimpleTestCase):
    prefix = "Mui"


@pytest.mark.latest
@override_settings(TEMPLATES=[
    {
        "BACKEND": "ryzom.backends.ryzom.Ryzom",
        "OPTIONS": {
            "app_dirname": "components",
            "components_module": "ryzom.components.django",
        },
    },
])
class TestMuiFactory(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Ryzom.get_default.cache_clear()

    def test_mui_widget_factory(self):
        factory = Factory('ryzom.components.muicss')
        widget = factory(PasswordInput())
        assert widget is MuiPasswordInput

    def test_mui_widget_fallback_to_django(self):
        factory = Factory('ryzom.components.muicss')
        # Widget ClearableFileInput is not yet implemented for MUI.
        widget = factory(ClearableFileInput())
        assert widget is ClearableFileInput

    def test_mui_widget_not_found(self):
        class FakeWidget():
            pass


        factory = Factory('ryzom.components.muicss')
        widget = factory(FakeWidget())
        assert widget is MuiTextInput
