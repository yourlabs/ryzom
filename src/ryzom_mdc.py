from django.middleware.csrf import get_token
from ryzom.html import *
from ryzom.js.renderer import JS


class MDCLink(A):
    pass


class MDCIcon(Icon):
    def __init__(self, icon, **kwargs):
        attrs = {
            'class': 'material-icons',
            'aria-hiddem': 'true'
        }

        if cls := kwargs.pop('cls', None):
            attrs['class'] += f' {cls}'
        super().__init__(icon, **attrs)


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
    def __init__(self, text, p=True, icon=None):
        black = 'black-button' if p else ''
        content = [Span(cls='mdc-button__ripple')]
        if icon and isinstance(icon, str):
            content.append(MDCIcon(icon))
        elif icon:
            content.append(icon)
        content.append(Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--outlined {black}'
        )


class MDCButton(Button):
    def __init__(self, text, p=True, disabled=False, icon=None):
        black = 'black-button' if p else ''
        attrs = {}
        if disabled:
            attrs['disabled'] = True

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
            **attrs
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
    def __init__(self, *content):
        attrs = {'class': 'mdc-notched-outline'}
        content = [
            Span(cls='mdc-notched-outline__leading'),
            Span(
                *content,
                cls='mdc-notched-outline__notch',
            ),
            Span(cls='mdc-notched-outline__trailing'),
        ]
        super().__init__(*content, **attrs)


class MDCFieldOutlined(Div):
    def __init__(self, *content, **kwargs):
        name = kwargs['name']
        input_id = f'id_{name}'
        label_id = f'id_{name}_label'
        label = kwargs.pop('label', name.capitalize())
        help_text = kwargs.pop('help_text', '')
        super().__init__(
            Label(
                MDCNotchOutline(
                    Span(
                        label,
                        id=label_id,
                        cls='mdc-floating-label',
                    ),
                ),
                *content,
                cls='mdc-text-field mdc-text-field--outlined',
                data_mdc_auto_init='MDCTextField',
            ),
            cls='form-group'
        )

    def set_error(self, error):
        helper = MDCTextFieldHelperLine(error, 'alert')
        label = self.content[0]
        label.attrs['class'] += ' mdc-text-field--invalid'
        label.attrs['aria-describedby'] = helper._id
        label.attrs['aria-controls'] = helper._id

        self.content.append(helper)


class MDCTextareaFieldOutlined(Label):
    def __init__(self, value='', label='', input_id='', label_id='', **kwargs):
        name = kwargs.get('name', '')
        if not label:
            label = name
        if name and not input_id:
            input_id = name + '_input'
        if input_id and not label_id:
            label_id = input_id + '_label'

        if label:
            label = Span(
                Span(label, cls='mdc-floating-label', id=label_id),
                cls='mdc-notched-outline__notch'),
        else:
            label = tuple()

        super().__init__(
            Span(
                Span(cls='mdc-notched-outline__leading'),
                *label,
                Span(cls='mdc-notched-outline__trailing'),
                cls='mdc-notched-outline'
            ),
            Span(
                Textarea(
                    value,
                    id=input_id,
                    cls='mdc-text-field__input',
                    **{'aria-labelledby': label_id},
                    **kwargs),
                cls='mdc-text-field__resizer'),
            cls='mdc-text-field mdc-text-field--outlined mdc-text-field--textarea',
            **{'data-mdc-auto-init': 'MDCTextField'}
        )


class MDCFormField(Div):
    attrs = {'class': 'mdc-form-field'}

    def __init__(self, *content, **kwargs):
        super().__init__(*content, **self.attrs, **kwargs)


