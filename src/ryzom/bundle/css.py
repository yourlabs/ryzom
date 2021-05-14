import importlib
import textwrap

try:
    import sass
except:
    sass = None


def to_css(selector, style):
    out = []

    maincss = []
    for style_key, style_value in style.items():
        if isinstance(style_value, dict):
            continue
        maincss.append(f'  {style_key}: {style_value};')

    if maincss:
        out = [selector + ' {', *maincss, '}']

    for sub_selector, sub_style in style.items():
        if not isinstance(sub_style, dict):
            continue
        out += to_css(f'{selector}{sub_selector}', sub_style)

    return out


def bundle(*modules):
    out = []
    done = []
    for module in modules:
        mod = importlib.import_module(module)
        for key, value in mod.__dict__.items():
            if not isinstance(value, type):
                continue
            if not hasattr(value, 'attrs'):
                continue
            if value in done:
                continue
            if sass_src := getattr(value, 'sass', None):
                if sass:
                    css = sass.compile(
                        string=textwrap.dedent(sass_src),
                        indented=True
                    )
                    if css not in out:
                        out.append(css)
            if 'style' in value.attrs:
                out += to_css('.' + value.__name__, value.attrs.style)
            done.append(value)
    return '\n'.join(out)
