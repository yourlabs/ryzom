"""
Render Django forms using ryzom components.
"""
from django.utils.html import conditional_escape
from django.utils.translation import gettext as _

from cli2 import Importable

from .components import *


COMPONENTS_MODULE = __name__  # 'ryzom.components.django'
COMPONENTS_PREFIX = 'Django'  # Django / MUICSS / Materialize


class Factory:
    @classmethod
    def as_component(self, field):
        widget_type = type(field.field.widget).__name__
        widget_type = f"{COMPONENTS_MODULE}.{COMPONENTS_PREFIX}{widget_type}"
        Component = Importable.factory(widget_type).target
        """ this would work for imported modules - is speed a factor?
        import sys
        component = getattr(sys.modules[module_name], widget_type, None)
        """
        if Component is None:
            raise NotImplementedError
        return Component


class DjangoTextInput(Input):
    def __init__(self, context):
        attrs = context['attrs']
        attrs.update({
            'name': context['name'],
            'type': context['type']
        })
        if context['value'] is not None:
            attrs['value'] = context['value']

        super().__init__(attr=attrs)


class DjangoSelect(Input):
    def __init__(self, context):
        attrs = context['attrs']
        attrs.update({
            'name': context['name'],
        })
        # TODO: optgroups and options
        super().__init__(attr=attrs)


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
    def __init__(self, field, widget=None, attrs=None, only_initial=False):
        widget = field.field.widget
        if field.field.localize:
            widget.is_localized = True
        attrs = attrs or {}
        attrs = field.build_widget_attrs(attrs, widget)
        if field.auto_id and 'id' not in widget.attrs:
            attrs.setdefault('id', field.html_initial_id
                             if only_initial else field.auto_id)

        context = widget.get_context(
            name=field.html_initial_name if only_initial else field.html_name,
            value=field.value(),
            attrs=attrs,
        )
        widget_context = context['widget']
        content = []
        html_class_attr = {}
        errors = field.form.error_class(field.errors)
        css_classes = field.css_classes()
        if css_classes:
            html_class_attr = {"class": css_classes}

        if field.label:
            label = conditional_escape(field.label)
            label = field.label_tag(label) or ''
        else:
            label = ''

        component = Factory.as_component(field)
        if label:
            content.append(
                Text(label)
            )
        content.append(component(widget_context))
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
