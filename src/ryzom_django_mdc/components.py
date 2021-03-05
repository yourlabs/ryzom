from ryzom_django.html import *
from ryzom_mdc import *
from ryzom_django.forms import field_kwargs, context_attrs, widget_attrs, widget_context


@template('django/forms/widgets/input.html')
@template('django/forms/widgets/date.html')
@template('django/forms/widgets/time.html')
@template('django/forms/widgets/text.html')
@template('django/forms/widgets/email.html')
@template('django/forms/widgets/password.html')
class MDCInputWidget(MDCTextFieldOutlined):
    @classmethod
    def from_boundfield(cls, bf):
        return cls(
            Input(**widget_attrs(bf)),
            label=bf.label,
            help_text=bf.help_text,
            errors=bf.errors,
        )


@template('django/forms/widgets/checkbox.html')
class MDCCheckboxWidget(MDCCheckboxField):
    @classmethod
    def from_boundfield(cls, bf):
        return cls(
            MDCCheckboxInput(**widget_attrs(bf)),
            **field_kwargs(bf),
        )


@template('django/forms/widgets/checkbox_select.html')
class MDCCheckboxSelectMultipleWidget(MDCCheckboxSelectField):
    @classmethod
    def from_boundfield(cls, bf):
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


@template('django/forms/widgets/multiwidget.html')
class MultiWidget(CList):
    def __init__(self, **context):
        super().__init__(*[
            templates[widget['template_name']](**widget)
            for widget in context['widget']['subwidgets']
        ])

    @classmethod
    def from_boundfield(cls, bf):
        return Div(
            Label(bf.label),
            cls(**widget_context((bf))),
            cls='mdc-form-field'
        )


@template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(MDCField):
    @classmethod
    def from_boundfield(cls, bf):
        context = widget_context(bf)
        style = 'margin-bottom: 0; margin-top: 12px'
        return cls(
            Label(bf.label),
            MDCFormField(
                MDCTextFieldOutlined(
                    Input(**context_attrs(context['subwidgets'][0])),
                    label='Date',
                    style='margin-right: 12px; ' + style,
                ),
                MDCTextFieldOutlined(
                    Input(**context_attrs(context['subwidgets'][1])),
                    label='Time',
                    style=style,
                ),
            ),
            **field_kwargs(bf),
        )


@template('django/forms/widgets/textarea.html')
class TextareaWidget(MDCTextareaFieldOutlined):
    @classmethod
    def from_boundfield(cls, bf):
        attrs = widget_attrs(bf)
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
