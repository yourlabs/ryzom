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
        bf.field.widget.attrs['aria-labelledby'] = f'id_{bf.name}_label'
        content.append(ryzom_mdc.MDCFieldOutlined(
            str(bf),
            name=bf.name,
            label=bf.field.label or bf.name.capitalize(),
            help_text=bf.help_text,
            errors=bf.form.error_class(bf.errors),
        ))
    return html.CList(*content)


def form_to_html(form):
    return form_to_components(form).to_html()


forms.Form.to_html = form_to_html
