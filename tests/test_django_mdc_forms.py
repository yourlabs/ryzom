import difflib
import os
import re
import pytest
from django import forms


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


def test_charfield():
    class TestForm(forms.Form):
        test = forms.CharField(label='test2')

    expected = '''
    <input
        class="mdc-text-field__input"
        type="text"
        required
        id="id_test"
        name="test"
        value="val"
        input-id="id_test"
        label-id="id_test_label"
        ryzom-id=""
    >
    '''
    assert_equals(expected, TestForm(dict(test='val'))['test'])


def test_form():
    class TestForm(forms.Form):
        test = forms.CharField()
    result = TestForm(dict(test='val')).to_html()
    assert_equals_fixture('test_charfield_form', result)
