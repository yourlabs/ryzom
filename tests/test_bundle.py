"""
Tests for ryzom.js.

For py2js tests, see test_py2js.py
"""

from ryzom.components import Component
from ryzom import bundle
from .test_py2js import assert_equals_fixture


class MyComponent(Component):
    tag = 'foo-bar'
    style = dict(padding=0)

    class HTMLElement:
        def connectedCallback(self):
            this.connected = True


class OtherComponent(Component):
    tag = 'div'
    attrs = dict(style=dict(margin=0))

    def nested_injection():
        print('hi')

    def on_form_submit():
        self.nested_injection()

    def py2js(self):
        self.on_form_submit()


def test_bundle_js():
    assert_equals_fixture('test_bundle', bundle.js(__name__))


def test_bundle_css():
    assert_equals_fixture('test_bundle', bundle.css(__name__), suffix='.css')
