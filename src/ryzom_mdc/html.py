from ryzom.html import *


class MDCLink(A):
    pass


class MDCIcon(Icon):
    attrs = {
        'class': 'material-icons',
        'aria-hiddem': 'true'
    }


class MDCTextButton(Button):
    def __init__(self, text, icon=None, **kwargs):
        content = [Span(cls='mdc-button__ripple')]
        if icon:
            content.append(MDCIcon(icon))
        content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls='mdc-button',
            **kwargs,
        )


class MDCButton(Button):
    attrs = {'class': 'mdc-button'}

    def __init__(self, text=None, icon=None, **kwargs):
        if icon and isinstance(icon, str):
            content = [MDCIcon(icon)]
        elif icon:
            content = [icon]
        else:
            content = []

        content.append(Span(cls='mdc-button__ripple'))
        if text:
            content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            **kwargs
        )


class MDCButtonRaised(MDCButton):
    attrs = {'addcls': 'mdc-button--raised'}


class MDCButtonOutlined(MDCButton):
    attrs = {'addcls': 'mdc-button--outlined'}


class MDCButtonLabelOutlined(Label):
    def __init__(self, text, p=True, icon=None):
        black = 'black-button' if p else ''
        content = [Span(cls='mdc-button__ripple')]
        if icon:
            content.append(MDCIcon(icon))
        content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--outlined {black}'
        )


class MDCTextInput(Input):
    def __init__(self, name, **attrs):
        attrs['name'] = name
        attrs.setdefault('type', 'text')
        attrs.setdefault('class', 'mdc-text-field__input')
        super().__init__(**attrs)


class MDCLabel(Span):
    attrs = {'class': 'mdc-floating-label'}


class MDCTextRipple(Span):
    def __init__(self):
        super().__init__(**{'class': 'mdc-text-field__ripple'})


class MDCLineRipple(Span):
    def __init__(self):
        super().__init__(**{'class': 'mdc-line-ripple'})


class MDCTextFieldFilled(Label):
    attrs = {
        'class': 'mdc-text-field mdc-text-field--filled',
    }

    def __init__(self, label='', input_id='', label_id='', **kwargs):
        content = [
            MDCTextRipple(),
            MDCLabel(label, label_id),
            MDCTextInput(input_id, **kwargs),
            MDCLineRipple(),
        ]
        super().__init__(*content, **self.attrs)


class MDCNotchOutline(Span):
    attrs = {'class': 'mdc-notched-outline'}

    def __init__(self, *content, **attrs):
        super().__init__(
            Span(cls='mdc-notched-outline__leading'),
            Span(
                *content,
                cls='mdc-notched-outline__notch',
            ),
            Span(cls='mdc-notched-outline__trailing'),
            **attrs,
        )


class MDCField(Div):
    VERTICAL_MARGIN = '32px'
    style = f'margin-top: {VERTICAL_MARGIN}; margin_bottom: {VERTICAL_MARGIN}'

    def __init__(self, *content, name, label=None, help_text=None, value=None,
                 errors=None, **attrs):
        helper_id = f'id_{name}_helper'
        errors_id = f'id_{name}_errors'

        if errors:
            self.errors = MDCErrorList(*errors, id=errors_id)
        else:
            self.errors = ''

        if help_text:
            self.help_text = MDCHelpText(help_text, id=helper_id)
        else:
            self.help_text = ''

        super().__init__(*content, self.errors, self.help_text, **attrs)


class MDCTextFieldOutlined(MDCField):
    def __init__(self, html_input, label=None, help_text=None, errors=None, **attrs):
        self.html_input = html_input
        self.html_input.attrs.addcls = 'mdc-text-field__input'

        name = self.html_input.attrs.name
        input_id = f'id_{name}'
        label_id = f'id_{name}_label'
        helper_id = f'id_{name}_helper'
        errors_id = f'id_{name}_errors'

        floating_label = Span(label, id=label_id, cls='mdc-floating-label')
        notch_outline = MDCNotchOutline(floating_label)
        self.label = Label(
            notch_outline,
            self.html_input,
            id=label_id,
            cls='mdc-text-field mdc-text-field--outlined',
            data_mdc_auto_init='MDCTextField',
        )
        self.html_input.attrs.aria_labelledby = label_id

        value = self.html_input.attrs.get('value', '')
        if value not in ('', None):
            # float label because there is a value
            self.label.attrs.addcls = 'mdc-text-field--label-floating'
            floating_label.attrs.addcls = 'mdc-floating-label--float-above'
            notch_outline.attrs.addcls = 'mdc-notched-outline--notched'

        if errors:
            self.label.attrs.addcls = 'mdc-text-field--invalid'
            self.html_input.attrs.aria_describedby = errors_id
            self.html_input.attrs.aria_controls = errors_id
        elif help_text:
            self.html_input.attrs.aria_describedby = helper_id
            self.html_input.attrs.aria_controls = helper_id

        super().__init__(self.label, name=name,
                         help_text=help_text,
                         errors=errors, **attrs)


class MDCTextareaFieldOutlined(MDCTextFieldOutlined):
    def __init__(self, textarea, label=None, help_text=None, errors=None):
        super().__init__(
            textarea,
            label=label,
            help_text=help_text,
            errors=errors,
        )
        # decorate textarea with a resizer
        self.label.content[1] = Span(textarea, cls='mdc-text-field__resizer')
        self.label.attrs.addcls = 'mdc-text-field--textarea'


class MDCFormField(Div):
    attrs = {'class': 'mdc-form-field'}

    def __init__(self, *content, **kwargs):
        super().__init__(*content, **self.attrs, **kwargs)


