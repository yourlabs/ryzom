"""
Render Django forms using ryzom components.
"""
from collections.abc import Iterable

from django.conf import settings
from django.template import engines
from django.template.context import Context
from django.utils.html import conditional_escape
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from .components import (
    Div, Input, Label, Li,
    Optgroup, Option, Select, Text, Textarea, Ul,
)


class Factory:
    """ Return the class required to render the ~django.forms.Widget. """
    def __init__(self, module):
        self.module = module

    def __call__(self, widget):
        cls = f'{self.module}.{type(widget).__name__}'
        try:
            cls = import_string(cls)
        except ImportError as exc:
            raise NotImplementedError(
                f'Ryzom not found: {cls}.'
            )
        return ComponentCls

    @classmethod
    def as_component(self, widget):
        ryzom_engine = engines['ryzom']
        widget_type = type(widget).__name__
        widget_type = (
            f'{ryzom_engine.components_module}'
            f'.{ryzom_engine.components_prefix}{widget_type}'
        )
        try:
            ComponentCls = import_string(widget_type)
        except ImportError as exc:
            raise NotImplementedError(
                f'Widget class {widget_type} not found.'
            )
        return ComponentCls


class DjangoTextInput(Input):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type']
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']

        super().__init__(**attrs)


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


class DjangoMultiWidget(Div):
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
            ComponentCls = Factory.as_component(widget)
            component = ComponentCls(widget)
            content.extend(
                component if isinstance(component, Iterable) else [component]
            )
        super().__init__(*content, **attrs)


class DjangoMultipleHiddenInput(DjangoMultiWidget):
    """ Return a list of hidden widgets. """
    def __init__(self, multi_widget):
        super().__init__(multi_widget)


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

        super().__init__(*content, **attrs)


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


class DjangoSelectOption(Option):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'value': widget['value'],
        })
        content = [Text(widget['label'])]
        super().__init__(*content, **attrs)


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
                    DjangoSelectOption(option)
                )
            if group_name:
                group_attrs = {
                    'label': group_name,
                }
                group_content.append(
                    Optgroup(*option_content, **group_attrs))
            else:
                group_content.extend(option_content)
        super().__init__(*group_content, **attrs)


class DjangoNullBooleanSelect(DjangoSelect):
    pass


class DjangoSelectMultiple(DjangoSelect):
    pass


class DjangoInputOption(Label):
    """ Return either an input element or a label wrapped around an input.
        Current style doesn't allow different element tags to be returned
        from one component so return the wrap_label version as default.
    """
    def __init__(self, widget):
        attrs = widget['attrs']
        if widget['wrap_label']:
            if attrs['id']:
                label_attrs = {
                    'for': attrs['id']
                }
            super().__init__(
                *[DjangoTextInput(widget),
                  Text(widget['label'])
                  ],
                **label_attrs
            )
        else:
            raise NotImplementedError
            # Use DjangoTextInput() if the label is not required.


class DjangoMultipleInput(Ul):
    def __init__(self, widget):
        attrs = widget['attrs']
        radio_attrs = {}
        _id = attrs['id']
        if _id:
            radio_attrs.update({
                'id': _id
            })
        if 'class' in attrs:
            radio_attrs.update({
                'class': attrs['class']
            })
        group_content = []
        for group, options, index in widget['optgroups']:
            option_content = []
            for option in options:
                option_content.append(
                    Li(*[DjangoInputOption(option) if option['wrap_label']
                         else DjangoTextInput(option)
                         ])
                )
            if group:
                group_attrs = {}
                if _id:
                    group_attrs['id'] = f'{_id}_{index}'
                group_content.append(
                    Li(
                       Text(group),
                       Ul(*option_content, **group_attrs),
                    )
                )
            else:
                group_content.extend(
                    option_content
                )

        super().__init__(*group_content, **radio_attrs)


class DjangoRadioSelect(DjangoMultipleInput):
    pass


class DjangoCheckboxSelectMultiple(DjangoMultipleInput):
    pass


class DjangoSplitDateTimeWidget(DjangoMultiWidget):
    pass


class DjangoSplitHiddenDateTimeWidget(DjangoSplitDateTimeWidget):
    pass


