"""
Render Django forms using ryzom components.
"""
from django.utils.html import conditional_escape
from django.utils.translation import gettext as _

from .components import *


class Factory:
    @classmethod
    def as_component(self, field):
        # TODO: map different widget.input_type(s) to ryzom.components
        return Input


class NonFieldErrors(Ul):
    """ Render non-field errors. """
    def __init__(self, form):
        content = []
        for error in form.non_field_errors():
            content.append(
                Li([Text(error)])
            )
        return super().__init__(
            content,
            {"class": "errorlist nonfield"}
        )


class HiddenErrors(Ul):
    """ Render hidden field errors. """
    def __init__(self, form):
        content = []
        for field in form.hidden_fields():
            if field.errors:
                for error in field.errors:
                    error_text = _('(Hidden field %(name)s) %(error)s') % \
                                 {'name': field.name, 'error': str(error)}
                    content.append(
                        Li([Text(error_text)])
                    )
        return super().__init__(
            content,
            {"class": "errorlist"}
        )


class HiddenFields(Div):
    """ Render hidden fields. """
    def __init__(self, form):
        content = []
        for field in form.hidden_fields():
            content.append(
                Field(field)
            )
        return super().__init__(
            content,
            {"class": "hidden"}
        )


def add_attrs(_dict, attrs):
    for name, value in _dict.items:
        pass


class FieldErrors(Ul):
    """ Render field errors. """
    def __init__(self, errors):
        content = []
        for error in errors:
            content.append(
                Li([Text(error)])
            )
        return super().__init__(
            content,
            {"class": "errorlist"}
        )


class HelpText(Ul):
    """ Render field help text. """
    def __init__(self, help_text):
        content = []
        content.append(
            Li([Text(help_text)])
        )
        return super().__init__(
            content,
            {"class": "helptext"}
        )


class Field(Div):
    """
    <input type="{{ widget.type }}" name="{{ widget.name }}"
    {% if widget.value != None %} value="{{ widget.value|stringformat:'s' }}"{% endif %}
    {% include "django/forms/widgets/attrs.html" %}>

    {% for name, value in widget.attrs.items %}{% if value is not False %} 
    {{ name }}{% if value is not True %}="{{ value|stringformat:'s' }}"{% endif %}
    {% endif %}{% endfor %}
    """
    def __init__(self, field):
        # TODO: get this closer to BoundField.as_widget()
        context = field.field.widget.get_context(field.label, field.value, {})
        widget = context['widget']
        content = []
        html_class_attr = {}
        errors = field.form.error_class(field.errors)
        css_classes = field.css_classes()
        if css_classes:
            html_class_attr = {"class": css_classes}
        # build attrs
        attrs = {
            "type": widget.get('type', field.field.widget.input_type),
            "name": field.name,
        }
        if field.value() is not None:
            attrs['value'] = str(field.value())
        attrs.update(widget['attrs'])

        if field.label:
            label = conditional_escape(field.label)
            label = field.label_tag(label) or ''
        else:
            label = ''

        fld_component = Factory.as_component(field)
        if label:
            content.append(
                Label([Text(field.label)],
                      {'for': field.id_for_label}
                      )
            )
        content.append(fld_component(attr=attrs))
        if errors:
            content.append(FieldErrors(errors))
        if field.help_text:
            content.append(HelpText(field.help_text))
        return super().__init__(
            content,
            attr=html_class_attr
        )


class Fields(Div):
    def __init__(self, form):
        content = []
        for field in form.visible_fields():
            content.append(Field(field))
        return super().__init__(
            content
        )


class Form(Div):
    def __init__(self, form):
        content = []
        # form = context or {}
        # self.form = form
        # form.non_field_errors
        content.append(NonFieldErrors(form))
        content.append(HiddenErrors(form))
        # form.fields
        content.append(Fields(form))
        # form.hidden_fields
        content.append(HiddenFields(form))
        content.append(Text(f'Django Form {form.__class__.__name__}'))
        return super().__init__(
            content,
        )
