import os.path
import pytest
import re

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from ryzom.components import component_html
from ryzom_example.settings import (
    CRUDLFAP_TEMPLATE_BACKEND, DEFAULT_TEMPLATE_BACKEND
)

from tests.test_django import NonModelForm


# @pytest.mark.skip
@override_settings(TEMPLATES=[
    CRUDLFAP_TEMPLATE_BACKEND,
    DEFAULT_TEMPLATE_BACKEND,
    {
        "BACKEND": "ryzom.backends.ryzom.Ryzom",
        "OPTIONS": {
            "app_dirname": "components",
            "components_module": "ryzom.components.muicss",
            "components_prefix": "Mui",
        },
    },
])
class TestMuiNonModelForm(SimpleTestCase):
    """ Test the individual fields from ExampleForm for correct HTML.
        Create fixture files to compare semantic HTML (not literal text;
        convert ryzom-id uuids to 'uuid' in the fixture files).
        Note: pytest.mark.parametrize doesn't work in unittest.TestCase class,
        which is required for the assertHTMLEqual method.
    """
    @classmethod
    def setUpClass(cls):
        super(TestMuiNonModelForm, cls).setUpClass()
        cls.form = NonModelForm(
            initial={'char_field': 'charfield',
                     'date_field': '20-01-2019',
                     'email_field': 'test@example.com',
                     }
        )
        # substitute generated ryzom ids when comparing HTML
        cls.ryzom_re = re.compile(r'(?<=ryzom-id=")(?P<uuid>\w*)')
        cls.ryzom_sub = 'uuid'
        cls.fixture_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'fixtures'
        )
        cls.render = 'ryzom.components.django.Field'
        cls.maxDiff = None
        from django.template import engines
        cls.prefix = engines['ryzom'].components_prefix

    def compare_HTML(self, field_name, widget_name=""):
        field = self.form[field_name]
        type_name = f'{type(field.field).__name__}{widget_name}'
        rendered = component_html(self.render, field)
        rendered = self.ryzom_re.sub(self.ryzom_sub, rendered)
        with open(os.path.join(
                self.fixture_path, f'{self.prefix}{type_name}.txt')) as fixture:
            self.assertHTMLEqual(rendered, fixture.read())

    def test_char_field(self):
        field_name = 'char_field'
        self.compare_HTML(field_name)

    def test_date_field(self):
        field_name = 'date_field'
        self.compare_HTML(field_name)

    def test_email_field(self):
        field_name = 'email_field'
        self.compare_HTML(field_name)

    def test_boolean_field(self):
        field_name = 'boolean_field'
        self.compare_HTML(field_name)

    def test_null_boolean_field(self):
        field_name = 'null_boolean_field'
        self.compare_HTML(field_name)

    def test_choice_field(self):
        field_name = 'choice_field'
        self.compare_HTML(field_name)

    def test_choice_radio_field(self):
        field_name = 'choice_radio_field'
        self.compare_HTML(field_name, 'RadioSelect')
