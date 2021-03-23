from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe

from ryzom.html import *
from .bundle import CSS_BUNDLE_URL, JS_BUNDLE_URL


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
    scripts = [JS_BUNDLE_URL]
    stylesheets = [CSS_BUNDLE_URL]


class CSRFInput(Input):
    def __init__(self, request):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(request)
        )
