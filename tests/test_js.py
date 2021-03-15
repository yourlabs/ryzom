"""
Tests for ryzom.js.

For py2js tests, see test_py2js.py
"""

from ryzom.components import Component
from ryzom.js import bundle
from .test_py2js import assert_equals_fixture


class MyComponent(Component):
    tag = 'foo-bar'

    class HTMLElement:
        def connectedCallback(self):
            this.connected = True


def test_bundle():
    assert_equals_fixture('test_bundle', bundle(__name__))
