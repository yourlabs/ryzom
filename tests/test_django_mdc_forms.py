import difflib
import os
import re
from unittest.mock import patch

import pytest
from django import forms

from ryzom import html
from ryzom import test
from ryzom_django_example.views import ExampleForm


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
    test.assert_equals_fixture(
        f'test_widget_{type(field).__name__}_{value}',
        result,
    )


def test_view_get(client):
    result = client.get('/').content.decode('utf8')
    test.assert_equals_fixture('test_form_get', result)


def test_form_post():
    result = ExampleForm(dict(
        char='',
        email='foo@b.b',
        datetime_0='11/11/2020',
        datetime_1='aoeu',
        textarea='example textarea value',
    )).to_html()
    test.assert_equals_fixture('test_form_post', result)


def test_form_to_component_override():
    class TestForm(ExampleForm):
        def to_component(self):
            return html.CList(self['char'], self['datetime'])
    result = TestForm().to_html()
    test.assert_equals_fixture('test_form_override', result)
