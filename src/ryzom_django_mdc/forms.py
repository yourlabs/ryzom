from django import forms
from ryzom import html
import ryzom_mdc


def form_to_components(form):
    content = []
    if non_field_errors := form.non_field_errors():
        content.append(ErrorList(*non_field_errors))

    # TODO
    # if form.form.hidden_fields():
    #     form.content.append(HiddenFields(form.form))
    # if form.hidden_errors():  # Local method.
    #     form.content.append(HiddenErrors(form.form))

    for bf in form.visible_fields():
        try:
            component = html.templates[bf.field.widget.template_name]
        except KeyError:
            content.append(str(bf))
        else:
            content.append(component.factory(bf))

    return html.CList(*content)


def form_to_html(form):
    return form.to_components().to_html()


forms.Form.to_components = form_to_components
forms.Form.to_html = form_to_html
