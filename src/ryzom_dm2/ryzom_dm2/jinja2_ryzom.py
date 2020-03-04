from ryzom.components import component_html


def render_form(form):
    return component_html('ryzom.components.django.Form', form)


def render_button(*args, **kwargs):
    print('render_button', args, kwargs)