class MDCFileField(Div):
    def __init__(self, html_input, label=None, help_text=None, errors=None, **attrs):
        self.btn = MDCButtonLabelOutlined(label, False)
        self.input_id = html_input.attrs['id']
        self.btn.attrs['for'] = self.input_id
        self.selected_text = Span('No file selected')
        self.label_id = self.selected_text.id
        super().__init__(
            Span(
                html_input,
                style='display:block;width:0;height:0;overflow:hidden'
            ),
            self.selected_text,
            self.btn
        )

    def set_update_name(input_id, label_id):
        def update_name(event):
            file_name = event.target.value
            label = getElementByUuid(label_id)
            label.innerHTML = file_name or 'No file selected'

        document.querySelector('#'+input_id).addEventListener('change', update_name)

    def py2js(self):
        self.set_update_name(self.input_id, self.label_id)


class MDCSplitDateTime(Div):
    def __init__(self, label='', input_id='', label_id='', **kwargs):
        name = kwargs.pop('name')
        kwargs.pop('type', None)
        value = kwargs.pop('value', None)
        date = value.date() if value else ''
        time = value.time() if value else ''

        super().__init__(
            MDCTextFieldOutlined(
                label='Date',
                input_id='date_' + name + '_input',
                name=name + '_0',
                value=date,
                type='date',
                **kwargs),
            MDCTextFieldOutlined(
                label='Time',
                input_id='time_' + name + '_input',
                name=name + '_1',
                value=time,
                type='time',
                **kwargs),
        )

    def set_error(self, error):
        helper = MDCTextFieldHelperLine(error, 'alert')
        label = self.content[1]
        label.attrs['class'] += ' mdc-text-field--invalid'
        label.attrs['aria-describedby'] = helper.id
        label.attrs['aria-controls'] = helper.id

        self.content.append(helper)


class MDCTextFieldHelperText(Div):
    attrs = {
        'class': ' '.join([
            'mdc-text-field-helper-text',
            'mdc-text-field-helper-text--persitent',
        ]),
    }

class MDCTextFieldHelperLine(Div):
    attrs = {
        'aria-hidden': 'true',
        'cls': 'mdc-text-field-helper-line',
    }


class MDCVerticalMargin(Div):
    style = 'margin-top: 18px; margin-bottom: 18px'


class MDCList(Div):
    attrs = {'class': 'mdc-list', 'data-mdc-auto-init': 'MDCList'}


class MDCListItem(Li):
    attrs = {'class': 'mdc-list-item'}

    def __init__(self, *content, icon=None, ripple=True, **attrs):
        if icon and not isinstance(icon, Component):
            icon = MDCIcon(icon, addcls='mdc-list-item__graphic')

        super().__init__(
            Span(cls='mdc-list-item__ripple') if ripple else None,
            icon,
            Span(*content, cls='mdc-list-item__text'),
            **attrs,
        )


class MDCSnackBar(Div):
    def __init__(self, msg, status='success', delay=0):
        self.delay = delay
        super().__init__(
            Div(
                Div(
                    msg,
                    cls='mdc-snackbar__label',
                    **{'aria-atomic': 'false'}
                ),
                Div(
                    Button(
                        Div(cls='mdc-button__ripple'),
                        Span('OK', cls='mdc-button__label'),
                        type='button',
                        cls='mdc-button mdc-snackbar__action'
                    ),
                    cls='mdc-snackbar__actions',
                    **{'aria-atomic': 'true'}
                ),
                cls='mdc-snackbar__surface',
                role='status',
                **{'aria-relevant': 'addition'}
            ),
            cls='mdc-snackbar',
            **{'data-mdc-auto-init': 'MDCSnackbar'}
        )

    def open_snack(elem):
        sb = new.mdc.snackbar.MDCSnackbar(elem)
        sb.open()

    def py2js(self):
        setTimeout(
            self.open_snack,
            self.delay,
            getElementByUuid(self.id)
        )


class MDCErrorListItem(Li):
    style = dict(list_style_type='none')


class MDCErrorList(Ul):
    style = dict(
        padding_left='10px',
        margin_top=0,
        margin_bottom=0,
        font_size='var(--mdc-typography-caption-font-size, 0.75rem)',
        color='var(--mdc-theme-error, #b00020)',
    )
    def __init__(self, *content, **attrs):
        super().__init__(*[
            MDCErrorListItem(c) if isinstance(c, str) else c
            for c in content
        ], **attrs)


class MDCHelpText(Div):
    style = dict(
        font_size='var(--mdc-typography-caption-font-size, 0.75rem)',
        color='rgba(0, 0, 0, 0.6)',
        padding_left='10px',
    )


class MDCInputCheckboxNativeControl(Input):
    attrs = {'class': 'mdc-checkbox__native-control'}


class MDCCheckboxInput(Div):
    """
    The actual input HTML element (widget).

    TODO: stop hijacking attrs like this because it enforces downstream
    boilerplate
    """
    def __init__(self, input=None, **attrs):
        attrs.setdefault('type', 'checkbox')
        super().__init__(
            cls='mdc-checkbox',
            input=input or MDCInputCheckboxNativeControl(**attrs),
            checkbox=Div(
                Component(
                    Component(
                        tag='path', fill='none',
                        d="M1.73,12.91 8.1,19.28 22.79,4.59",
                        cls='mdc-checkbox__checkmark-path'),
                    tag='svg', viewBox='0 0 24 24',
                    cls='mdc-checkbox__checkmark'
                ),
                Div(cls='mdc-checkbox__mixedmark'),
                cls='mdc-checkbox__background',
            ),
        )


class MDCCheckboxField(MDCField):
    def __init__(self, *content, name, label=None, help_text=None, value=None,
                 errors=None):
        super().__init__(
            MDCFormField(
                *content,
                Label(label or name.capitalize()),
            ),
            name=name,
            errors=errors,
            help_text=help_text,
        )

        # compensate for widget margin
        if self.errors:
            self.errors.attrs.style.margin_top = '-10px'
        elif self.help_text:
            self.help_text.attrs.style.margin_top = '-10px'


