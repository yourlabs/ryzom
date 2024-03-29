"""
Tests for ryzom.js.

For py2js tests, see test_py2js.py
"""

from ryzom.components import Component
from ryzom import bundle
from .test_py2js import assert_equals_fixture


class MyComponent(Component):
    tag = 'foo-bar'
    style = {
        'padding': 0,
        ' p': {
            'margin': 0,
            ' ul': {'list-style-type': 'none'},
        },
        ':hover': {
            'margin': '10px'
        }
    }
    sass = '''
    @media (max-width: 700px)
        .MyComponent
            .hidden
                display: none
    '''

    class HTMLElement:
        def connectedCallback(self):
            this.connected = True


class OtherComponent(Component):
    tag = 'div'
    attrs = dict(style=dict(margin=0))

    def nested_injection():
        print('hi')

    def click_nested_injection():
        print('hi')

    def on_form_submit():
        self.nested_injection()

    def py2js(self):
        self.on_form_submit()

    def onclick(target):
        something()
        self.click_nested_injection()

    def onmouseover(target):
        self.nested_injection()


def test_bundle_js():
    assert_equals_fixture('test_bundle', bundle.js(__name__))
    assert OtherComponent.attrs.onclick == 'OtherComponent_onclick(this)'


def test_bundle_css():
    assert_equals_fixture('test_bundle', bundle.css(__name__), suffix='.css')
