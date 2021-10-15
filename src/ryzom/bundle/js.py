import ast
import inspect
import importlib
import py2js
from py2js.transpiler import JS
import re
import textwrap


AUTOCOMPILE = (
    'onclick',
    'onmouseover',
    'onsubmit',
    'onchange',
    'oninput',
)


def webcomponent(value):
    return [
        py2js.transpile_class(
            value.HTMLElement,
            superclass='HTMLElement',
            newname=value.__name__,
        ),
        f'window.customElements.define("{value.tag}", {value.__name__});',
    ]



def _functions(transpiler, done, **context):
    out = []
    for name, func in transpiler._functions.items():
        if func in done:
            continue
        func_src = textwrap.dedent(inspect.getsource(func))
        func_ast = ast.parse(func_src)
        func_ast.body[0].name = name
        func_js = JS()
        func_js._context = context
        func_js.visit(func_ast)
        out.append(func_js.read())
        if func_js._functions:
            out += _functions(func_js, done, **context)
        done.append(func)
    return out


def functions(value, done):
    out = []
    tree = ast.parse(textwrap.dedent(inspect.getsource(value.py2js)))
    transpiler = JS()
    transpiler._context = dict(self=value)
    transpiler.visit(tree)
    out += _functions(transpiler, done, self=value)
    return out


def methods(value, done_funcs):
    out = []

    for name in AUTOCOMPILE:
        method = getattr(value, name, None)
        if not method:
            continue
        src = textwrap.dedent(inspect.getsource(method))
        src = re.sub(r'^def ', f'def {value.__name__}_', src)
        tree = ast.parse(src)
        transpiler = JS()
        transpiler._context = dict(self=value)
        transpiler.visit(tree)
        out += [transpiler.read()]
        out += _functions(transpiler, done_funcs, self=value)

    return out


def bundle(*modules):
    out = []
    done = []
    done_funcs = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if value in done:
                continue
            if hasattr(value, 'HTMLElement'):
                out += webcomponent(value)
            if callable(getattr(value, 'py2js', None)):
                out += functions(value, done_funcs)
            out += methods(value, done_funcs)
            done.append(value)
    return '\n'.join(out)
