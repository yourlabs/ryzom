from django import forms
import ryzom_mdc as html


def boundfield_to_component(bf):
    try:
        template = html.templates[bf.field.widget.template_name]
    except KeyError:
        return str(bf)
    else:
        return template.factory(bf)
forms.BoundField.to_component = boundfield_to_component


def boundfield_to_html(bf):
    return bf.to_component().to_html()
forms.BoundField.to_html = boundfield_to_html


def form_to_component(form):
    content = []
    if non_field_errors := form.non_field_errors():
        content.append(ErrorList(*non_field_errors))

    # TODO
    # if form.form.hidden_fields():
    #     form.content.append(HiddenFields(form.form))
    # if form.hidden_errors():  # Local method.
    #     form.content.append(HiddenErrors(form.form))

    for bf in form.visible_fields():
        content.append(html.MDCVerticalMargin(bf.to_component()))

    return html.CList(*content)
forms.BaseForm.to_component = form_to_component


def form_to_html(form):
    return form.to_component().to_html()
forms.BaseForm.to_html = form_to_html
