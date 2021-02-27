from ryzom import html


def test_default_tag_name():
    class MyComponent(html.Component):
        pass

    assert MyComponent().tag == 'my-component'


def test_declarative_attributes():
    class MyComponent(html.Component):
        attrs = {'type': 'text'}

    assert MyComponent(name='foo').attrs == {'type': 'text', 'name': 'foo'}


def test_addcls_rmcls():
    class MyComponent(html.Component):
        attrs = {'class': 'foo'}

    assert MyComponent(addcls='bar').attrs['class'] == 'foo bar'

    # test that we didn't break the class (that attrs were copied)
    assert MyComponent(addcls='bar').attrs['class'] == 'foo bar'

    assert MyComponent(rmcls='foo', addcls='bar').attrs['class'] == 'bar'