class MDCCheckboxSelectField(MDCField):
    def __init__(self, *content, name, label=None, help_text=None, value=None,
                 errors=None):
        super().__init__(
            *content,
            name=name,
            errors=errors,
            help_text=help_text,
        )

        # compensate for widget margin
        if self.errors:
            self.errors.attrs.style.margin_top = '-10px'
        elif self.help_text:
            self.help_text.attrs.style.margin_top = '-10px'


class MDCCheckboxListItem(Li):
    def __init__(self, title, id, checked=False, **kwargs):
        self.input_id = id
        if checked:
            kwargs['checked'] = True
        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            Span(
                Div(
                    Input(
                        id=id,
                        type='checkbox',
                        cls='mdc-checkbox__native-control',
                        **kwargs),
                    Div(
                        Component(
                            Component(
                                tag='path', fill='none',
                                d="M1.73,12.91 8.1,19.28 22.79,4.59",
                                cls='mdc-checkbox__checkmark-path'),
                            tag='svg', viewBox='0 0 24 24',
                            cls='mdc-checkbox__checkmark'),
                        Div(cls='mdc-checkbox__mixedmark'),
                        cls='mdc-checkbox__background'),
                    cls='mdc-checkbox'),
                cls='mdc-list-item__graphic'),
            Label(title, cls='mdc-list-item__text', **{'for': id}),
            cls='mdc-list-item',
            role='checkbox',
            **{
                'aria-checked': 'true' if checked else 'false',
                'data-list-item-of': id
            }
        )

    def click_input(event):
        event.stopPropagation()
        elem = event.target.querySelector('input')
        if elem:
            elem.click()

    def py2js(self):
        elem = getElementByUuid(self.id)
        elem.onclick = self.click_input


class MDCMultipleChoicesCheckbox(Ul):
    def __init__(self, name, choices, n=1, **kwargs):
        self.max = n
        alabel = kwargs.pop('aria-label', 'Label')
        super().__init__(
            *(MDCCheckboxListItem(
                title,
                f'{name}_input_{i}',
                name=name,
                value=value,
                **kwargs
            ) for i, title, value in choices),
            cls='mdc-list',
            role='group',
            **{'aria-label': alabel}
        )

    def update_inputs(event):
        input_list = event.currentTarget
        checked = input_list.querySelectorAll('input:checked')
        unchecked = input_list.querySelectorAll('input:not(:checked)')

        def disable(elem, pos, arr):
            elem.disabled = True
            list_item = document.querySelector(
                '[data-list-item-of="' + elem.id + '"]'
            ).classList.add('mdc-list-item--disabled')

        def enable(elem, pas, arr):
            elem.disabled = undefined
            list_item = document.querySelector(
                '[data-list-item-of="' + elem.id + '"]'
            ).classList.remove('mdc-list-item--disabled')

        if checked.length >= self.max:
            unchecked.forEach(disable)
        else:
            unchecked.forEach(enable)

    def py2js(self):
        input_list = getElementByUuid(self.id)
        input_list.max = self.max
        input_list.addEventListener('change', self.update_inputs)


class MDCSelect(Div):
    attrs = {'class': 'mdc-select mdc-select--filled', 'data-mdc-auto-init': 'MDCSelect'}

    def __init__(self, select, *content, **attrs):
        super().__init__(
            '''
            <div class="mdc-select__anchor" role="button" aria-haspopup="listbox"
                  aria-labelledby="demo-pagination-select" tabindex="0">
              <span class="mdc-select__selected-text-container">
                <span id="demo-pagination-select" class="mdc-select__selected-text">10</span>
              </span>
              <span class="mdc-select__dropdown-icon">
                <svg
                    class="mdc-select__dropdown-icon-graphic"
                    viewBox="7 10 10 5">
                  <polygon
                      class="mdc-select__dropdown-icon-inactive"
                      stroke="none"
                      fill-rule="evenodd"
                      points="7 10 12 15 17 10">
                  </polygon>
                  <polygon
                      class="mdc-select__dropdown-icon-active"
                      stroke="none"
                      fill-rule="evenodd"
                      points="7 15 12 10 17 15">
                  </polygon>
                </svg>
              </span>
              <span class="mdc-notched-outline mdc-notched-outline--notched">
                <span class="mdc-notched-outline__leading"></span>
                <span class="mdc-notched-outline__trailing"></span>
              </span>
            </div>

            <div class="mdc-select__menu mdc-menu mdc-menu-surface mdc-menu-surface--fullwidth" role="listbox">
              <ul class="mdc-list">
            ''',
            *[
                f'''
                <li class="mdc-list-item {'mdc-list-item--selected" aria-selected="true' if option.attrs.get('selected', False) else ''}" role="option" data-value="{option.attrs.value}">
                  <span class="mdc-list-item__text">{option.attrs.value}</span>
                </li>
                '''
                for option in select.content
            ],
            '''
              </ul>
            </div>
            ''',
            **attrs,
        )


class MDCOption(Li):
    def __init__(self, index, **choice):
        extra_attrs = dict()

        selected = choice.get('selected', False)
        if selected:
            extra_attrs['addcls'] = 'mdc-list-item--selected'
            extra_attrs['aria-selected'] = 'true'

        if index == '0':
            extra_attrs['tabindex'] = 0

        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            Span(
                choice['label'] if choice['value'] else '',
                cls='mdc-list-item__text'
            ),
            data_value=choice['value'],
            cls='mdc-list-item',
            role='option',
            **extra_attrs,
        )


class MDCNamedOptgroup(Div):
    def __init__(self, name, choices):
        super().__init__(
            Ul(
                H6(name, cls='mdc-list-group__subheader'),
                *(MDCOption(**choice) for choice in choices),
                cls='mdc-list'
            ),
            cls='mdc-list-group'
        )


