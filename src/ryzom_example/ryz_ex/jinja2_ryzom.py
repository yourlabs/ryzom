from operator import attrgetter

from django.template.loader import render_to_string
from jinja2.utils import contextfunction

from crudlfap.jinja2 import render_form as render_crudlfap


@contextfunction
def render_form(context, form):
    get_ryzom = attrgetter('Meta.model.Project.ryzom')
    try:
        _ = get_ryzom(form)
    except AttributeError:
        pass
    else:
        """
        context = dict(
            form=form,
        )
        tmpl = get_template(
            'ryzom.components.django.Form',
            using='ryzom',
        )
        return tmpl.render(context)
        """
        return render_to_string('ryzom.components.django.Form', context)

    return render_crudlfap(form)
