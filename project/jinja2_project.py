from operator import attrgetter

from crudlfap.jinja2 import render_form as render_crudlfap

from ryzom.components import component_html


def render_form(form):
    get_ryzom = attrgetter('Meta.model.Project.ryzom')
    try:
        if get_ryzom(form):
            return component_html('ryzom.components.django.Form', form)
    except AttributeError:
        pass

    return render_crudlfap(form)
