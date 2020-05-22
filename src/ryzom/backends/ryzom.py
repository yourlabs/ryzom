import functools

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.template.backends.django import reraise
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from django.utils.module_loading import import_string


class Ryzom(BaseEngine):

    app_dirname = 'components'

    @staticmethod
    @functools.lru_cache()
    def get_default():
        """
        This is required for preserving historical APIs that rely on a
        globally available, implicitly configured engine such as:

        >>> from django.template import Context, Template
        >>> template = Template("Hello {{ name }}!")
        >>> context = Context({'name': "world"})
        >>> template.render(context)
        'Hello world!'
        """
        from django.template import engines

        ryzom_engines = [engine for engine in engines.all()
                         if isinstance(engine, Ryzom)]
        if len(ryzom_engines) == 1:
            return ryzom_engines[0]
        elif len(ryzom_engines) == 0:
            raise ImproperlyConfigured(
                "No Ryzom backend is configured.")
        else:
            raise ImproperlyConfigured(
                "Multiple Ryzom backends are configured. "
                "You must select one explicitly.")

    def __init__(self, params):
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        self.app_dirname = options.pop("app_dirname", "components")
        super().__init__(params)

        self.debug = options.pop("debug", settings.DEBUG)
        self.context_processors = options.pop("context_processors", [])
        self.components_module = options.pop("components_module",
                                             "ryzom.components.muicss")
        self.components_prefix = options.pop("components_prefix",
                                             "Mui")

    def get_template(self, template_name):
        try:
            return Template(template_name)
        except TemplateDoesNotExist as exc:
            reraise(exc, self)


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
