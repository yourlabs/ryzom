from operator import attrgetter

from crudlfap.jinja2 import render_form as render_crudlfap


def render_form(form):
    get_ryzom = attrgetter('Meta.model.Project.ryzom')
    try:
        if get_ryzom(form):
            # TODO: call ryzom rendering
            return 'MUI Form'
    except AttributeError:
        pass

    return render_crudlfap(form)