class MDCOptgroup(CList):
    def __init__(self, name, choices, index):
        if name:
            super().__init__(MDCNamedOptgroup(name, choices))
        else:
            super().__init__(
                *(MDCOption(**choice) for choice in choices)
            )


class MDCSelectAnchor(Div):
    def __init__(self, label, selected=None, **attrs):
        required = attrs.pop('required', None)

        super().__init__(
            Span(
                Span(cls='mdc-notched-outline__leading'),
                Span(
                    label,
                    cls='mdc-notched-outline__notch'),
                Span(cls='mdc-notched-outline__trailing'),
                cls='mdc-notched-outline'),
            Span(
                selected or Span(cls='mdc-select__selected-text'),
                cls='mdc-select__selected-text-container'),
            Span(
                Svg(
                    Polygon(
                        stroke='none',
                        fill_rule='evenodd',
                        points='7 10 12 15 17 10',
                        cls='mdc-select__dropdown-icon-inactive'),
                    Polygon(
                        stroke='none',
                        fill_rule='evenodd',
                        points='7 15 12 10 17 15',
                        cls='mdc-select__dropdown-icon-active'),
                    viewBox="7 10 10 5",
                    focusable="false",
                    cls='mdc-select__dropdown-icon-graphic'),
                cls='mdc-select__dropdown-icon'),
            cls='mdc-select__anchor',
            role="button",
            aria_required='true' if required else 'false',
            aria_labelled_by=label.id,
            aria_haspopup="listbox",
            aria_expanded="false",
        )


class MDCSelectMenu(Div):
    def __init__(self, optgroups, **attrs):
        super().__init__(
            Ul(
                *(
                    MDCOptgroup(group_name, group_choices, group_index)
                    for group_name, group_choices, group_index
                    in optgroups
                ),
                cls='mdc-list'
            ),
            cls='mdc-select__menu mdc-menu mdc-menu-surface mdc-menu-surface--fullwidth',
        )


class MDCSelectOutlined(Div):
    tag = 'mdc-select-outlined'

    def __init__(self, **attrs):
        attrs.pop('template_name')
        label = attrs.pop('label', attrs.get('name', None))

        cls = 'mdc-select mdc-select--outlined'
        if required := attrs.pop('required', None):
            cls += ' mdc-select--required'

        super().__init__(
            Input(
                type='hidden',
                name=attrs['name'],
                value=attrs['value'][0] if attrs['value'] else '',
            ),
            MDCSelectAnchor(
                Span(
                    label,
                    cls='mdc-floating-label'
                ),
                **dict(required=required),
            ),
            MDCSelectMenu(**attrs),
            cls=cls,
            data_mdc_auto_init='MDCSelect',
        )

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('change', this.change.bind(this))

        def change(self, event):
            hidden = this.querySelector('input[type=hidden]')
            option = this.querySelector('[aria-selected=true]')
            hidden.value = option.dataset.value


class MDCAccordionToggle(MDCListItem):
    tag = 'mdc-accordion-toggle'

    def __init__(self, *, label=None, **context):
        super().__init__(label, icon='add', **context)

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.click.bind(this))

        def click(self, event):
            section = this.parentElement
            if section.classList.contains('active'):
                section.toggle()
            else:
                section.parentElement.closeAll()
                section.open()


class MDCAccordionMenu(Div):
    tag = 'mdc-accordion-menu'

    style = dict(
        display='block',
        overflow='hidden',
        max_height='0px',
    )

    def __init__(self, *content, **context):
        super().__init__(
            *content,
            cls='MDCAccordionMenu',
            **context
        )

    class HTMLElement:
        def connectedCallback(self):
            window.addEventListener('load', this.ready.bind(this))

        def ready(self):
            max_height = this.style.maxHeight
            this.style.transition = ''
            this.close()
            this.from_px = '0px'
            if max_height and max_height != '0px':
                this.from_px = max_height
                this.open()

        def start_layout(self):
            this.style.transition = ''
            this.from_px = this.style.maxHeight
            this.style.maxHeight = 'initial'
            this.rect = this.getBoundingClientRect()

            closest = this.parentElement.closest('mdc-accordion-menu')
            if closest:
                closest.start_layout()

        def end_layout(self):
            this.style.maxHeight = self.from_px
            this.getBoundingClientRect()
            this.style.transition='max-height 0.4s ease-out'
            this.style.maxHeight = this.rect.height

            closest = this.parentElement.closest('mdc-accordion-menu')
            if closest:
                closest.end_layout()

        def open(self):
            this.start_layout()
            this.end_layout()

        def close(self):
            this.style.maxHeight = 0


class MDCAccordionSection(MDCList):
    tag = 'mdc-accordion-section'

    def __init__(self, *content, **context):
        super().__init__(
            MDCAccordionToggle(**context),
            MDCAccordionMenu(*content, **context),
            addcls='mdc-accordion',
        )

    class HTMLElement:
        def open(self):
            this.querySelector('mdc-accordion-toggle').classList.add(
                'mdc-list-item--selected'
            )
            this.classList.add('active')
            this.querySelector('mdc-accordion-menu').open()
            this.querySelector('i').innerText = 'remove'

        def close(self):
            this.querySelector('mdc-accordion-toggle').classList.remove(
                'mdc-list-item--selected'
            )
            this.classList.remove('active')
            this.querySelector('mdc-accordion-menu').close()
            this.querySelector('i').innerText = 'add'

        def toggle(self):
            if this.classList.contains('active'):
                this.close()
            else:
                this.open()


class MDCAccordion(Div):
    tag = 'mdc-accordion'

    def __init__(self, *content, **context):
        def get_content():
            for c in content[:-1]:
                yield c
                yield Hr(cls='mdc-list-divider')
            if len(content):
                yield content[-1]

        super().__init__(
            *(c for c in get_content()),
            addcls='mdc-accordion'
        )

    class HTMLElement:
        def closeAll(self):
            sections = this.querySelectorAll('mdc-accordion-section')
            for section in sections:
                section.close()


