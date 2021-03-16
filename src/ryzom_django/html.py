from django.utils.safestring import mark_safe

from ryzom.html import *
from .bundle import CSSBundle, JSBundle


def component_html(path, *args, **kwargs):
    try:
        from jinja2.utils import Markup
    except ImportError:
        Markup = None
    # todo: replace with importlib
    import cli2
    ComponentCls = cli2.Node(path).target
    component = ComponentCls(*args, **kwargs)
    html = component.to_html()

    if Markup:
        html = Markup(html)
    return mark_safe(html)


class ErrorList(Ul):
    def __init__(self, *content, **attrs):
        super().__init__(
            *[Li(e) for e in content]
        )


class Html(Html):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.head.stylesheets.append(CSSBundle().attrs.href)
        self.body.scripts.append(JSBundle().attrs.src)
