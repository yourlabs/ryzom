from ryzom_django.html import *
from ryzom_mdc import *


def context_attrs(context, **extra):
    attrs = dict()
    attrs.update(context['widget']['attrs'])
    attrs.update(dict(
        name=context['widget']['name'],
        value=context['widget']['value'],
    ))
    attrs.update(extra)
    return attrs


@template('django/forms/widgets/input.html')
@template('django/forms/widgets/text.html')
class MDCInputWidget(Input):
    def __init__(self, **context):
        attrs = context_attrs(
            context,
            cls='mdc-text-field__input'
        )
        super().__init__(**attrs)

    @classmethod
    def factory(cls, bf):
        bf.field.widget.attrs['aria-labelledby'] = f'id_{bf.name}_label'
        return MDCFieldOutlined(
            str(bf),
            name=bf.name,
            label=bf.label,
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
        return MDCCheckboxField(str(bf), label=bf.label)


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
        return Div(Div(Label(bf.label), str(bf), cls='mdc-form-field'), cls='form-group')
