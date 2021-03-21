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


class MDCButtonOutlined(Button):
    def __init__(self, text, p=True, icon=None, **kwargs):
        black = 'black-button' if p else ''
        content = [Span(cls='mdc-button__ripple')]
        if icon and isinstance(icon, str):
            content.append(MDCIcon(icon))
        elif icon:
            content.append(icon)
        content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--outlined {black}',
            **kwargs
        )


class MDCButton(Button):
    def __init__(self, text, p=True, icon=None, **kwargs):
        black = 'black-button' if p else ''

        if icon and isinstance(icon, str):
            content = [MDCIcon(icon)]
        elif icon:
            content = [icon]
        else:
            content = []

        content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--raised {black}',
            **kwargs
        )


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

    def __init__(self, *content, icon=None, **attrs):
        if icon and not isinstance(icon, Component):
            icon = MDCIcon(icon, addcls='mdc-list-item__graphic')

        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            icon or '',
            Span(*content, cls='mdc-list-item__text'),
            **attrs,
        )


class MDCSnackBar(Div):
    def __init__(self, msg, status='success'):
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


    def py2js(self):
        elem = getElementByUuid(self.id)
        sb = new.mdc.snackbar.MDCSnackbar(elem)
        sb.open()


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
    """The actual input HTML element (widget)."""
    def __init__(self, **attrs):
        attrs.setdefault('type', 'checkbox')
        super().__init__(
            cls='mdc-checkbox',
            input=MDCInputCheckboxNativeControl(**attrs),
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
        input_list = event.target
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
        input_list.addEventListener('change', self.update_inputs)


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
            return ''
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

    def __init__(self, *content, container=None, pagination=None, table=None,
            tbody=None, thead=None, **attrs):

        super().__init__(
            container=container or MDCDataTableContainer(
                table=table or MDCDataTableTable(
                    thead=thead,
                    tbody=tbody,
                )
            ),
            pagination=pagination or MDCDataTablePagination(),
            **attrs,
        )
        self.table = self.container.table
        self.tbody = self.table.tbody
        self.thead = self.table.thead


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
    pass



class MDCDataTableThead(Thead):
    def __init__(self, *content, tr=None, **attrs):
        super().__init__(*content, tr=tr or MDCDataTableTr(), **attrs)

    def content_html(self, *content, **context):
        for tr in content:
            tr.attrs.addcls = 'mdc-data-table__header-row'
        return super().content_html(*content, **context)


class MDCDataTableTh(Th):
    attrs = {
        'class': 'mdc-data-table__header-cell',
        'role': 'columnheader',
        'scope': 'col',
    }


class MDCDataTableTr(Tr):
    def __init__(self, *content, checkbox=None, **context):
        if checkbox is not None:
            self.checkbox = MDCCheckboxInput()
            self.checkbox.attrs.addcls = 'mdc-data-table__header-row-checkbox'
            if checkbox:
                self.checkbox.attrs.addcls = 'mdc-checkbox--selected'

            self.checkboxcol = MDCDataTableTh(
                self.checkbox,
                addcls='mdc-data-table__header-cell--checkbox',
            )
            content = [self.checkboxcol] + list(content)
        super().__init__(*content, **context)


class MDCDataTableTd(Td):
    pass


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


class MDCDataTablePagination(Div):
    attrs = {'class': 'mdc-data-table__table-pagination'}

    def to_html(self, *content, **context):
        return super().to_html('''
  <div class="mdc-data-table__pagination-trailing">
    <div class="mdc-data-table__pagination-rows-per-page">
      <div class="mdc-data-table__pagination-rows-per-page-label">
        Rows per page
      </div>

      <div class="mdc-select mdc-select--outlined mdc-select--no-label mdc-data-table__pagination-rows-per-page-select">
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
            <li class="mdc-list-item mdc-list-item--selected" aria-selected="true" role="option" data-value="10">
              <span class="mdc-list-item__text">10</span>
            </li>
            <li class="mdc-list-item" role="option" data-value="25">
              <span class="mdc-list-item__text">25</span>
            </li>
            <li class="mdc-list-item" role="option" data-value="100">
              <span class="mdc-list-item__text">100</span>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="mdc-data-table__pagination-navigation">
      <div class="mdc-data-table__pagination-total">
        1‑10 of 100
      </div>
      <button class="mdc-icon-button material-icons mdc-data-table__pagination-button" data-first-page="true" disabled>
        <div class="mdc-button__icon">first_page</div>
      </button>
      <button class="mdc-icon-button material-icons mdc-data-table__pagination-button" data-prev-page="true" disabled>
        <div class="mdc-button__icon">chevron_left</div>
      </button>
      <button class="mdc-icon-button material-icons mdc-data-table__pagination-button" data-next-page="true">
        <div class="mdc-button__icon">chevron_right</div>
      </button>
      <button class="mdc-icon-button material-icons mdc-data-table__pagination-button" data-last-page="true">
        <div class="mdc-button__icon">last_page</div>
      </button>
    </div>
  </div>
        ''')


class Body(Body):
    attrs = {'class': 'mdc-typography'}

    def py2js(self):
        mdc.autoInit()


class Html(Html):
    scripts = [
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js',
        '/static/py2js.js',
    ]
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap',
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css',
    ]
    body_class = Body
