"""
Tests for py2js.

For ryzom.js tests (including bundle), see test_js.py
"""
import os

import pytest

import py2js
from py2js.renderer import JS


def assert_equals_fixture(name, result, suffix='.js'):
    path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        f'{name}{suffix}',
    )
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(result)
        pytest.fail('Fixture created')
    with open(path, 'r') as f:
        expected = f.read()

    assert result == expected


def test_assign():
    def func():
        a = 2
        b = 0.5
        c = 'string'
        d = []
        e = {}
        f = [1, 2 ,3]
        g = ['a', 'b', 'c']
        h = {'a': 1, 'b': 2}
        k = {'toto': 11532}
        i = h

    result = JS(func)

    assert_equals_fixture('test_assign',  result)


def test_assign_deep():
    def func():
        a.b.c = 2
        d.e.f['titi'] = 'test'

    result = JS(func)

    assert_equals_fixture('test_assign_deep', result)


def test_new():
    def func():
        test = new.HTMLElement(param)
        test.deep = new.deep.ClassName

    result = JS(func)

    assert_equals_fixture('test_new', result)


def test_print():
    def func():
        print('to console')

    result = JS(func)
    assert_equals_fixture('test_print', result)


def test_context():
    def func():
        toto = 10 + ctx_int
        print(ctx_str)
        tutu = ctx_dict['a']
        titi = ctx_dict[ctx_idx]
        assign_dict = ctx_dict
        val = assign_dict[ctx_idx]

    result = JS(func, dict(
        ctx_int=5,
        ctx_str='toto',
        ctx_dict=dict(
            a='tutu',
            b='test',
        ),
        ctx_idx='b'
    ))

    # Actually the ctx_dict is fully replaced before indexing
    # if referred by its name but can be assigned
    assert_equals_fixture('test_context', result)


def test_bin_op():
    def func():
        test1 = 2 + 4
        test2 = (3 / 1) + 4
        test3 = (10 - 5) % 3
        test4 = (4 / 2) + 5.2
        test5 = 'titi' + 'tutu'

    result = JS(func)
    assert_equals_fixture('test_bin_op', result)


def test_bool_op():
    def func():
        f = True and False
        t = 1 or 'titi'
        t = (x or y) and (a or b)

    result = JS(func)
    assert_equals_fixture('test_bool_op', result)


def test_lambda():
    def func():
        lambda: print(x)
        lambda arg : arg.method()

    result = JS(func)
    assert_equals_fixture('test_lambda', result)


def test_async_await():
    async def func():
        res = await fetch(params).then(
            lambda r : r
        ).then(
            lambda r : print(r) and r.status
        )

    result = JS(func)
    assert_equals_fixture('test_async_await', result)


def test_assign_op():
    def func():
        test = x != y
        test2 = not a == b

    result = JS(func)
    assert_equals_fixture('test_assign_op', result)


def test_in():
    def func():
        if 1 in [1, 2, 3]:
            print('test')

        if 2 not in [3, 4, 5]:
            print('test2')

        if x in deep.test:
            print('test3')

    result = JS(func)
    assert_equals_fixture('test_in', result)


def test_range():
    def func():
        a = range(10)

        for x in range(3):
            print(x)

    result = JS(func)
    assert_equals_fixture('test_range', result)


def test_py2js_context_attribute_string():
    class Test:
        def __init__(self):
            self._id = 'test'

        def bind():
            getElementByUuid(self._id)

    self = Test()
    assert py2js.transpile(self.bind, self=self) == '''function bind() {
    getElementByUuid("test");
}
'''


def test_py2js_context_attribute_deep():
    class Test_A:
        test = 'test'

    class Test:
        def __init__(self):
            self.x = Test_A()

        def log():
            # should write "console.log('test')"
            print(self.x.test)

    self = Test()
    assert py2js.transpile(self.log, self=self) == '''function log() {
    console.log("test");
}
'''


def test_py2js_context_attribute_deeper():
    class Test_A:
        z = 'test'

    class Test_B:
        y = Test_A()

    class Test_C:
        x = Test_B()

    class Test:
        def __init__(self):
            self.w = Test_C()

        def log():
            # should write "console.log('test')"
            print(self.w.x.y.z)

    self = Test()
    assert py2js.transpile(self.log, self=self) == '''function log() {
    console.log("test");
}
'''


def test_py2js_context_attribute_deeper2():
    class Test_A:
        z = 10

    class Test_B:
        y = Test_A()

    class Test_C:
        x = Test_B()

    class Test:
        def __init__(self):
            self.w = Test_C()

        def log():
            # should write "console.log(10)"
            print(self.w.x.y.z)

    self = Test()
    assert py2js.transpile(self.log, self=self) == '''function log() {
    console.log(10);
}
'''


def test_py2js_inject_mixin():
    class JSMixin:
        def fun(self):
            print('ok')

        def py2js(self):
            self.fun()

    class Test(JSMixin):
        tag = 'a'

    self = Test()
    assert py2js.transpile_body(self.py2js, self=self) == '''JSMixin_fun();\n'''


def test_transpile_body():
    def foo():
        print('a')
    assert py2js.transpile_body(foo) == "console.log('a');\n"


def test_class():
    class HTMLElement:
        pass

    class MyComponent(HTMLElement):
        def __init__(self):
            self.something = 'test'

    result = py2js.transpile(MyComponent)
    assert_equals_fixture('test_class', result)


def test_transpile_class():
    class MyComponent:
        def __init__(self):
            self.something = 'test'

        def change(self, event):
            print(event)

    result = py2js.transpile_class(
        MyComponent,
        newname='Test',
        superclass='HTMLElement',
    )
    assert_equals_fixture('test_transpile_class', result)

def test_transpile_function():
    class Test:
        def foo():
            bar
        foo.something = 'test'

    result = py2js.transpile_function(Test.foo, 'Foo__bar')
    assert_equals_fixture('test_transpile_function', result)
