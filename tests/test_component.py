import pytest
from ryzom import html


def test_default_tag_name():
    class MyComponent(html.Component):
        pass

    assert MyComponent.tag == 'my-component'
    assert MyComponent().tag == 'my-component'

    # self naming of Component should not break inherited tag names
    class MyDivComponent(html.Div):
        pass
    assert MyDivComponent.tag == 'div'
    assert MyDivComponent().tag == 'div'

    # unless it defines an HTMLElement
    class MyDivComponent(html.Div):
        class HTMLElement:
            pass
    assert MyDivComponent.tag == 'my-div-component'
    assert MyDivComponent().tag == 'my-div-component'

    # test thread safety of tag override
    assert html.Div(tag='test').tag == 'test'
    assert html.Div().tag == 'div'


def test_declarative_attributes():
    class MyComponent(html.Component):
        attrs = {'type': 'text'}

    assert MyComponent(name='foo').attrs == {'type': 'text', 'name': 'foo'}


def test_declarative_noclose():
    class Foo(html.Div):
        selfclose = True
    assert Foo().selfclose
    assert not Foo(selfclose=False).selfclose


def test_addcls_rmcls():
    class MyComponent(html.Component):
        attrs = {'class': 'foo'}

    assert MyComponent(addcls='bar').attrs['class'] == 'foo bar'
    assert MyComponent(rmcls='foo', addcls='bar').attrs['class'] == 'bar'

    assert MyComponent(addcls=['a', 'b']).attrs['class'] == 'foo a b'
    assert MyComponent(cls=['a', 'b']).attrs['class'] == 'a b'


class Test1(html.Div):
    attrs = dict(
        x='x',
        y='y',
        z='z',
    )

class Test2(Test1):
    attrs = dict(
        x='xx',
        z=None,
    )


def test_attr_copy():
    # test that we didn't break the class (that attrs were copied)
    assert Test1().attrs is not Test1.attrs


def test_attr_inheritance():
    assert Test1.attrs.x == 'x'
    assert Test2.attrs.x == 'xx'
    assert Test2.attrs.y == 'y'


def test_attr_delete():
    assert 'z' not in Test2.attrs

    test = Test2()
    assert test.attrs.x
    test.attrs.x = None
    assert 'x' not in test.attrs

    test.attrs.lol = None
    assert 'lol' not in test.attrs

def test_attr_instance():
    test = Test1()
    test.attrs.x = None
    assert 'x' not in test.attrs
    # test against any side effect on class
    assert Test1.attrs.x == 'x'


def test_attr_class():
    class C1(html.Component):
        attrs = dict(cls='foo')
    assert C1.attrs['class'] == 'foo'
    assert C1().attrs['class'] == 'foo'

    class C2(C1):
        attrs = dict(addcls='bar')
    assert C2.attrs['class'] == 'foo bar'
    assert C2().attrs['class'] == 'foo bar'

    class C3(C2):
        attrs = dict(rmcls='foo')
    assert C3.attrs['class'] == 'bar'
    assert C3().attrs['class'] == 'bar'


def test_html_payload():
    test = html.HTMLPayload(background_color='white')
    assert [*test.keys()] == ['background-color']
    assert test['background-color'] == 'white'
    assert test.background_color == 'white'

    test.background_position = 'top'
    assert test['background-position'] == 'top'
    assert test.background_position == 'top'
    assert [*test.keys()] == ['background-color', 'background-position']


def test_attrs_to_html():
    comp = Test1()
    comp.attrs['foo'] = True
    comp.attrs.y = False
    comp.attrs.z = None
    comp.attrs['test'] = ''
    comp.attrs.lol_bar = 'ok'
    comp.attrs.style.x_y = 0
    comp.attrs.style.color = 'red'
    comp.attrs.style.o = None
    assert comp.attrs.to_html() == 'x="x" foo test="" lol-bar="ok" style="x-y: 0; color: red"'


class BlueWhite(html.Div):
    style = dict(
        background_color='white',
        color='blue',
    )


class RedWhite(BlueWhite):
    style = dict(
        color='red',
    )


def test_component_scripts_stylesheets():
    class Foo(html.Div):
        scripts = ['foo.js']
        stylesheets = ['foo.css']


    class Bar(html.Div):
        scripts = ['bar.js']
        stylesheets = ['bar.css']


    class FooBar(Foo, Bar):
        scripts = ['foobar.js']
        stylesheets = ['foobar.css']

    assert FooBar.scripts == [
        'foo.js',
        'bar.js',
        'foobar.js',
    ]

    assert FooBar.stylesheets == [
        'foo.css',
        'bar.css',
        'foobar.css',
    ]


def test_component_slots():
    comp = html.Div(foo=html.Div('foo'), bar=html.Div('bar'))
    foo = html.Div('foo', slot='foo')
    bar = html.Div('bar', slot='bar')
    assert comp.foo == foo
    assert comp.bar == bar
    assert comp.content == [foo, bar]


class Div(html.Div):
    style = {'pop': 'me'}

@pytest.mark.parametrize('El', [Div, html.Div])
def test_style(El):
    div = El(style='foo:bar')
    assert div.attrs.style.foo == 'bar'
    assert div.style.foo == 'bar'
    div.attrs.style.foo = 'test'
    assert div.style.foo == 'test'
    assert div.attrs.style.foo == 'test'


def test_markdown():
    assert html.Markdown('''
    # Title
    - list item
    Body
    [link](/bye)
    ''').render() == '''
<h1>Title</h1>
<ul>
<li>list item
Body
<a href="/bye">link</a></li>
</ul>
'''.strip()
