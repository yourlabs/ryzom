from ryzom_django.forms import widget_template

from django.utils.safestring import mark_safe
from ryzom_django_mdc.html import *
from ryzom_django_mdc.forms import (context_attrs, field_kwargs, widget_attrs,
                                    widget_context)
from ryzom.contrib.django import Static


Html.stylesheets = Html.stylesheets + [Static('autocomplete_light/autocomplete-light.css')]
Html.scripts = Html.scripts + [Static('autocomplete_light/autocomplete-light.js')]


class AutocompleteSelectInput(Component):
    pass


class AutocompleteSelect(Component):
    pass


class PlaceholderRemover(MDCTextFieldOutlined):
    class HTMLElement:
        def connectedCallback(self):
            this.setup()

        def setup(self):
            if not this.input:
                this.input = this.querySelector('input')
                this.field = this.querySelector('label')

                if this.input and this.field:
                    this.input.addEventListener('focus', this.focus.bind(this))
                    this.input.addEventListener('blur', this.blur.bind(this))

        def focus(self, event):
            this.setup()
            event.target.value = ''

        def blur(self, event):
            this.setup()
            if event and event.target:
                event.target.value = ''
                this.field.MDCTextField.foundation.deactivateFocus()


@widget_template('django/forms/widgets/select.html')
class SelectWidget(Component):
    sass = '''
    select-widget
        input
            border: 0
            outline: 0

        input:focus
            outline: none !important

    '''

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        bf.field.widget.attrs['slot'] = 'select'

        kwargs = {}
        if bf.field.widget.attrs.get('multiple', None):
            kwargs['multiple'] = True

        mdc_field = PlaceholderRemover(
            MDCTextInput(
                slot='input',
                name=f'{bf.name}-autocomplete',
            ),
            Div(slot='deck', style='padding: 4px'),
            label=bf.label,
        )
        mdc_field.label.attrs.addcls = 'mdc-text-field--textarea'
        mdc_field.label.style['align-items'] = 'baseline'
        return cls(
            MDCField(
                AutocompleteSelect(
                    bf.field.widget.render(bf.name, bf.value()),
                    AutocompleteSelectInput(
                        mdc_field,
                        MDCHelpText(
                            bf.help_text,
                        ),
                        **kwargs,
                    ),
                ),
                name=bf.name,
            )
        )
