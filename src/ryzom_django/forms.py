from django import forms

from ryzom import html

from .html import ErrorList, HiddenFields


widget_templates = dict()

def widget_template(*names):
    global widget_templates
    def decorator(component):
        for name in names:
            widget_templates[name] = component
        return component
    return decorator


def boundfield_to_component(bf, **attrs):
    try:
        template = widget_templates[bf.field.widget.template_name]
    except KeyError:
        return html.Text(str(bf))
    else:
        return template.from_boundfield(bf, **attrs)
forms.BoundField.to_component = boundfield_to_component


def boundfield_to_html(bf, **context):
    return bf.to_component().to_html(**context)
forms.BoundField.to_html = boundfield_to_html


def form_to_component(form):
    content = []
    if non_field_errors := form.non_field_errors():
        error_list = form.non_field_error_component
        content.append(error_list(*non_field_errors))

    if form.hidden_fields():
        content.append(HiddenFields(*form.hidden_fields()))
    # if form.hidden_errors():  # Local method.
    #     form.content.append(HiddenErrors(form.form))

    for bf in form.visible_fields():
        content.append(bf.to_component())

    return html.CList(str(form.media), *content)
forms.BaseForm.non_field_error_component = ErrorList
forms.BaseForm.to_component = form_to_component


def form_to_html(form, **context):
    form_component = form.to_component()
    html = form_component.to_html(**context)
    form.scripts = form_component.scripts
    form.stylesheets = form_component.stylesheets
    return html
forms.BaseForm.to_html = form_to_html


def context_attrs(widget_context, extra=None):
    # extract attrs from a widget context
    attrs = dict()
    attrs.update(dict(
        name=widget_context['name'],
        value=widget_context['value'],
    ))
    attrs.update(widget_context['attrs'])
    if 'type' in widget_context:
        attrs['type'] = widget_context['type']
    attrs.update(extra or {})
    return attrs


def boundfield_context(bf, attrs=None):
    # copy of BoundField.as_widget() with get_context instead of widget.render()
    widget = bf.field.widget
    if bf.field.localize:
        widget.is_localized = True
    attrs = attrs or {}
    attrs = bf.build_widget_attrs(attrs, widget)
    if bf.auto_id and 'id' not in widget.attrs:
        attrs.setdefault('id', bf.auto_id)
    return widget.get_context(
        name=bf.html_name,
        value=bf.value(),
        attrs=attrs,
    )


def widget_context(bf, attrs=None):
    return boundfield_context(bf, attrs)['widget']


def widget_attrs(bf, attrs=None):
    return context_attrs(widget_context(bf), attrs)


def field_kwargs(bf):
    return dict(
        name=bf.name,
        label=bf.label,
        value=bf.value(),
        help_text=bf.help_text,
        errors=bf.errors,
    )
