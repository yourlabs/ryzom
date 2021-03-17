"""
Test helpers for Ryzom TDD.

Example:

.. code-block:: python

    def test_columns():
        table = Table(
            [dict(name='foo', test='y')],
            columns=['name'],
        )
        result = table.to_html()
        assert pretty(result) == '''
    %table
      %thead
        %tr
          %th
            name
      %tbody
        %tr
          %td
            foo
    '''.strip()


In pytest, this will display a beautiful diff in case of failure !
"""

import os
import re
import pytest  # noqa: F401
from lxml.html import HtmlElement, fromstring


def tree(html):
    return html if isinstance(html, HtmlElement) else fromstring(html)


def pretty(html, indent=None):
    indent = indent or 0
    spaces = indent * ' '
    el = tree(html)

    out = [f'{spaces}%{el.tag}\n']
    for key in sorted(el.attrib.keys()):
        if key == 'ryzom-id':
            continue
        out += [f'{spaces}  {key}={el.attrib[key]}\n']
    if el.text:
        out += [f'{spaces}  {el.text}\n']
    for child in el:
        out += pretty(child, indent + 2)

    if el.tail:
        out += [f'{spaces}{el.tail}\n']

    if not indent:
        return ''.join(out).strip()

    return out


def test_pretty():
    assert pretty('''
    <foo bar="test"><a x="Y">text1<br />text2</a></foo>
    ''') == '''%foo
  bar=test
  %a
    x=Y
    text1
    %br
    text2
'''.strip()


ryzom_id_re = re.compile(r'(?<=ryzom-id=")([^"]*)')
re_uuid = re.compile(r'"[a-z0-9]{32}"')
csrf_re = r'[<][^<]*name="csrfmiddlewaretoken"[^>]*[>]'


def assert_equals(expected, result):
    from django.test.html import parse_html
    expected = parse_html(expected)
    result = parse_html(result)
    assert result == expected


def assert_equals_fixture(name, result):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'tests',
        'fixtures',
        f'{name}.html',
    ))
    result = re.sub(ryzom_id_re, '', str(result))
    result = re.sub(re_uuid, '""', str(result))
    result = re.sub(csrf_re, 'csrfmiddlewaretoken', result)
    if not os.path.exists(path):
        result = re.sub(ryzom_id_re, '', str(result))
        with open(path, 'w') as f:
            f.write(result)
        pytest.fail('Fixture created')
    with open(path, 'r') as f:
        expected = f.read()
    assert_equals(expected, result)
