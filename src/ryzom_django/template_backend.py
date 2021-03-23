import functools

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware import csrf
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.template.backends.django import reraise
from django.template.base import Origin
from django.template.context import BaseContext
from django.utils.encoding import smart_text
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.module_loading import import_string

from ryzom import html


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
        self._context_processors = options.pop("context_processors", [])
        self.components_module = options.pop("components_module",
                                             "ryzom.components.django")

    def get_template(self, template_name):
        if template_name in html.templates:
            return Template(html.templates[template_name], self)

        try:
            return Template(template_name, self)
        except TemplateDoesNotExist as exc:
            reraise(exc, self)

    @cached_property
    def context_processors(self):
        return tuple(import_string(path) for path in self._context_processors)


class Template:

    def __init__(self, template, backend):
        if callable(template):
            # NOTE: Jinja2 chokes on non-string template name values, so
            # calls in this form require the using='ryzom' keyword argument.
            self.template = template
        else:
            try:
                self.template = import_string(template)
            except ImportError as exc:
                raise TemplateDoesNotExist(template, backend=self) from exc
            except Exception as exc:
                raise TemplateSyntaxError(template) from exc
        self.backend = backend
        self.name = f'{self.template.__module__}.{self.template.__name__}'
        self.origin = Origin(
            name=self.name,
            template_name=self.name  # TODO: No searching of app_dirs yet.
        )

    def render(self, context=None, request=None):  # noqa: C901
        from django.utils.safestring import mark_safe
        try:
            from jinja2.utils import Markup
        except ImportError:
            Markup = None

        if context is None:
            context = {}
        if request is not None:
            def _get_val():
                token = csrf.get_token(request)
                if token is None:
                    return 'NOTPROVIDED'
                else:
                    return smart_text(token)

            context["csrf_token"] = SimpleLazyObject(_get_val)

            # Support for django context processors
            for processor in self.backend.context_processors:
                context.update(processor(request))

        if self.backend.debug:
            from django.test import signals

            # Define a django-like context to imitate the multi-
            # layered context object. This is mainly for apps like
            # django-debug-toolbar that are tightly coupled to django's
            # internal implementation of context.
            if not isinstance(context, BaseContext):
                class CompatibilityContext(dict):
                    @property
                    def dicts(self):
                        return [self]

                context = CompatibilityContext(context)

            signals.template_rendered.send(sender=self,
                                           template=self,
                                           context=context)

        html = self.template().render(**context)
        if Markup:
            html = Markup(html)
        return mark_safe(html)
