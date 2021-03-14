'''
Ryzom MUI CSS components.
'''
import re
from collections.abc import Iterable

from django.utils.html import conditional_escape
from django.utils.translation import gettext as _

from .components import Select as RyzSelect
from .components import *  # noqa
from .django import Factory, InputOption, SelectOption
from .django import TextInput as DjangoTextInput

"""
class Component(Component):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})
        super().__init__(*args, **kwargs)


class Appbar(Component):
    '''
    Appbar component

    Represents a MUI CSS <appbar>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=None, attr=None, events=None,
                 parent='body', _id=None, context=None):
        return Div(content,
                   attr={'class': "mui-appbar"},
                   events, parent, _id)


class Button(Component):
    '''
    Button component

    Represents a MUI CSS <button>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=None, attr=None,
                 events=None, parent='body', _id=None, context=None):
        attr = attr or {}
        cls = attr.setdefault('class', '')
        attr['class'] = f"mui-btn {cls}"
        return Button(content, attr, events, parent, _id)


class Container(Component):
    '''
    Container component

    Represents a MUI CSS <container>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=None, attr=None, events=None,
                 parent='body', _id=None, context=None):
        return Div(content,
                   attr={'class': "mui-container"},
                   events, parent, _id)
"""


class MuiForm(Component):
    '''
    Form component

    Represents a MUI CSS <form>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        attrs = {'class': "mui-form"}
        super().__init__(*content, **attrs, tag='form')


class Legend(Component):
    '''
    Legend component

    Represents a MUI CSS <legend>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        super().__init__(*content, **attrs, tag='legend')


class TextInput(Div):
    # Prevent default pre-element labelling
    embed_label = True

    def __init__(self, widget):

        div_content = []
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type'],
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']
        div_content.append(
            Input(**attrs),
        )
        if 'label_tag' in widget:
            # Radio input options won't have a label_tag.
            div_content.append(
                widget['label_tag'],
            )
        div_attrs = {'class': "mui-textfield mui-textfield--float-label"}

        super().__init__(*div_content, **div_attrs)


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


# TODO: Code ClearableFileInput()
# class ClearableFileInput():
#     pass


class Textarea(Textarea):
    # Prevent default pre-element labelling
    embed_label = True

    def __init__(self, widget):
        content = []
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
        })
        if widget['value'] is not None:
            content.append(
                Text(widget['value']),
                widget['label_tag'],
            )
        div_content = []
        div_content.append(
            Textarea(*content, **attrs)
        )
        div_attrs = {'class': "mui-textfield mui-textfield--float-label"}

        super().__init__(*div_content, **div_attrs)


class DateTimeBaseInput(TextInput):
    pass


class DateInput(DateTimeBaseInput):
    pass


class DateTimeInput(DateTimeBaseInput):
    pass


class TimeInput(DateTimeBaseInput):
    pass


class CheckboxInput(Div):
    # Prevent default pre-element labelling
    embed_label = True

    def __init__(self, widget):
        div_content = []
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type'],
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']

        # widget['label_tag'] isn't useful here.
        div_content.append(
            Label(
                Input(**attrs),
                Text(widget.get(
                    'label', re.findall('>([^<]*)<', widget['label_tag'])[0])),
                **{'for': widget['attrs']['id']}
            )
        )
        div_attrs = {'class': "mui-checkbox"}

        super().__init__(*div_content, **div_attrs)


class ChoiceWidget():
    # not directly called
    pass


class Select(Div):
    def __init__(self, widget):
        div_content = []
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

        div_content.append(
            RyzSelect(*group_content, **attrs),
        )
        div_attrs = {"class": "mui-select"}
        super().__init__(*div_content, **div_attrs)


class NullBooleanSelect(Select):
    pass


class SelectMultiple(Div):
    def __init__(self, widget):
        options = []
        for group_name, group_choices, group_index in widget['optgroups']:
            for option in group_choices:
                options.append(
                    SelectOption(option)
                )

        super().__init__(
            Component(
                Component(
                    *options, multiple='true', name=widget['name'],
                    tag='select', slot='select'
                ),
                Component(slot='deck', tag='div'),
                Component(
                    Component(slot='input', tag='input', type='text'),
                    slot='input',
                    tag='autocomplete-light',
                ),
                multiple='true',
                tag='autocomplete-select'
            )
        )


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
                    Li(InputOption(option)
                           if option['wrap_label']
                           else DjangoTextInput(option)
                           )
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


class Button(Button):
    """
    {{ render_button(view.title_submit, button_type="submit",
        button_class="btn-primary") }}
    """
    def __init__(self, widget):
        """
        def render_button(
            content,
            button_type=None,
            icon=None,
            button_class="btn-default",
            size="",
            href="",
            name=None,
            value=None,
            title=None,
            extra_classes="",
            id="",
        ):

        """
        div_content = []
        attrs = widget['attrs']
        attrs.update({
            'name': widget['name'],
            'type': widget['type'],
        })
        if widget['value'] is not None:
            attrs['value'] = widget['value']
        div_content.append(
            Input(**attrs),
            widget['label'],
        )
        div_attrs = {'class': "mui-textfield mui-textfield--float-label"}

        super().__init__(*div_content, **div_attrs)


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
    """Render a MUI field using ryzom components and return an AST.

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

        # For CheckboxInput
        label_chkbox = ''
        if field.label:
            label = conditional_escape(field.label)
            label_chkbox = label
            label = field.label_tag(label) or ''
        else:
            label = ''

        widget_context['label_tag'] = label
        widget_context['label'] = label_chkbox

        ComponentCls = Factory()(widget)
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

    :param ~django.forms.Form: The form being rendered.
    :return: An AST representing the rendered fields.
    :rtype: list
    """
    def __init__(self, form):
        content = []
        # form.non_field_errors
        content.append(NonFieldErrors(form))
        content.append(HiddenErrors(form))
        # form.visible_fields
        content.append(VisibleFields(form))
        # form.hidden_fields
        content.append(HiddenFields(form))

        super().__init__(
            *content,
        )
