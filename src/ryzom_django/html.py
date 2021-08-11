import functools

from django.middleware.csrf import get_token
from django.utils.safestring import SafeString, mark_safe
from django.utils.html import escape

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


to_html = Component.to_html

def component_to_html(self, *args, **kwargs):
    if self.tag == 'text':
        if not isinstance(self.content, SafeString):
            return escape(f'{self.content}')
    return to_html(self, *args, **kwargs)

Component.to_html = component_to_html


class ErrorList(Ul):
    def __init__(self, *content, **attrs):
        super().__init__(
            *[Li(e) for e in content]
        )


class HiddenFields(CList):
    def __init__(self, *content, **attrs):
        super().__init__(*content, **attrs)


class Html(Html):
    scripts = [JSBundle()]
    stylesheets = [CSSBundle()]


class CSRFInput(Input):
    def __init__(self, request):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(request)
        )
