from ryzom_django_mdc.html import *


class ActionButton(A):
    """Single bound view rendered as a navigation link or Unpoly modal trigger.

    Reads view.label, view.url, view.icon, view.color, view.controller.
    When controller == 'modal', opens in an Unpoly overlay and wires _next
    so the opener refreshes on success.
    """

    def __init__(self, view, _next=None, _next_destructible=False, **attrs):
        href = view.url
        extra = {}

        if getattr(view, 'controller', None) == 'modal':
            extra['up_layer'] = 'new'
            dangerous = _next_destructible and getattr(view, 'destructive', False)
            if dangerous:
                next_url = str(view.router['list'].url)
                extra['up_on_accepted'] = f'up.visit("{next_url}")'
            else:
                next_url = _next
            if next_url:
                sep = '&' if '?' in href else '?'
                href = href + sep + '_next=' + str(next_url)
                extra['up_accept_location'] = str(next_url)
        else:
            extra['up_target'] = 'body'

        super().__init__(
            MDCTextButton(
                view.label.capitalize(),
                icon=getattr(view, 'icon', None),
                tag='span',
                style={
                    'margin': '10px',
                    'color': getattr(view, 'color', 'inherit'),
                },
            ),
            href=href,
            style='text-decoration: none',
            **extra,
            **attrs,
        )


class ActionMenu(Div):
    """Row of ActionButtons for a single permission-scoped menu.

    Pass the views list already filtered by has_perm() — this component
    renders all of them except the one matching current_urlname.
    """
    attrs = {'class': 'mdc-elevation--z2', 'style': 'margin-bottom: 10px'}

    def __init__(self, views, current_urlname=None, _next=None,
                 _next_destructible=False, **attrs):
        buttons = [
            ActionButton(view, _next=_next, _next_destructible=_next_destructible)
            for view in views
            if getattr(view, 'urlname', None) != current_urlname
        ]
        super().__init__(*buttons, **attrs)


class ActionDropdown(Component):
    """Per-row action menu.

    One action → plain ActionButton.
    Multiple actions → icon-button that opens an MDC dropdown menu.
    """

    def __init__(self, views, _next=None, _next_destructible=False, **attrs):
        views = list(views)

        if not views:
            super().__init__(**attrs)

        elif len(views) == 1:
            super().__init__(
                ActionButton(views[0], _next=_next,
                             _next_destructible=_next_destructible),
                **attrs,
            )

        else:
            items = [
                MDCListItem(
                    A(
                        getattr(v, 'label', '').capitalize(),
                        href=v.url,
                        style='text-decoration: none; color: inherit; display: block',
                        up_target='body',
                    ),
                )
                for v in views
            ]
            super().__init__(
                Button(
                    MDCIcon('more_vert'),
                    cls='mdc-icon-button action-dropdown__toggle',
                    type='button',
                    aria_label='Actions',
                ),
                MDCMenu(*items),
                **attrs,
            )

    class HTMLElement:
        def connectedCallback(self):
            window.addEventListener('load', this.init.bind(this))

        def init(self):
            btn = this.querySelector('.action-dropdown__toggle')
            menu_el = this.querySelector('mdc-menu')
            if btn and menu_el:
                btn.addEventListener('click', this.toggle.bind(this))
                document.addEventListener('click', this.closeIfOutside.bind(this))

        def toggle(self, event):
            menu_el = this.querySelector('mdc-menu')
            if menu_el:
                menu_el.classList.toggle('mdc-menu-surface--open')

        def closeIfOutside(self, event):
            if not this.contains(event.target):
                menu_el = this.querySelector('mdc-menu')
                if menu_el:
                    menu_el.classList.remove('mdc-menu-surface--open')
