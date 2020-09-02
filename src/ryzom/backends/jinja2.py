# -*- coding: utf-8 -*-
from django.template import TemplateSyntaxError
from django.utils.module_loading import import_string
from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader, TemplateNotFound
from threadlocals.threadlocals import get_current_request


class RyzomLoader(BaseLoader):
    """ Import a ryzom component in a Jinja2 template include. """

    def get_source(self, environment, template):
        try:
            self.component = import_string(template)
        except ImportError as exc:
            raise TemplateNotFound(template) from exc
        except Exception as exc:
            raise TemplateSyntaxError(template) from exc

        # Template context is not available here, so use threadlocals for
        # `request`.
        request = get_current_request()

        source = self.component(request).render()

        # Don't cache the response (the lambda).
        return source, template, lambda: False


def loader(template_dirs):
    """ Attempt to load a Jinja2 template, or import a ryzom component. """

    loader = ChoiceLoader([
        FileSystemLoader(template_dirs),
        RyzomLoader()
    ])
    return loader