class DjangoSelectDateWidget(DjangoMultiWidget):
    pass


class NonFieldErrors(Ul):
    """ Render non-field errors. """
    def __init__(self, form):
        content = []
        for error in form.non_field_errors():
            content.append(
                Li(Text(error))
            )
        super().__init__(
            *content,
            **{"class": "errorlist nonfield"}
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
                        Li(Text(error_text))
                    )
        super().__init__(
            *content,
            **{"class": "errorlist"}
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
            *content,
            **{"class": "hidden"}
        )


class FieldErrors(Ul):
    """ Render field errors. """
    def __init__(self, errors):
        content = []
        for error in errors:
            content.append(
                Li(Text(error))
            )
        super().__init__(
            *content,
            **{"class": "errorlist"}
        )


class HelpText(Ul):
    """ Render field help text. """
    def __init__(self, help_text):
        content = []
        content.append(
            Li(Text(help_text))
        )
        super().__init__(
            *content,
            **{"class": "helptext"}
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
    def __init__(self, field, widget=None, attrs=None, only_initial=False):  # noqa: C901 E501
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
        html_class_attrs = {}
        errors = field.form.error_class(field.errors)
        css_classes = field.css_classes()
        if css_classes:
            html_class_attrs = {"class": css_classes}

        # For MuiCheckboxInput
        label_chkbox = ''
        if field.label:
            label = conditional_escape(field.label)
            label_chkbox = label
            label = field.label_tag(label) or ''
        else:
            label = ''

        widget_context['label_tag'] = label
        widget_context['label'] = label_chkbox

        ComponentCls = Factory.as_component(widget)
        if label:
            # MUICSS may embed <label> after <input> in a containing div.
            if not getattr(ComponentCls, 'embed_label', False):
                content.append(
                    Text(label)
                )
        component = ComponentCls(widget_context)
        content.extend(
            component if isinstance(component, Iterable) else [component]
        )

        if errors:
            content.append(FieldErrors(errors))
        if field.help_text:
            content.append(HelpText(field.help_text))
        super().__init__(
            *content,
            **html_class_attrs
        )


class VisibleFields(Div):
    """Render the regular Django fields of a form using ryzom components
    and return an AST.

    :param ~django.forms.Form: The form being rendered.
    :return: An AST representing the rendered fields.
    :rtype: list
    """
    def __init__(self, form):
        content = []
        for field in form.visible_fields():
            content.append(Field(field))
        super().__init__(
            *content
        )


class Form(Div):
    """Render a complete Django form using ryzom components and return an AST.

    :param context: Dict-like object containing a ~django.forms.Form to be rendered.
    :return: An AST representing the rendered fields.
    :rtype: list
    """
    def __init__(self, context=None):
        if context is None:
            context = {}
        self.orig_context = self.context = context
        self.prepare()
        super().__init__(
            *self.content
        )

    def hidden_errors(self):
        for h in self.form.hidden_fields():
            if h.errors:
                return True

    def prepare(self, extra_context=None):
        self.content = []  # Clear any previous rendering.
        if extra_context is not None:
            # Reset context and apply extras.
            self.context = self.orig_context.update(extra_context)
        self.form = self.context.get('form', None)
        if self.form is None:
            return

        if self.form.errors:
            self.content.append(
                Ul(Li(Text(_("Please fix any errors in this form."))),
                   **{"class": "errorlist"}
                   )
            )
        # form.non_field_errors
        if self.form.non_field_errors():
            self.content.append(NonFieldErrors(self.form))
        if self.hidden_errors():  # Local method.
            self.content.append(HiddenErrors(self.form))
        # form.visible_fields
        if self.form.visible_fields():
            self.content.append(VisibleFields(self.form))
        # form.hidden_fields
        if self.form.hidden_fields():
            self.content.append(HiddenFields(self.form))
        """
        # DEBUG: helper message
        if settings.DEBUG:
            ryzom_engine = engines['ryzom']
            self.content.append(
                Text(
                    f'ryzom {ryzom_engine.components_prefix}'
                    f' Form {self.form.__class__.__name__}'
                )
            )
        """
