from operator import attrgetter

from django import template

from crudlfap.jinja2 import render_form as render_crudlfap

from ryzom.components import component_html
from ryzom.components import django as ryzom


def render_form(form):
    get_ryzom = attrgetter('Meta.model.Project.ryzom')
    try:
        if get_ryzom(form):
            """
            form.renderer = ryzom.Field()
            context = dict(form=form)
            tpl = ['{{ form }}']

            return template.Template(
                ' '.join(tpl)
            ).render(template.Context(context))
            """
            return component_html('ryzom.components.django.Form', form)
    except AttributeError:
        pass

    return render_crudlfap(form)
