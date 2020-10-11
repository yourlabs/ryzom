'''
Ryzom MUI CSS components.
'''
from collections.abc import Iterable

from django.conf import settings
from django.template import engines
from django.utils.html import conditional_escape
from django.utils.translation import gettext as _

from .components import (
    Button, Component, Div, Input, Label, Li,
    Optgroup, Option, Select, Text, Textarea, Ul,
)
from .django import Factory, DjangoTextInput, Field, VisibleFields, Form


"""
class MuiComponent(Component):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})
        super().__init__(*args, **kwargs)


class Appbar(MuiComponent):
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


class Button(MuiComponent):
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
    MuiForm component

    Represents a MUI CSS <form>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        attrs = {'class': "mui-form"}
        super().__init__(*content, **attrs, tag='form')


class MuiLegend(Component):
    '''
    Legend component

    Represents a MUI CSS <legend>.

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        super().__init__(*content, **attrs, tag='legend')


class MuiTextInput(Div):
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


class MuiNumberInput(MuiTextInput):
    pass


class MuiEmailInput(MuiTextInput):
    pass


class MuiURLInput(MuiTextInput):
    pass


class MuiPasswordInput(MuiTextInput):
    pass


class MuiHiddenInput(MuiTextInput):
    pass


class MuiMultiWidget(Div):
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
        super().__init__(*content, **attrs)


class MuiMultipleHiddenInput(MuiMultiWidget):
    """ Return a list of hidden widgets. """
    def __init__(self, multi_widget):
        super().__init(multi_widget)


class MuiFileInput(MuiTextInput):
    pass


class MuiClearableFileInput():
    # TODO: Code ClearableFileInput()
    pass


class MuiTextarea(Textarea):
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


class MuiDateTimeBaseInput(MuiTextInput):
    pass


class MuiDateInput(MuiDateTimeBaseInput):
    pass


class MuiDateTimeInput(MuiDateTimeBaseInput):
    pass


class MuiTimeInput(MuiDateTimeBaseInput):
    pass


class MuiCheckboxInput(Div):
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
                Text(widget['label']),
                **{'for': widget['attrs']['id']}
            )
        )
        div_attrs = {'class': "mui-checkbox"}

        super().__init__(*div_content, **div_attrs)


class MuiChoiceWidget():
    # not directly called
    pass


class MuiSelectOption(Option):
    def __init__(self, widget):
        attrs = widget['attrs']
        attrs.update({
            'value': widget['value'],
        })
        content = [Text(widget['label'])]
        super().__init__(*content, **attrs)


class MuiSelect(Div):
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
                    MuiSelectOption(option)
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
            Select(*group_content, **attrs),
        )
        div_attrs = {"class": "mui-select"}
        super().__init__(*div_content, **div_attrs)


class MuiNullBooleanSelect(MuiSelect):
    pass


class MuiSelectMultiple(MuiSelect):
    pass


class MuiInputOption(Label):
    """ Return either an input element or a label wrapped around an input. """
    def __init__(self, widget):
        attrs = widget['attrs']
        if widget['wrap_label']:
            if attrs['id']:
                label_attrs = {
                    'for': attrs['id']
                }
            super().__init__(
                DjangoTextInput(widget),
                Text(widget['label']),
                **label_attrs
            )
        else:
            raise NotImplementedError
            # Use DjangoTextInput() if the label is not required.


class MuiMultipleInput(Ul):
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
                    Li(MuiInputOption(option) if option['wrap_label']
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


class MuiRadioSelect(MuiMultipleInput):
    pass


class MuiCheckboxSelectMultiple(MuiMultipleInput):
    pass


class MuiSplitDateTimeWidget(MuiMultiWidget):
    pass


class MuiSplitHiddenDateTimeWidget(MuiSplitDateTimeWidget):
    pass


class MuiSelectDateWidget(MuiMultiWidget):
    pass


class MuiButton(Button):
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
