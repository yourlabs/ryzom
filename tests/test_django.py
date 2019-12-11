import os.path
import re

from django import forms
from django.conf import settings
from django.test import SimpleTestCase, override_settings

from ryzom.components import component_html


class NonModelForm(forms.Form):
    VINYL = 'vinyl'
    CD = 'cd'
    MP3 = 'mp3'
    VHS = 'vhs'
    DVD = 'dvd'
    BLURAY = 'blu-ray'
    MEDIA_CHOICES = (
        ('Audio', (
            (VINYL, 'Vinyl'),
            (CD, 'CD'),
            (MP3, 'MP3')
            )
         ),
        ('Video', (
            (VHS, 'VHS tape'),
            (DVD, 'DVD'),
            (BLURAY, 'Blu-ray')
            )
         ),
    )

    char_field = forms.CharField(label='Char field', max_length=50)
    date_field = forms.DateField(label='Date field')
    email_field = forms.EmailField(label='Email field')
    boolean_field = forms.BooleanField()
    null_boolean_field = forms.NullBooleanField()
    choice_field = forms.ChoiceField(choices=MEDIA_CHOICES)


@override_settings(RYZOM_COMPONENTS_MODULE='ryzom.components.django')
@override_settings(RYZOM_COMPONENTS_PREFIX='Django')
class TestDjangoNonModelForm(SimpleTestCase):
    """ Test the individual fields from ExampleForm for correct HTML.
        Create fixture files to compare semantic HTML (not literal text;
        convert ryzom-id uuids to 'uuid' in the fixture files).
        Note: pytest.mark.parametrize doesn't work in unittest.TestCase class,
        which is required for the assertHTMLEqual method.
    """
    @classmethod
    def setUpClass(cls):
        super(TestDjangoNonModelForm, cls).setUpClass()
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

    def compare_HTML(self, field_name):
        field = self.form[field_name]
        type_name = type(field.field).__name__
        prefix = settings.RYZOM_COMPONENTS_PREFIX
        rendered = component_html(self.render, field)
        rendered = self.ryzom_re.sub(self.ryzom_sub, rendered)
        with open(os.path.join(
                self.fixture_path, f'{prefix}{type_name}.txt')) as fixture:
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
