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
        return Div(str(bf), Label(bf.label), cls='mdc-form-field')

#
#@template('django/forms/widgets/checkbox_select.html')
#class MDCCheckboxSelectMultipleWidget(Div):
#
