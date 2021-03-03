import difflib
import os
import re
import pytest
from django import forms
from ryzom import html
from ryzom_django_example.urls import ExampleForm


ryzom_id_re = re.compile(r'(?<=ryzom-id=")(?P<uuid>\w*)')


def assert_equals(expected, result):
    from django.test.html import parse_html
    expected = parse_html(expected)
    result = parse_html(re.sub(ryzom_id_re, '', str(result)))
    assert result == expected


def assert_equals_fixture(name, result):
    path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        f'{name}.html',
    )
    if not os.path.exists(path):
        result = re.sub(ryzom_id_re, '', str(result))
        with open(path, 'w') as f:
            f.write(result.replace('>', '>\n'))
        pytest.fail('Fixture created')
    with open(path, 'r') as f:
        expected = f.read()
    assert_equals(expected, result)


@pytest.mark.parametrize(
    'field,value',
    [
        (forms.CharField(label='L', help_text='H'), 'V'),
        (forms.BooleanField(label='L', help_text='H'), True),
        (forms.BooleanField(label='L'), False),
    ]
)
def test_widget_rendering(field, value):
    class TestForm(forms.Form):
        test = field
    result = TestForm(dict(test=value))['test'].to_html()
    assert_equals_fixture(
        f'test_widget_{type(field).__name__}_{value}',
        result,
    )


def test_form():
    result = ExampleForm(dict(
        char='',
        email='foo@b.b',
        datetime_0='11/11/2020',
        datetime_1='aoeu',
    )).to_html()
    assert_equals_fixture('test_form', result)


def test_form_to_component_override():
    class TestForm(ExampleForm):
        def to_component(self):
            return html.CList(self['char'], self['datetime'])
    result = TestForm().to_html()
    assert_equals_fixture('test_form_override', result)
