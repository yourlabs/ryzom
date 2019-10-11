from crudlfap.jinja2 import render_form as render_crudlfap


def render_form(form):
    if getattr(form, 'Meta', None):  # SearchForm and FilterSetForm
        if getattr(form.Meta.model.Project, 'ryzom', None):  # ModelForm
            # TODO: call ryzom rendering
            return 'MUI Form'

    return render_crudlfap(form)