class MDCFileInput(Div):
    def __init__(self, btn_text='', input_id='', name=''):
        self.btn = MDCButtonLabelOutlined(btn_text, False)
        self.input_id = input_id
        self.btn.attrs['for'] = input_id
        self.selected_text = Span('No file selected')
        super().__init__(
            Span(
                Input(type='file', id=input_id, name=name),
                style='display:block;width:0;height:0;overflow:hidden'
            ),
            self.selected_text,
            self.btn
        )

    def render_js(self):
        def change_event():
            def update_name(event):
                file_name = document.querySelector(input_id).value
                label = getElementByUuid(label_id)

                if file_name != '':
                    setattr(label, 'innerText', file_name)
                else:
                    setattr(label, 'innerText', 'No file selected')


            document.querySelector(input_id).addEventListener('change', update_name)

        return JS(change_event, dict(
            input_id=f'#{self.input_id}',
            label_id=self.selected_text._id,
        ))


class CSRFInput(Input):
    def __init__(self, request):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(request)
        )


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
        label.attrs['aria-describedby'] = helper._id
        label.attrs['aria-controls'] = helper._id

        self.content.append(helper)


class MDCTextFieldHelperLine(Div):
    attrs = {'aria-hidden': 'true'}

    def __init__(self, text, role, **kwargs):
        super().__init__(
            Div(
                text,
                cls='mdc-text-field-helper-text mdc-text-field-helper-text--persitent mdc-text-field-helper-text--validation-msg',
                role=role,
            ),
            cls='mdc-text-field-helper-line',
            **attrs
        )


class MDCVerticalMargin(Div):
    style = 'margin-top: 12px; margin-bottom: 12px'


class MDCList(Div):
    attrs = {'class': 'mdc-list', 'data-mdc-auto-init': 'MDCList'}


class MDCListItem(Li):
    attrs = {'class': 'mdc-list-item'}

    def __init__(self, *content, **attrs):
        super().__init__(
            Span(cls='mdc-list-item__ripple'),
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

    def render_js(self):
        return (
            '\nvar snack = function() {' +
            '\n\tvar elem = document.querySelector(".mdc-snackbar");' +
            '\n\tsn = new mdc.snackbar.MDCSnackbar(elem);' +
            '\n\tsn.open();' +
            '\n}; '
        )


class MDCCheckboxInput(Div):
    """The actual input HTML element (widget)."""
    def __init__(self, **kwargs):
        kwargs.setdefault('type', 'checkbox')
        super().__init__(
            Input(
                cls='mdc-checkbox__native-control',
                **kwargs
            ),
            Div(
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
            cls='mdc-checkbox',
        )


class MDCCheckboxField(Div):
    def __init__(self, *content, **kwargs):
        if not content:
            content = [MDCCheckboxInput(**kwargs)]

        super().__init__(
            *content,
            Label(kwargs.get('label', kwargs.get('name'))),
            cls='mdc-form-field',
        )


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

    def render_js(self):
        def events():
            def click_input(event):
                event.stopPropagation()
                elem = event.target.querySelector('input')
                if elem:
                    elem.click()

            elem = getElementByUuid(id)
            setattr(elem, 'onclick', click_input)

        return JS(events, dict(id=self._id))


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

    def render_js(self):
        def change_event():
            def update_inputs(event):
                checked = input_list.querySelectorAll('input:checked')
                unchecked = input_list.querySelectorAll('input:not(:checked)')

                def disable(elem, pos, arr):
                    setattr(elem, 'disabled', 'true')
                    list_item = document.querySelector(
                        '[data-list-item-of="' + elem.id + '"]'
                    ).classList.add('mdc-list-item--disabled')

                def enable(elem, pas, arr):
                    setattr(elem, 'disabled', undefined)
                    list_item = document.querySelector(
                        '[data-list-item-of="' + elem.id + '"]'
                    ).classList.remove('mdc-list-item--disabled')

                if checked.length >= max_choices:
                    unchecked.forEach(disable)
                else:
                    unchecked.forEach(enable)

            input_list = getElementByUuid(id)
            input_list.addEventListener('change', update_inputs)

            document.addEventListener('readystatechange', update_inputs)

        return JS(change_event, dict(id=self._id, max_choices=self.max))


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
                aria_labelledby=f'{name}-label',
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
