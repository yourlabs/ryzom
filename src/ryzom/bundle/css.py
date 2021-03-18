import importlib

from ryzom.components import Component


def bundle(*modules):
    out = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if not isinstance(value, type):
                continue
            if not hasattr(value, 'attrs'):
                continue
            if 'style' not in value.attrs:
                continue

            line = '.' + value.__name__ + ' {'
            if line in out:
                continue  # already imported

            out.append(line)
            for style_key, style_value in value.attrs.style.items():
                out.append(f'  {style_key}: {style_value};')
            out.append('}')
    return '\n'.join(out)