class MDCSelectPerPage(MDCSelect):
    tag = 'mdc-select-per-page'

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('MDCSelect:change', this.change.bind(this))

        async def change(self, event):
            url = new.URL(document.location)
            if url.search.indexOf('per_page=') > 0:
                search = url.search.replace(
                    new.RegExp('per_page=[^&]*'),
                    'per_page=' + event.detail.value,
                )
            else:
                search = '?per_page=' + event.detail.value

            up.visit(url.pathname + search, {target: '.mdc-data-table'})



class MDCIconButton(A):
    attrs = dict(cls='material-icons mdc-top-app-bar__navigation-icon mdc-icon-button')


class MdcTopAppBar(Component):
    """
    <header class="mdc-top-app-bar">
      <div class="mdc-top-app-bar__row">
        <section class="mdc-top-app-bar__section mdc-top-app-bar__section--align-start">
          <button class="material-icons mdc-top-app-bar__navigation-icon mdc-icon-button" aria-label="Open navigation menu">menu</button>
          <span class="mdc-top-app-bar__title">Page title</span>
        </section>
        <section class="mdc-top-app-bar__section mdc-top-app-bar__section--align-end" role="toolbar">
          <button class="material-icons mdc-top-app-bar__action-item mdc-icon-button" aria-label="Favorite">favorite</button>
          <button class="material-icons mdc-top-app-bar__action-item mdc-icon-button" aria-label="Search">search</button>
          <button class="material-icons mdc-top-app-bar__action-item mdc-icon-button" aria-label="Options">more_vert</button>
        </section>
      </div>
    </header>
    """
    tag = 'header'

    def __init__(self, *content, **context):
        action_items = context.pop('action_items', None)
        super().__init__(
            Div(
                # Navigation menu icon and page title.
                Component(
                    Button(
                        'menu',
                        aria_label="Open navigation menu",
                        cls='material-icons mdc-top-app-bar__navigation-icon mdc-icon-button',
                    ),
                    Span(
                        *content,
                        cls='mdc-top-app-bar__title',
                    ),
                    cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-start',
                    tag='section',
                ),
                # Actions items and menu.
                MdcAppBarActions(action_items=action_items),
                cls='mdc-top-app-bar__row',
            ),
            cls='mdc-top-app-bar app-bar',
            id='app-bar',
            data_mdc_auto_init='MDCTopAppBar',
            **context,
        )


class MdcDrawer(Component):
    """
    <aside class="mdc-drawer mdc-drawer--dismissible">
      <div class="mdc-drawer__header">
        <h3 class="mdc-drawer__title">Drawer/h3>
        <h6 class="mdc-drawer__subtitle">Demonstration</h6>
      </div>
      <div class="mdc-drawer__content">
        <nav class="mdc-list">
          <a class="mdc-list-item mdc-list-item--activated" href="#" aria-current="page">
            <span class="mdc-list-item__ripple"></span>
            <i class="material-icons mdc-list-item__graphic" aria-hidden="true">inbox</i>
            <span class="mdc-list-item__text">Inbox</span>
          </a>
          <a class="mdc-list-item" href="#">
            <span class="mdc-list-item__ripple"></span>
            <i class="material-icons mdc-list-item__graphic" aria-hidden="true">send</i>
            <span class="mdc-list-item__text">Outgoing</span>
          </a>
          <hr class="mdc-list-divider">
          <h6 class="mdc-list-group__subheader">Labels</h6>
          <a class="mdc-list-item" href="#">
            <span class="mdc-list-item__ripple"></span>
            <i class="material-icons mdc-list-item__graphic" aria-hidden="true">drafts</i>
            <span class="mdc-list-item__text">Drafts</span>
          </a>
        </nav>
      </div>
    </aside>
    """
    tag = 'aside'

    def __init__(self, *content, **context):
        super().__init__(
            # Header.
            Div(
                H3(
                    *context['mdc-header-title'],
                    cls="mdc-drawer__title",
                ),
                H6(
                    *context['mdc-header-subtitle'],
                    cls="mdc-drawer__subtitle",
                ),
                cls="mdc-drawer__header",
            ) if 'mdc-header-title' in context else '',
            # List.
            Div(
                *content,
                cls='mdc-drawer__content',
            ),
            cls='mdc-drawer mdc-drawer--dismissible mdc-top-app-bar--fixed-adjust',
            data_mdc_auto_init='MDCDrawer',
            **context,
        )

class MdcAppContent(Div):
    """
    <div class="mdc-drawer-app-content mdc-top-app-bar--fixed-adjust">
      <main class="main-content" id="main-content">
        App Content
      </main>
    </div>
    """
    def __init__(self, *content, **context):
        super().__init__(
            Component(
                *content,
                tag='main',
                cls='main-content',
                id='main-content',
            ),
            cls='mdc-drawer-app-content mdc-top-app-bar--fixed-adjust',
        )


class MdcDrawerHeader(Div):
    """
    <div class="mdc-drawer__header">
      <h3 id="drawer-title" class="mdc-drawer__title">Title</h3>
      <h6 id="drawer-subtitle" class="mdc-drawer__subtitle">subtitle</h6>
    </div>
    """
    def __init__(self, *content, **context):
        title = context.pop('drawer_title', '')
        subtitle = context.pop('drawer_subtitle', '')
        super().__init__(
            *content,
            H3(
                title,
                cls='mdc-drawer__title',
                id='drawer-title',
            ),
            H6(
                subtitle,
                cls='mdc-drawer__subtitle',
                id='drawer-subtitle',
            ),
            cls='mdc-drawer__header',
        )


