"""
Render Django forms using ryzom components.
"""
import logging
from collections.abc import Iterable

from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from ..backends.ryzom import Ryzom
from .components import (Div, Input, Label, Li, Optgroup, Option, Select, Text,
                         Textarea, Ul)

logger = logging.getLogger(__name__)


class Factory:
    """ Return the ryzom class required to render the ~django.forms.Widget.
        Initialise with a dotted module path or the template engine
        settings are used by default.
        The fallback to defaults can be disabled to force full override.

    :param str module: A dotted module path to custom components.
    :param bool fallback: Use default components, if available.
    :return: A Factory instance that will import the required Component.
    """
    def __init__(self, module=None, fallback=True):
        self.default_module = Ryzom.get_default().components_module
        self.module = module or self.default_module
        self.fallback = fallback

    def __call__(self, widget):
        cls = f'{self.module}.{type(widget).__name__}'
        try:
            cls = import_string(cls)
        except (ImportError,) as exc:  # noqa: F841
            if self.fallback and (self.module != self.default_module):
                default_cls = f'{self.default_module}.{type(widget).__name__}'
                try:
                    default_cls = import_string(default_cls)
                    logger.debug(f'Ryzom - using default widget for: {cls}')
                    cls = default_cls
                except (ImportError,) as exc:  # noqa: F841
                    pass
            # If requested widget is not found, use a basic custom widget.
            if isinstance(cls, str):
                logger.debug(f'Ryzom - widget not found: {cls}.')
                cls = f'{self.module}.TextInput'
                cls = import_string(cls)
        return cls

    @classmethod
    def as_component(self, widget):
        widget_type = type(widget).__name__
        widget_type = f'{self.default_module}.{widget_type}'
        try:
            cls = import_string(widget_type)
        except (ImportError,) as exc:  # noqa: F841
            raise NotImplementedError(
                f'Widget class {widget_type} not found.'
            )
        return cls


class Static:
    '''Return a static url for an app asset.

    :param str src: The app path of the asset.
    '''
    def __init__(self, src):
        self._data = src
        self.url = staticfiles_storage.url(src)

    def __str__(self):
        return self.url


class TextInput(Input):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type']
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']

        super().__init__(**attrs)


class NumberInput(TextInput):
    pass


class EmailInput(TextInput):
    pass


class URLInput(TextInput):
    pass


class PasswordInput(TextInput):
    pass


class HiddenInput(TextInput):
    pass


class MultiWidget(Div):
    """ Return a list of widgets of the correct types.
        NOTE: Adds an extra div tag as a container for the widgets.
    """
    def __init__(self, multi_widget):
        content = []
        factory = Factory()
        for widget in multi_widget.subwidgets:
            attrs = widget['attrs']
            attrs.update({
                'name': widget['name'],
            })
            if widget['type'] is not None:
                attrs['type'] = widget['type']
            if widget['value'] is not None:
                attrs['value'] = widget['value']
            cls = factory(widget)
            component = cls(widget)
            content.extend(
                component if isinstance(component, Iterable) else [component]
            )
        super().__init__(*content, **attrs)


class MultipleHiddenInput(MultiWidget):
    """ Return a list of hidden widgets. """
    def __init__(self, multi_widget):
        super().__init__(multi_widget)


class FileInput(TextInput):
    pass


class ClearableFileInput():
    # TODO: Code ClearableFileInput()
    pass


class Textarea(Textarea):
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


class DateTimeBaseInput(TextInput):
    pass


class DateInput(DateTimeBaseInput):
    pass


class DateTimeInput(DateTimeBaseInput):
    pass


class TimeInput(DateTimeBaseInput):
    pass


class CheckboxInput(TextInput):
    pass


class ChoiceWidget():
    # not directly called
    pass


class SelectOption(Option):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'value': widget['value'],
        })
        content = [Text(widget['label'])]
        super().__init__(*content, **attrs)


class Select(Select):
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
                    SelectOption(option)
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


class NullBooleanSelect(Select):
    pass


class SelectMultiple(Select):
    pass


class InputOption(Label):
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
                *[TextInput(widget),
                  Text(widget['label'])
                  ],
                **label_attrs
            )
        else:
            raise NotImplementedError
            # Use TextInput() if the label is not required.


class MultipleInput(Ul):
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
                    Li(*[InputOption(option) if option['wrap_label']
                         else TextInput(option)
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


class RadioSelect(MultipleInput):
    pass


class CheckboxSelectMultiple(MultipleInput):
    pass


class SplitDateTimeWidget(MultiWidget):
    pass


class SplitHiddenDateTimeWidget(SplitDateTimeWidget):
    pass


class SelectDateWidget(MultiWidget):
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
    def __init__(self, field, widget=None, attrs=None, only_initial=False,  # noqa: C901 E501
                 label_suffix=None):
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
        label = label_tag = ''
        if field.label:
            label = field.label
            label_suffix = (label_suffix if label_suffix is not None
                            else field.field.label_suffix
                            if field.field.label_suffix is not None
                            else field.form.label_suffix)
            if label_suffix and label[-1] not in _(':?.!'):
                label_with_suffix = format_html('{}{}', label, label_suffix)
            label_tag = field.label_tag(field.label)

        widget_context['label_tag'] = label_tag
        widget_context['label'] = label_with_suffix
        widget_context['label_no_suffix'] = label

        ComponentCls = Factory()(widget)
        if label:
            # MUICSS may embed <label> after <input> in a containing div.
            if not getattr(ComponentCls, 'embed_label', False):
                content.append(
                    Text(label_tag)
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

    :param context: Dict-like object containing a ~django.forms.Form to be
                    rendered.
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
