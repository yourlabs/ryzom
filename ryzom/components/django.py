"""
Render Django forms using ryzom components.
"""
from collections.abc import Iterable

from django.utils.html import conditional_escape
from django.utils.translation import gettext as _

from cli2 import Importable

from .components import *


COMPONENTS_MODULE = __name__  # 'ryzom.components.django'
COMPONENTS_PREFIX = 'Django'  # Django / MUICSS / Materialize


class Factory:
    @classmethod
    def as_component(self, widget):
        widget_type = type(widget).__name__
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
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type']
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']

        super().__init__(attr=attrs)


class DjangoNumberInput(DjangoTextInput):
    pass


class DjangoEmailInput(DjangoTextInput):
    pass


class DjangoURLInput(DjangoTextInput):
    pass


class DjangoPasswordInput(DjangoTextInput):
    pass


class DjangoHiddenInput(DjangoTextInput):
    pass


class DjangoMultipleWidget(Div):
    """ Return a list of widgets of the correct types.
        NOTE: Adds an extra div tag as a container for the widgets.
    """
    def __init__(self, multi_widget):
        content = []
        for widget in multi_widget.subwidgets:
            attrs = widget['attrs']
            attrs.update({
                'name': widget['name'],
            })
            if widget['type'] is not None:
                attrs['type'] = widget['type']
            if widget['value'] is not None:
                attrs['value'] = widget['value']
            Component = Factory.as_component(widget)
            component = Component(widget)
            content.extend(
                component if isinstance(component, Iterable) else [component]
            )
        super().__init__(content)


class DjangoMultipleHiddenInput(DjangoMultipleWidget):
    """ Return a list of hidden widgets. """
    def __init__(self, multi_widget):
        super().__init(multi_widget)


class DjangoFileInput(DjangoTextInput):
    pass


class DjangoClearableFileInput():
    # TODO: Code ClearableFileInput()
    pass


class DjangoTextarea(Textarea):
    def __init__(self, widget):
        content = []
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
        })
        if widget['value'] is not None:
            content.append(
                Text(widget['value'])
            )

        super().__init__(content, attr=attrs)


class DjangoDateTimeBaseInput(DjangoTextInput):
    pass


class DjangoDateInput(DjangoDateTimeBaseInput):
    pass


class DjangoDateTimeInput(DjangoDateTimeBaseInput):
    pass


class DjangoTimeInput(DjangoDateTimeBaseInput):
    pass


class DjangoCheckboxInput(DjangoTextInput):
    pass


class DjangoChoiceWidget():
    # not directly called
    pass


class DjangoOption(Option):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'value': widget['value'],
        })
        content = [Text(widget['label'])]
        super().__init__(content, attr=attrs)


class DjangoSelect(Select):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
        })
        group_content = []
        for group_name, group_choices, group_index in widget['optgroups']:
            option_content = []
            for option in group_choices:
                option_content.append(
                    DjangoOption(option)
                )
            if group_name:
                group_attrs = {
                    'label': group_name,
                }
                group_content.append(
                    Optgroup(option_content, group_attrs))
            else:
                group_content.extend(option_content)
        super().__init__(group_content, attr=attrs)


class DjangoNullBooleanSelect(DjangoSelect):
    pass


class DjangoSelectMultiple(DjangoSelect):
    pass


class DjangoRadioOption(Component):
    """ Return either an input element or a label wrapped around an input. """
    def __init__(self, widget):
        attrs = widget['attrs']
        if widget['wrap_label']:
            if attrs['id']:
                label_attrs = {
                    'for': attrs['id']
                }
            Label.__init__(
                [DjangoTextInput(widget),
                 Text(widget['label'])
                 ],
                label_attrs
            )
        else:
            DjangoTextInput.__init__(widget)


class DjangoRadioSelect(Ul):
    def __init__(self, widget):
        attrs = widget['attrs']
        radio_attrs = {}
        _id = attrs['id']
        if _id:
            radio_attrs.update({
                'id': _id
            })
        if attrs['class']:
            radio_attrs.update({
                'class': attrs['class']
            })
        group_content = []
        for group, options, index in widget['optgroups']:
            group_content = []
            option_content = []
            for option in options:
                option_content.append(
                    Li([DjangoRadioOption(option)])
                )
            if group:
                group_attrs = {}
                if _id:
                    group_attrs.update({
                        'id': f'{_id}_{index}'
                    })
                group_content.append(
                    Li([
                        Text(group),
                        Ul(option_content, group_attrs),
                    ])
                )
            else:
                group_content.extend(
                    option_content
                )

        super().__init__(group_content, attr=radio_attrs)


class NonFieldErrors(Ul):
    """ Render non-field errors. """
    def __init__(self, form):
        content = []
        for error in form.non_field_errors():
            content.append(
                Li([Text(error)])
            )
        super().__init__(
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
        super().__init__(
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
        super().__init__(
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
        super().__init__(
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
        super().__init__(
            content,
            {"class": "helptext"}
        )


class Field(Div):
    """Render a Django field using ryzom components and return an AST.

    Prepare the widget attrs, field label and context then render the
    field using ryzom components.
    Code adapted from ~django.forms.BoundField.as_widget().

    :param ~django.forms.BoundField field: The field being rendered.
    :param widget: A widget to override the default for the field.
    :type widget: ~django.forms.Widget or None
    :param attrs: Optional widget attributes.
    :type attrs: dict or None
    :param bool only_initial: A flag to render only initial dynamic values.
    :return: An AST representing the rendered field.
    :rtype: list
    """
    def __init__(self, field, widget=None, attrs=None, only_initial=False):
        widget = widget or field.field.widget
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

        Component = Factory.as_component(widget)
        if label:
            content.append(
                Text(label)
            )
        component = Component(widget_context)
        content.extend(
            component if isinstance(component, Iterable) else [component]
        )

        if errors:
            content.append(FieldErrors(errors))
        if field.help_text:
            content.append(HelpText(field.help_text))
        super().__init__(
            content,
            attr=html_class_attr
        )


class Fields(Div):
    def __init__(self, form):
        content = []
        for field in form.visible_fields():
            content.append(Field(field))
        super().__init__(
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
        # form.visible_fields
        content.append(Fields(form))
        # form.hidden_fields
        content.append(HiddenFields(form))
        content.append(Text(f'Django Form {form.__class__.__name__}'))
        super().__init__(
            content,
        )