class MdcListDivider(Text):
    """
    <hr class="mdc-list-divider">
    <h6 class="mdc-list-group__subheader">Section</h6>
    """
    def __init__(self, *content, **context):
        super().__init__(
            Hr(cls="mdc-list-divider"),
            H6(
                *content,
                cls="mdc-list-group__subheader",
                **context,
            ),
        )


class MdcIcon(Component):
    tag = 'i'

    def __init__(self, *content, **context):
        super().__init__(
            *content,
            cls='material-icons mdc-list-item__graphic',
            aria_hidden='true',
            **context,
        )


class MdcList(Component):
    """ Allow tag to be overridden via context.

    """
    def __init__(self, *content, **context):
        context.setdefault('tag', 'ul')
        context.setdefault('cls', '')
        context['cls'] = (' '.join((context['cls'], 'mdc-list'))
                          if context['cls'] else 'mdc-list')
        super().__init__(*content, **context)


class MdcNavList(MdcList):
    def __init__(self, *content, **context):
        context['tag'] = 'nav'
        super().__init__(*content, **context)


class MdcListItem(Component):
    """ MdcListItem(Text("Home"), icon='home', href='#', active=True)
    <a class="mdc-list-item mdc-list-item--activated" href="#" aria-current="page">
      <span class="mdc-list-item__ripple"></span>
      <i class="material-icons mdc-list-item__graphic" aria-hidden="true">home</i>
      <span class="mdc-list-item__text">Home</span>
    </a>
    """
    def __init__(self, *content, icon=None, **context):
        context.setdefault('tag', 'a')
        context.setdefault('aria-current', 'page')
        context.setdefault('cls', '')
        context['cls'] = (' '.join((context['cls'], 'mdc-list-item'))
                          if context['cls'] else 'mdc-list-item')
        if context.pop('active', None):
            context['cls'] += ' mdc-list-item--activated'
            context['tabindex'] = 0
        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            MdcIcon(icon) if icon else '',
            Span(*content, cls='mdc-list-item__text'),
            **context,
        )


class MdcAppBarActions(Component):
    def __init__(self, *content, **context):
        action_items = context.pop('action_items', None)
        if not action_items:
            super().__init__()
        else:
            context['tag'] = 'section'
            super().__init__(
                *[Button(
                    item[0],  # icon
                    aria_label=item[1],  # label
                    href=item[2],
                    cls='material-icons mdc-top-app-bar__action-item mdc-icon-button',
                ) for item in action_items],
                cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-end',
                role='toolbar',
                **context,
            )


class MdcButton(Div):
    def __init__(self, label=None, name=None, *content, **context):
        label = label or (name and name.capitalize())
        context.setdefault('tag', 'button')
        context.setdefault('cls', '')
        context['cls'] += 'mdc-button mdc-button--touch mdc-button--raised'
        super().__init__(
            # TODO: What tag here? Context?
            Component(
                Span(cls='mdc-button__ripple'),
                *content,
                Span(label, cls='mdc-button__label'),
                Span(cls='mdc-button__touch'),
                **context,
            ),
            cls='mdc-touch-target-wrapper',
            data_mdc_auto_init='MDCRipple',
        )


class MdcTextField(Label):
    """
    <label class="mdc-text-field mdc-text-field--filled mdc-text-field--label-floating">
      <span class="mdc-text-field__ripple"></span>
      <input class="mdc-text-field__input" type="text" aria-labelledby="my-label-id" value="Initial value">
      <span class="mdc-floating-label mdc-floating-label--float-above" id="my-label-id">
        Label in correct place
      </span>
      <span class="mdc-line-ripple"></span>
    </label>
    """
    def __init__(self, name=None, label=None, value=None, **context):
        label = label or (name and name.capitalize()) or ''
        super().__init__(
            Span(cls='mdc-text-field__ripple'),
            Input(
                name=name,
                value=value or '',
                type='text',
                aria_labelledby=f'id_{name}-label',
                cls='mdc-text-field__input',
                **context,
            ),
            Span(
                Text(label),
                id=f'{name}-label',
                cls='mdc-floating-label',
            ),
            Span(cls='mdc-line-ripple'),
            cls='mdc-text-field mdc-text-field--filled',
            data_mdc_auto_init='MDCTextField',
        )


class MDCLayoutGrid(Div):
    attrs = {'class': 'mdc-layout-grid'}


class MDCLayoutGridInner(Div):
    attrs = {'class': 'mdc-layout-grid__inner'}


class MDCLayoutGridCell(Div):
    attrs = {'class': 'mdc-layout-grid__cell'}


class MDCCard(Div):
    attrs = {'class': 'mdc-card'}


class MDCDataTable(Div):
    attrs = {'class': 'mdc-data-table', 'data-mdc-auto-init': 'MDCDataTable'}

    def __init__(self, *content, container=None, table=None,
            tbody=None, thead=None, **attrs):

        super().__init__(
            container=container or MDCDataTableContainer(
                table=table or MDCDataTableTable(
                    thead=thead,
                    tbody=tbody,
                )
            ),
            **attrs,
        )
        self.table = self.container.table
        self.tbody = self.table.tbody
        self.thead = self.table.thead


class MDCDataTableResponsive(MDCDataTable):
    sass = '''
    @media (max-width: 700px)
        .MDCDataTableResponsive
            thead
                display: none
            tr
                display: block
            td
                display: block
                text-align: right
                height: auto
            td:before
                content: attr(data-label)
                float: left
                font-weight: bold
    '''


class MDCDataTableTable(Table):
    attrs = {'class': 'mdc-data-table__table'}

    def __init__(self, *content, thead=None, tbody=None, **attrs):
        super().__init__(
            *content,
            thead=thead or MDCDataTableThead(),
            tbody=tbody or MDCDataTableTbody(),
            **attrs,
        )

    def to_html(self, *content, **context):
        self.attrs.arial_label = context['view'].title
        return super().to_html(*content, **context)



