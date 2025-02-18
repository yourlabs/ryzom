from django.middleware.csrf import get_token
from ryzom_django.forms import widget_template, widget_templates
from ryzom_django.html import *
from ryzom_django_mdc.forms import (context_attrs, field_kwargs, widget_attrs,
                                    widget_context)

from ryzom_django.html import *
from ryzom_mdc.html import *
from ryzom_django import html as ryzom_django


class Html(ryzom_django.Html, Html):
    pass


@widget_template(
    'django/forms/widgets/input.html',
    'django/forms/widgets/date.html',
    'django/forms/widgets/time.html',
    'django/forms/widgets/datetime.html',
    'django/forms/widgets/text.html',
    'django/forms/widgets/email.html',
    'django/forms/widgets/password.html',
    'django/forms/widgets/number.html',
    'django/forms/widgets/url.html',
)
class MDCInputWidget(MDCTextFieldOutlined):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        return cls(
            Input(**attrs),
            label=bf.label,
            help_text=bf.help_text,
            errors=bf.errors,
        )


@widget_template('django/forms/widgets/date.html')
class MDCDateInputWidget(MDCInputWidget):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        attrs['type'] = 'date'
        return cls(
            Input(**attrs),
            label=bf.label,
            help_text=bf.help_text,
            errors=bf.errors,
        )


@widget_template('django/forms/widgets/checkbox.html')
class MDCCheckboxWidget(MDCCheckboxField):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        return cls(
            MDCCheckboxInput(**attrs),
            **field_kwargs(bf),
        )


@widget_template('django/forms/widgets/switch_option.html')
class MDCSwitchOption(MDCSwitch):
    def __init__(self, **attrs):
        del attrs['type']
        self.input = MDCSwitchInput(**attrs)
        super().__init__(self.input)


class MDCSwitchWidget(MDCField):
    sass = """
    .switch-field
        .inner-switch-field
            display: flex
            flex-flow: row
        label
            margin-right: 32px
    """
    def __init__(self, bf, label, **attrs):
        super().__init__(
            Div(
                Label(label, **{'for': attrs['id']}),
                MDCSwitch(MDCSwitchInput(**attrs), checked=attrs.get('checked', False)),
                cls='inner-switch-field'
            ),
            **field_kwargs(bf),
            cls='MDCField switch-field'
        )

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        del attrs['type']
        return cls(bf, bf.label, **attrs)


@widget_template('django/forms/widgets/checkbox_option.html')
class MDCCheckbox(MDCCheckboxInput):
    pass


@widget_template('django/forms/widgets/checkbox_select.html')
class MDCCheckboxSelectMultipleWidget(MDCCheckboxSelectField):
    option_template_name = 'django/forms/widgets/checkbox_option.html'

    sass = """
    .mdc-select-multiple
        display: flex
        flex-flow: column wrap
        gap: 8px

        .select-multiple-option
            display: flex
            flex-flow: row
            justify-content: space-between
            align-items: center
            margin: 8px
            gap: 8px
    """

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        choices = []
        for group, options, index in context['optgroups']:
            if group is not None:
                continue
            choices += options

        content = []
        option_template = widget_templates[cls.option_template_name]
        for choice in choices:
            choice_input = option_template(**context_attrs(choice))
            content.append(
                Div(
                    Label(choice['label'], **{'for': choice_input.input.id}),
                    choice_input,
                    cls='select-multiple-option'
                )
            )

        return cls(
            Label(bf.label),
            Div(
                *content,
                cls='mdc-select-multiple'
            ),
            **field_kwargs(bf),
        )


@widget_template('postgres/widgets/split_array.html')
@widget_template('django/forms/widgets/multiwidget.html')
class MultiWidget(CList):
    def __init__(self, **context):
        if 'widget' in context:
            subwidgets = context['widget']['subwidgets']
            temp = templates
        elif 'subwidgets' in context:
            subwidgets = context['subwidgets']
            temp = widget_templates
        else:
            subwidgets = []
            temp = {}

        super().__init__(*[
            temp[widget['template_name']](
                Input(**widget),
                label=context['label'] + f' {i}',
            ) for i, widget in enumerate(subwidgets, start=1)
        ])

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_context(bf))
        return Div(
            MDCErrorList(*bf.errors),
            cls(
                label=bf.label,
                **attrs
            )
        )


@widget_template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(MDCField):
    time_style = 'margin-bottom: 0; margin-top: 12px'
    date_style = 'margin-right: 12px; ' + time_style

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        date_context = context_attrs(context['subwidgets'][0])
        date_lead = date_context.pop('leading_icon', '')
        date_trail = date_context.pop('trailing_icon', '')
        if date_lead:
            icon = I(date_lead, cls='material-icons mdc-text-field__icon mdc-text-field__icon--leading')
        if date_trail:
            icon = I(date_trail, cls='material-icons mdc-text-field__icon mdc-text-field__icon--trailing')
        time_context = context_attrs(context['subwidgets'][1])
        return cls(
            Label(bf.label, style='display: block'),
            MDCFormField(
                MDCTextFieldOutlined(
                    Input(**date_context),
                    icon if date_lead or date_trail else None,
                    label='label' in date_context
                          and date_context['label'] or 'Date',
                    style=cls.date_style
                ),
                MDCTextFieldOutlined(
                    Input(**time_context),
                    label='label' in time_context
                          and time_context['label'] or 'Time',
                    style=cls.time_style,
                ),
                cls='split-datetime',
            ),
            **field_kwargs(bf),
        )


@widget_template('django/forms/widgets/textarea.html')
class TextareaWidget(MDCTextareaFieldOutlined):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        return cls(
            Textarea(
                attrs.pop('value', '') or '',
                aria_labelledby=f'id_{bf.html_name}_label',
                **attrs,
            ),
            label=bf.label,
            help_text=bf.help_text,
            errors=bf.errors,
        )


@widget_template('django/forms/widgets/file.html')
class FileInputWidget(MDCField):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_attrs(bf))
        if 'label' not in attrs:
            attrs['label'] = 'Select file'

        name = attrs['name']
        label = Label(bf.label, id=name + '_label_id')
        return Div(
            cls(
                label,
                MDCFileField(
                    Input(aria_labelledby=label.id, **attrs),
                    **attrs
                ),
                name=name
            ),
            MDCErrorList(*bf.errors),
        )


@widget_template('django/forms/widgets/select.html')
class SelectWidget(MDCField):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        attrs.update(widget_attrs(bf))
        context['label'] = bf.label
        return cls(
            MDCFormField(
                MDCSelectOutlined(**context),
            ),
            name=attrs['name']
        )


@widget_template('django/forms/widgets/radio.html')
class RadioSelectWidget(MDCRadio):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        attrs.update(widget_attrs(bf))
        return cls(
            bf.label,
            Input(**context)
        )


class SimpleForm(Form):
    def __init__(self, view, form):
        label = getattr(form, 'submit_label', 'submit')
        super().__init__(
            CSRFInput(view.request),
            form,
            MDCButton(label),
            method='POST')
