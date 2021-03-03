from ryzom_django.html import *
from ryzom_mdc import *
from ryzom_django.forms import field_kwargs, widget_attrs, widget_context


@template('django/forms/widgets/input.html')
@template('django/forms/widgets/date.html')
@template('django/forms/widgets/time.html')
@template('django/forms/widgets/text.html')
@template('django/forms/widgets/email.html')
@template('django/forms/widgets/password.html')
class MDCInputWidget(Input):
    attrs = {'class': 'mdc-text-field__input'}

    @classmethod
    def from_boundfield(cls, bf):
        attrs = {'aria-labelledby': f'id_{bf.name}_label'}

        helper_id = f'id_{bf.name}_helper'
        if bf.errors or bf.help_text:
            attrs['aria-controls'] = helper_id
            attrs['aria-describedby'] = helper_id

        return MDCFieldOutlined(
            cls(**widget_attrs(bf, attrs)),
            **field_kwargs(bf),
        )


@template('django/forms/widgets/checkbox.html')
class MDCCheckboxWidget(MDCCheckboxInput):
    @classmethod
    def from_boundfield(cls, bf):
        return MDCCheckboxField(
            cls(**widget_attrs(bf)),
            **field_kwargs(bf),
        )


@template('django/forms/widgets/checkbox_select.html')
class MDCCheckboxSelectMultipleWidget(Div):
    def __init__(self, **context):
        group_content = []
        for group, options, index in context['optgroups']:
            option_content = []
            for option in options:
                option_content.append(
                    MDCCheckboxField(
                        MDCCheckboxInput(**option),
                        name=option['name'],
                    )
                    if option['wrap_label']
                    else MDCTextInput(**option)
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
        super().__init__(*group_content)

    @classmethod
    def from_boundfield(cls, bf):
        return MDCField(
            Label(bf.label),
            cls(**widget_context(bf)),
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
class SplitDateTimeWidget(CList):
    def __init__(self, **context):
        date_widget = context['subwidgets'][0]
        time_widget = context['subwidgets'][1]
        super().__init__(
            MDCVerticalMargin(
                MDCFieldOutlined(
                    templates[date_widget['template_name']](**date_widget),
                    name=date_widget['name'],
                    label='Date',
                ),
            ),
            MDCVerticalMargin(
                MDCFieldOutlined(
                    templates[time_widget['template_name']](**time_widget),
                    name=time_widget['name'],
                    label='Time',
                ),
            ),
        )

    @classmethod
    def from_boundfield(cls, bf):
        return MDCField(
            Label(bf.label),
            cls(**widget_context((bf))),
            **field_kwargs(bf),
        )