class MDCDataTableTbody(Tbody):
    attrs = {'class': 'mdc-data-table__content'}


class MDCDataTableThead(Thead):
    def __init__(self, *content, tr=None, **attrs):
        super().__init__(*content, tr=tr or MDCDataTableTr(), **attrs)


class MDCDataTableTh(Th):
    attrs = {
        'class': 'mdc-data-table__header-cell',
        'role': 'columnheader',
        'scope': 'col',
    }


class MDCDataTableHeaderTr(Tr):
    attrs = {'class': 'mdc-data-table__header-row'}


class MDCDataTableTr(Tr):
    attrs = {'class': 'mdc-data-table__row'}


class MDCDataTableTd(Td):
    attrs = {'class': 'mdc-data-table__cell'}


thead = '''
      <th
        class="mdc-data-table__header-cell mdc-data-table__header-cell--with-sort"
        role="columnheader"
        scope="col"
        aria-sort="none"
        data-column-id="dessert"
      >
        <div class="mdc-data-table__header-cell-wrapper">
          <div class="mdc-data-table__header-cell-label">
            Dessert
          </div>
          <button class="mdc-icon-button material-icons mdc-data-table__sort-icon-button"
                  aria-label="Sort by dessert" aria-describedby="dessert-status-label">arrow_upward</button>
          <div class="mdc-data-table__sort-status-label" aria-hidden="true" id="dessert-status-label">
          </div>
        </div>
      </th>
      <th
        class="mdc-data-table__header-cell mdc-data-table__header-cell--numeric mdc-data-table__header-cell--with-sort mdc-data-table__header-cell--sorted"
        role="columnheader"
        scope="col"
        aria-sort="ascending"
        data-column-id="carbs"
      >
        <div class="mdc-data-table__header-cell-wrapper">
          <button class="mdc-icon-button material-icons mdc-data-table__sort-icon-button"
                  aria-label="Sort by carbs" aria-describedby="carbs-status-label">arrow_upward</button>
          <div class="mdc-data-table__header-cell-label">
            Carbs (g)
          </div>
          <div class="mdc-data-table__sort-status-label" aria-hidden="true" id="carbs-status-label"></div>
        </div>
      </th>
      <th
        class="mdc-data-table__header-cell mdc-data-table__header-cell--numeric mdc-data-table__header-cell--with-sort"
        role="columnheader"
        scope="col"
        aria-sort="none"
        data-column-id="protein"
      >
        <div class="mdc-data-table__header-cell-wrapper">
          <button class="mdc-icon-button material-icons mdc-data-table__sort-icon-button"
                  aria-label="Sort by protein" aria-describedby="protein-status-label">arrow_upward</button>
          <div class="mdc-data-table__header-cell-label">
            Protein (g)
          </div>
          <div class="mdc-data-table__sort-status-label" aria-hidden="true" id="protein-status-label"></div>
        </div>
      </th>
      <th
        class="mdc-data-table__header-cell"
        role="columnheader"
        scope="col"
        data-column-id="comments"
      >
        Comments
      </th>
      '''

tbody  = '''
    <tbody class="mdc-data-table__content">
      <tr data-row-id="u0" class="mdc-data-table__row">
        <td class="mdc-data-table__cell mdc-data-table__cell--checkbox">
          <div class="mdc-checkbox mdc-data-table__row-checkbox">
            <input type="checkbox" class="mdc-checkbox__native-control" aria-labelledby="u0"/>
            <div class="mdc-checkbox__background">
              <svg class="mdc-checkbox__checkmark" viewBox="0 0 24 24">
                <path class="mdc-checkbox__checkmark-path" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59" />
              </svg>
              <div class="mdc-checkbox__mixedmark"></div>
            </div>
            <div class="mdc-checkbox__ripple"></div>
          </div>
        </td>
      <td class="mdc-data-table__cell">Frozen yogurt</td>
      <td class="mdc-data-table__cell mdc-data-table__cell--numeric">
        20
      </td>
      <td class="mdc-data-table__cell mdc-data-table__cell--numeric">
        4.0
      </td>
      <td class="mdc-data-table__cell">Super tasty</td>
      </tr>
      <tr data-row-id="u0" class="mdc-data-table__row">
        <td class="mdc-data-table__cell mdc-data-table__cell--checkbox">
          <div class="mdc-checkbox mdc-data-table__row-checkbox">
            <input type="checkbox" class="mdc-checkbox__native-control" aria-labelledby="u0"/>
            <div class="mdc-checkbox__background">
              <svg class="mdc-checkbox__checkmark" viewBox="0 0 24 24">
                <path class="mdc-checkbox__checkmark-path" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59" />
              </svg>
              <div class="mdc-checkbox__mixedmark"></div>
            </div>
            <div class="mdc-checkbox__ripple"></div>
          </div>
        </td>
      <td class="mdc-data-table__cell">Frozen yogurt</td>
      <td class="mdc-data-table__cell mdc-data-table__cell--numeric">
        24
      </td>
      <td class="mdc-data-table__cell mdc-data-table__cell--numeric">
        4.0
      </td>
      <td class="mdc-data-table__cell">Super tasty</td>
      </tr>
    </tbody>
        '''

class MDCDataTableContainer(Div):
    attrs = {'class': 'mdc-data-table__table-container'}

    def __init__(self, *content, table=None, **attrs):
        return super().__init__(
            table=table or MDCDataTableTable(),
            **attrs,
        )


class MDCDrawerToggle(Component):
    tag = 'mdc-drawer-toggle'

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.toggle.bind(this))

        def toggle(self):
            drawer = document.getElementById(this.attributes['data-drawer-id'].value)
            drawer = mdc.drawer.MDCDrawer.attachTo(drawer)
            drawer.open = not drawer.open


