import importlib
import py2js


def bundle(*modules):
    out = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if not hasattr(value, 'HTMLElement'):
                continue
            if not hasattr(value, 'tag'):
                continue

            out.append(
                py2js.transpile_class(
                    value.HTMLElement,
                    superclass='HTMLElement',
                    newname=value.__name__,
                )
            )
            out.append(f'window.customElements.define("{value.tag}", {value.__name__});')
    return '\n'.join(out)
