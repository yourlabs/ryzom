from django.middleware.csrf import get_token
from ryzom_django.forms import widget_template
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
    'django/forms/widgets/text.html',
    'django/forms/widgets/email.html',
    'django/forms/widgets/password.html',
    'django/forms/widgets/number.html',
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


@widget_template('django/forms/widgets/checkbox_select.html')
class MDCCheckboxSelectMultipleWidget(MDCCheckboxSelectField):
    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        choices = []
        for group, options, index in context['optgroups']:
            if group is not None:
                continue
            choices += options

        return cls(
            Label(bf.label),
            *[
                Div(
                    MDCFormField(
                        MDCCheckboxInput(**context_attrs(choice)),
                        Label(choice['label'])
                    )
                )
                for choice in choices
            ],
            **field_kwargs(bf),
        )


@widget_template('django/forms/widgets/multiwidget.html')
class MultiWidget(CList):
    def __init__(self, **context):
        super().__init__(*[
            templates[widget['template_name']](**widget)
            for widget in context['widget']['subwidgets']
        ])

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        attrs.update(widget_context(bf))
        return Div(
            Label(bf.label),
            cls(**attrs),
            cls='mdc-form-field'
        )


@widget_template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(MDCField):
    time_style = 'margin-bottom: 0; margin-top: 12px'
    date_style = 'margin-right: 12px; ' + time_style

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        context = widget_context(bf)
        date_context = context_attrs(context['subwidgets'][0])
        time_context = context_attrs(context['subwidgets'][1])
        return cls(
            Label(bf.label, style='display: block'),
            MDCFormField(
                MDCTextFieldOutlined(
                    Input(**date_context),
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

        return cls(
            Label(bf.label),
            MDCFileField(
                Input(**attrs),
                **attrs
            ),
            name=attrs['name']
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


class SimpleForm(Form):
    def __init__(self, view, form):
        label = getattr(form, 'submit_label', 'submit')
        super().__init__(
            CSRFInput(view.request),
            form,
            MDCButton(label),
            method='POST')