class ToggleNextElement(Component):
    tag = 'toggle-element'
    style = {
        ' svg': {
            'transition': 'all 0.5s ease',
        },
        '.open svg': {
            'transform': 'rotate(180deg)',
        }
    }

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.click.bind(this))

        def click(self, event):
            element = this.nextElementSibling
            if element.style.display == 'none':
                element.style.display = 'block'
                this.classList.add('open')
            else:
                element.style.display = 'none'
                this.classList.remove('open')


class MDCFilterField(Component):
    style = {
        ' h3': {
            'display': 'flex',
            'justify-content': 'space-between',
        }
    }

    def __init__(self, label=None, widget=None, **attrs):
        super().__init__(
            label=ToggleNextElement(
                H3(
                    Span(label),
                    Component(
                        '<g><path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z"></path> <path d="M0 0h24v24H0z" fill="none"></path></g><svg>',
                        tag='svg',
                        width='26',
                        height='26',
                        viewBox='0 0 26 26',
                        role='presentation',
                        xmlns='http://www.w3.org/2000/svg',
                        cls='gc-icon gc-icon--expand',
                    ),
                ),
            ),
            widget=Div(
                widget,
                style={'transition': 'all 1s ease'},
            ),
            **attrs,
        )

    @classmethod
    def from_boundfield(cls, bf):
        return cls(
            label=bf.label,
            field=bf.to_component(),
        )


class MDCDataTablePagination(Div):
    attrs = {'class': 'mdc-data-table__pagination'}
    sass = '''
    @media (max-width: 700px)
        .MDCDataTablePagination [slot]
            display: block
    '''


class MDCDialogContainer(Div):
    attrs = {'class': 'mdc-dialog__container'}


class MDCDialogTitle(H2):
    attrs = {'class': 'mdc-dialog__title'}


class MDCDialogActions(Div):
    attrs = {'class': 'mdc-dialog__actions'}


class MDCDialogContent(Div):
    attrs = {'class': 'mdc-dialog__content'}


class MDCDialogSurface(Div):
    def __init__(self, title, content, actions=None, **attrs):
        extra_attrs = {}

        _title = MDCDialogTitle(title)
        _content = MDCDialogContent(content)
        _actions = actions

        if _actions is None:
            _actions = MDCDialogActions(
                    MDCDialogCloseButtonOutlined('cancel'),
                    MDCDialogAcceptButton('confirm'),
                    style='display: flex; justify-content: space-around'
                )

        super().__init__(
            _title,
            _content,
            _actions,
            cls='mdc-dialog__surface',
            role='alertdialog',
            aria_modal='true',
            aria_labelledby=_title.id,
            aria_describedby=_content.id
        )


class MDCDialogCloseButton(MDCButton):
    tag = 'a'
    attrs = {'data-mdc-dialog-action': 'close'}


class MDCDialogCloseButtonOutlined(MDCButtonOutlined):
    tag = 'a'
    attrs = {'data-mdc-dialog-action': 'close'}


class MDCDialogAcceptButton(MDCButtonRaised):
    tag = 'a'
    attrs = {'data-mdc-dialog-action': 'accept'}


class MDCDialogAcceptButtonOutlined(MDCButtonOutlined):
    tag = 'a'
    attrs = {'data-mdc-dialog-action': 'accept'}


class MDCDialogScrim(Div):
    attrs = {'class': 'mdc-dialog__scrim'}


class MDCDialog(Div):
    tag = 'mdc-dialog'
    attrs = {
        'class': 'mdc-dialog',
        'data-mdc-auto-init': 'MDCDialog'
    }

    def __init__(self, *content, **attrs):
        actions = attrs.pop('actions', None)
        super().__init__(
            MDCDialogContainer(
                MDCDialogSurface(*content, actions=actions)
            ),
            MDCDialogScrim(),
            **attrs
        )

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('MDCDialog:closing', self.handle_closing.bind(this))
            this.addEventListener('MDCDialog:closed', self.handle_closed.bind(this))
            this.addEventListener('MDCDialog:opening', self.handle_opening.bind(this))
            this.addEventListener('MDCDialog:opened', self.handle_opened.bind(this))

        def onclosing(self, event):
            pass

        def onclosed(self, event):
            pass

        def onopening(self, event):
            pass

        def onopened(self, event):
            pass

        def open(self):
            this.MDCDialog.open()

        def close(self):
            this.MDCDialog.close()

        def layout(self):
            this.MDCDialog.layout()

        def handle_closing(self, event):
            this.onclosing(event)

        def handle_closed(self, event):
            this.onclosed(event)

        def handle_opening(self, event):
            this.onopening(event)

        def handle_opened(self, event):
            this.onopened(event)


class MDCChip(Div):
    attrs = {'class': 'mdc-chip', 'role': 'row'}

    def __init__(self, *content, icon=None, **attrs):
        super().__init__(
            MDCChipRipple(),
            Gridcell(*content),
            icon=Gridcell(icon) if icon else '',
            **attrs
        )


class MDCChipRipple(Div):
    attrs = {'class': 'mdc-chip__ripple'}


class Gridcell(Span):
    attrs = {'role': 'gridcell'}


class InlineForm(Form):
    style = {
        'display': 'inline-block',
        ' .MDCField': {
            'display': 'inline-block',
        },
    }


class Body(Body):
    attrs = {'class': 'mdc-typography'}

    def py2js(self):
        mdc.autoInit()


class Html(Html):
    scripts = [
        'https://unpkg.com/material-components-web@10.0.0/dist/material-components-web.min.js',
        'https://unpkg.com/@webcomponents/webcomponentsjs@2.0.0/webcomponents-bundle.js',
        'https://cdn.polyfill.io/v2/polyfill.min.js',
        '/static/py2js.js',
    ]
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css?family=Roboto:300,400,500',
        'https://unpkg.com/material-components-web@10.0.0/dist/material-components-web.min.css',
    ]
    body_class = Body
