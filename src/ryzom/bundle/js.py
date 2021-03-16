import ast
import inspect
import importlib
import py2js
from py2js.transpiler import JS
import textwrap


def webcomponent(value):
    return [
        py2js.transpile_class(
            value.HTMLElement,
            superclass='HTMLElement',
            newname=value.__name__,
        ),
        f'window.customElements.define("{value.tag}", {value.__name__});',
    ]


def functions(value):
    out = []
    tree = ast.parse(textwrap.dedent(inspect.getsource(value.py2js)))
    transpiler = JS()
    transpiler._context = dict(self=value)
    transpiler.visit(tree)
    for name, func in transpiler._functions.items():
        func_src = textwrap.dedent(inspect.getsource(func))
        func_ast = ast.parse(func_src)
        func_ast.body[0].name = name
        func_js = JS()
        func_js._context = dict(self=value)
        func_js.visit(func_ast)
        out.append(func_js.read())
    return out


def bundle(*modules):
    out = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if hasattr(value, 'HTMLElement') and hasattr(value, 'tag'):
                out += webcomponent(value)
            if callable(getattr(value, 'py2js', None)):
                out += functions(value)
    return '\n'.join(out)
