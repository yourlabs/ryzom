'''
Ryzom mdc (Material Design Components) components.
'''
from .components import *  # noqa


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


"""
class Component(Component):
    def __init_(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})
        super().__init_(*args, **kwargs)


class Appbar(Component):
    '''
    Appbar component

    Represents a MUI CSS <appbar>.

    :parameters: see :class:`Component`
    '''
    def __init_(self, content=None, attr=None, events=None,
                 parent='body', id=None, context=None):
        return Div(content,
                   attr={'class': "mui-appbar"},
                   events, parent, id)


class Button(Component):
    '''
    Button component

    Represents a MUI CSS <button>.

    :parameters: see :class:`Component`
    '''
    def __init_(self, content=None, attr=None,
                 events=None, parent='body', id=None, context=None):
        attr = attr or {}
        cls = attr.setdefault('class', '')
        attr['class'] = f"mui-btn {cls}"
        return Button(content, attr, events, parent, id)


class Container(Component):
    '''
    Container component

    Represents a MUI <container>.

    :parameters: see :class:`Component`
    '''
    def __init_(self, content=None, attr=None, events=None,
                 parent='body', id=None, context=None):
        return Div(content,
                   attr={'class': "mui-container"},
                   events, parent, id)
"""


class MdcForm(Component):
    '''
    Form component

    Represents a MUI CSS <form>.

    :parameters: see :class:`Component`
    '''
    def __init_(self, *content, **attrs):
        attrs = {'class': "mui-form"}
        super().__init_(*content, **attrs, tag='form')


class MdcLegend(Component):
    '''
    Legend component

    Represents a MUI CSS <legend>.

    :parameters: see :class:`Component`
    '''
    def __init_(self, *content, **attrs):
        super().__init_(*content, **attrs, tag='legend')
