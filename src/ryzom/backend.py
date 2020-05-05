from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from django.utils.module_loading import import_string


class Ryzom(BaseEngine):

    # Name of the subdirectory containing the templates for this engine
    # inside an installed application.
    app_dirname = 'ryzom'

    def __init__(self, params):
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        super().__init__(params)

    def get_template(self, template_name):
        return Template(template_name)


class Template:

    def __init__(self, template):
        try:
            self.template = import_string(template)
        except ImportError as exc:
            raise TemplateDoesNotExist(template, backend=self) from exc
        except Exception as exc:
            raise TemplateSyntaxError(template) from exc

    def render(self, context=None, request=None):
        from django.utils.safestring import mark_safe
        try:
            from jinja2.utils import Markup
        except ImportError:
            Markup = None

        if context is None:
            context = {}
        if request is not None:
            context['request'] = request
            context['csrf_input'] = csrf_input_lazy(request)
            context['csrf_token'] = csrf_token_lazy(request)

        # ryzom templates currently consume context in __init__ rather than
        # render() - this should possibly change...
        html = self.template(context).render()
        if Markup:
            html = Markup(html)
        return mark_safe(html)
