from ryzom_django.html import *
from ryzom_mdc import *


def context_attrs(context, **extra):
    # extract attrs from a widget context
    attrs = dict()
    attrs.update(context['widget']['attrs'])
    attrs.update(dict(
        name=context['widget']['name'],
        value=context['widget']['value'],
        type=context['widget']['type']
    ))
    attrs.update(extra)
    return attrs


def widget_context(bf, attrs=None):
    # copy of BoundField.as_widget() with get_context instead of widget.render()
    widget = bf.field.widget
    if bf.field.localize:
        widget.is_localized = True
    attrs = attrs or {}
    attrs = bf.build_widget_attrs(attrs, widget)
    if bf.auto_id and 'id' not in widget.attrs:
        attrs.setdefault('id', bf.auto_id)
    return widget.get_context(
        name=bf.html_name,
        value=bf.value(),
        attrs=attrs,
    )


@template('django/forms/widgets/input.html')
@template('django/forms/widgets/date.html')
@template('django/forms/widgets/time.html')
@template('django/forms/widgets/text.html')
@template('django/forms/widgets/email.html')
@template('django/forms/widgets/password.html')
class MDCInputWidget(Input):
    def __init__(self, **context):
        super().__init__(**context_attrs(
            context,
            cls='mdc-text-field__input'
        ))

    @classmethod
    def factory(cls, bf):
        attrs = {'aria-labelledby': f'id_{bf.name}_label'}

        helper_id = f'id_{bf.name}_helper'
        if bf.errors or bf.help_text:
            attrs['aria-controls'] = helper_id
            attrs['aria-describedby'] = helper_id

        return MDCFieldOutlined(
            cls(**widget_context(bf, attrs)),
            name=bf.name,
            label=bf.label,
            value=bf.value(),
            help_text=bf.help_text,
            errors=bf.form.error_class(bf.errors),
        )


@template('django/forms/widgets/checkbox.html')
class MDCCheckboxWidget(MDCCheckboxInput):
    def __init__(self, **context):
        attrs = context_attrs(context, type='checkbox')
        super().__init__(**attrs)

    @classmethod
    def factory(cls, bf):
        return MDCCheckboxField(cls(**widget_context(bf)), label=bf.label)


@template('django/forms/widgets/checkbox_select.html')
class MDCCheckboxSelectMultipleWidget(MDCList):
    def __init__(self, **context):
        group_content = []
        for group, options, index in context['widget']['optgroups']:
            option_content = []
            for option in options:
                option_content.append(
                    MDCListItem(
                        MDCCheckboxField(**option),
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
    def factory(cls, bf):
        return Div(Label(bf.label), str(bf))


@template('django/forms/widgets/multiwidget.html')
class MultiWidget(CList):
    def __init__(self, **context):
        super().__init__(*[
            templates[widget['template_name']](widget=widget)
            for widget in context['widget']['subwidgets']
        ])

    @classmethod
    def factory(cls, bf):
        return Div(Label(bf.label), cls(**widget_context((bf))), cls='mdc-form-field')


@template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(CList):
    def __init__(self, **context):
        date_widget = context['widget']['subwidgets'][0]
        time_widget = context['widget']['subwidgets'][1]
        super().__init__(
            MDCVerticalMargin(
                MDCFieldOutlined(
                    templates[date_widget['template_name']](widget=date_widget),
                    name=date_widget['name'],
                    label='Date',
                ),
            ),
            MDCVerticalMargin(
                MDCFieldOutlined(
                    templates[time_widget['template_name']](widget=time_widget),
                    name=time_widget['name'],
                    label='Time',
                ),
            ),
        )

    @classmethod
    def factory(cls, bf):
        return Div(Label(bf.label), cls(**widget_context((bf))))
