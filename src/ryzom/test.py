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
