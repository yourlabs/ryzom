import importlib
import py2js


def webcomponent(value):
    return [
        py2js.transpile_class(
            value.HTMLElement,
            superclass='HTMLElement',
            newname=value.__name__,
        ),
        f'window.customElements.define("{value.tag}", {value.__name__});',
    ]


def bundle(*modules):
    out = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if hasattr(value, 'HTMLElement') and hasattr(value, 'tag'):
                out += webcomponent(value)
    return '\n'.join(out)
