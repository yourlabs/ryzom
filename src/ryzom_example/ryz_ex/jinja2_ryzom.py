from operator import attrgetter

from django.template.context import Context
from django.template.loader import get_template

from crudlfap.jinja2 import render_form as render_crudlfap


def render_form(form):
    get_ryzom = attrgetter('Meta.model.Project.ryzom')
    try:
        _ = get_ryzom(form)
    except AttributeError:
        pass
    else:
        context = dict(form=form)
        tmpl = get_template(
            'ryzom.components.django.Form',
            using='ryzom',
        )
        return tmpl.render(Context(context))

    return render_crudlfap(form)
