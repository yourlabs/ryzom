from django.conf import settings
from django.utils.translation import ugettext as _

from crudlfap import shortcuts as crudlfap
from ryzom_django_mdc.html import *


class UpolyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Up-Location'] = request.path_info
        return response



def geticon(arg):
    return getattr(arg, 'material_icon', getattr(arg, 'icon', None))


class A(A):
    attrs = dict(
        up_target='#main, .mdc-top-app-bar__title',
        up_transition='cross-fade',
    )


class Main(Main):
    def to_html(self, *content, **context):
        buttons = []
        if 'page-menu' in context:
            menu = context['page-menu']

            for v in menu:
                if v == context['view']:
                    continue

                button = A(
                    MDCTextButton(
                        v.title.capitalize(),
                        icon=geticon(v),
                        tag='span',
                    ),
                    href=v.url,
                    style='text-decoration: none',
                )

                buttons.append(button)
        return super().to_html(*buttons, *content, *self.content, **context)


class Body(Body):
    style = 'margin: 0'

    def __init__(self, *content, **attrs):
        self.drawer = mdcDrawer(id='drawer')
        self.bar = mdcTopAppBar()
        self.main = Main(*content, cls='main mdc-drawer-app-content', id='main')
        self.debug = settings.DEBUG
        super().__init__(
            self.bar,
            Div(
                self.drawer,
                self.main,
                cls='mdc-top-app-bar--fixed-adjust',
            ),
        )

    def py2js(self):
        up.compiler('[data-mdc-auto-init]', lambda: mdc.autoInit())
        if self.debug:
            up.log.enable()


class App(Html):
    body_class = Body
    scripts = [
        'https://unpkg.com/unpoly@0.62.1/dist/unpoly.min.js',
    ]
    stylesheets = [
        'https://unpkg.com/unpoly@0.62.1/dist/unpoly.min.css',
    ]
#        self.drawer = mdcDrawer(
#            # mdcList(
#            #     *[
#            #         view.get_link('drawer')
#            #         for view in apps.Project.current().get_menu(
#            #             'global',
#            #             request=view.request
#            #         )
#            #     ],
#            #     tag='div',
#            # )
#        )


class NarrowCard(MDCCard):
    style = {
        'max-width': '25em',
        'margin': 'auto',
        'padding': '1em',
        'button': {
            'width': '100%',
        },
        '.MDCField label': {
            'width': '100%',
        }
    }


@template('crudlfap/form.html', App)
@template('crudlfap/create.html', App)
@template('registration/login.html', App, NarrowCard)
class FormTemplate(Form):
    attrs = dict(
        up_target='#main, .mdc-top-app-bar__title, #drawer .mdc-list',
        method='post',
    )

    def to_html(self, view, form, **context):
        return super().to_html(
            form,
            CSRFInput(view.request),
            MDCButton(getattr(view, 'title_submit', _('Submit'))),
        )


@template('crudlfap/home.html', App)
class Home(Div):
    def to_html(self, **context):
        return super().to_html(H1('Welcome to Ryzom-CRUDLFA+'), **context)


@template('crudlfap/detail.html', App)
class ObjectDetail(Div):
    def to_html(self, **context):
        table = Table()

        for field in context['view'].display_fields:
            table.addchild(Tr(
                Th(field['field'].verbose_name.capitalize()),
                Td(field['value']),
            ))

        return super().to_html(table, **context)


@template('crudlfap/list.html', App)
class ObjectList(Div):
    def context(self, *content, **context):
        context['page-menu'] = context['view'].router.get_menu(
            'model',
            context['view'].request,
        )
        return super().context(*content, **context)

    def to_html(self, **context):
        return super().to_html(
            MDCDataTable(),
            **context,
        )


class mdcTopAppBar(Header):
    def __init__(self, title='', buttons=None):
        self.title = title
        self.buttons = buttons or []
        super().__init__(
            Div(cls='mdc-top-app-bar__row'),
            cls='mdc-top-app-bar app-bar',
            id='app-bar',
            data_mdc_auto_init='MDCTopAppBar',
        )

    def to_html(self, view, **context):
        self.content[0].content = [Component(
            Section(
                Button(
                    'menu',
                    cls='material-icons mdc-top-app-bar__navigation-icon mdc-icon-button',
                ),
                Span(
                    view.title,
                    cls='mdc-top-app-bar__title',
                ),
                cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-start',
            ),
            cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-start',
            tag='section',
        )]
        return super().to_html(**context)

    def nav():
        window.drawer.open = not window.drawer.open

    def py2js(self):
        window.addEventListener('DOMContentLoaded', self.setup)

    def setup():
        window.drawer = mdc.drawer.MDCDrawer.attachTo(document.getElementById('drawer'))
        topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(document.getElementById('app-bar'))
        topAppBar.setScrollTarget(document.getElementById('main'))
        topAppBar.listen('MDCTopAppBar:nav', self.nav)


class mdcDrawer(Aside):
    def __init__(self, *content, **attrs):
        super().__init__(
            Div(
                *content,
                cls='mdc-drawer__content',
            ),
            cls='mdc-drawer mdc-drawer--dismissible mdc-top-app-bar--fixed-adjust' ,
            data_mdc_auto_init='MDCDrawer',
            **attrs,
        )

    def to_html(self, *content, view, **context):
        request = view.request

        content = []
        for view in crudlfap.site.get_menu('main', request):
            router = getattr(view, 'router', None)
            if view.router:
                icon = geticon(view.router)
                title = getattr(view, 'model_verbose_name', view.title)
            else:
                icon = geticon(view)
                title = getattr(view, 'title', '')

            content.append(
                A(
                    MDCListItem(title.capitalize(), icon=icon),
                    href=view.url,
                    style='text-decoration: none',
                )
            )

        return super().to_html(MDCList(*content))

class mdcAppContent(Div):
    def __init__(self, *content):
        super().__init__(
            Component(
                *content,
                tag='main',
                cls='main-content',
                id='main-content',
            ),
            cls='mdc-drawer-app-content mdc-top-app-bar--fixed-adjust',
        )


class mdcIcon(Component):
    tag = 'i'

    def __init__(self, name):
        super().__init__(
            name,
            cls='material-icons mdc-list-item__graphic',
            aria_hidden='true',
        )


class mdcList(Component):
    def __init__(self, *content, **attrs):
        attrs.setdefault('cls', '')
        attrs['cls'] += ' mdc-list'
        attrs.setdefault('tag', 'ul')
        super().__init__(*content, **attrs)

    def to_html(self, **context):
        for i, component in enumerate(self.content):
            component.attrs['tabindex'] = i
        return super().to_html(**context)


class mdcListItem(Component):
    def __init__(self, *content, icon=None, **attrs):
        attrs.setdefault('tag', 'li')
        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            mdcIcon(icon) if icon else '',
            Span(*content, cls='mdc-list-item__text'),
            cls='mdc-list-item',
            **attrs,
        )


class mdcButton(Div):
    def __init__(self, label, *args, **kwargs):
        label = label or name.capitalize()
        kwargs.setdefault('tag', 'button')
        kwargs.setdefault('cls', 'mdc-button mdc-button--touch mdc-button--raised')
        super().__init__(
            Component(
                Span(cls='mdc-button__ripple'),
                *args,
                Span(label, cls='mdc-button__label'),
                Span(cls='mdc-button__touch'),
                **kwargs,
            ),
            cls='mdc-touch-target-wrapper',
            data_mdc_auto_init='MDCRipple',
        )


class mdcTextField(Div):
    def __init__(
        self, name, label=None, value=None, type=None, errors=None, help=None,
        required=False,
    ):
        label = label or name.capitalize()
        cls = 'mdc-text-field mdc-text-field--filled'
        if errors:
            cls += ' mdc-text-field--invalid'
            help = '. '.join(errors)

        input_attrs = dict(
            name=name,
            value=value or '',
            type=type,
            aria_labelledby=f'{name}-label',
            cls='mdc-text-field__input'
        )
        if required:
            input_attrs['required'] = 'required'

        if help:
            input_attrs.update(dict(
                aria_labelledby=f'{name}_helper_id',
                aria_controls=f'{name}_helper_id',
                aria_describedby=f'{name}_helper_id',
            ))

        content = [
            Label(
                Span(cls='mdc-text-field__ripple'),
                Input(**input_attrs),
                Span(
                    label,
                    id=f'{name}-label',
                    cls='mdc-floating-label',
                ),
                Span(cls='mdc-line-ripple'),
                cls=cls,
                data_mdc_auto_init='MDCTextField',
            ),
        ]

        if help:
            content.append(Div(
                Div(
                    help,
                    cls='mdc-text-field-helper-text',
                    id=f'{name}_helper_id',
                    aria_hidden='true',
                    style='color: var(--mdc-theme-error, #b00020)',
                ),
                cls='mdc-text-field-helper-line',
            ))

        super().__init__(*content)


class mdcSwitch(Component):
    def __init__(
        self, name, label=None, value=None, type=None, errors=None, help=None,
        required=False,
    ):
        super().__init__(
            Div(
                Div(cls='mdc-switch__track'),
                Div(
                    Div(cls='mdc-switch__thumb'),
                    Input(
                        type='checkbox',
                        id='id_' + name,
                        role='switch',
                        aria_checked='true' if bool(value) else '',
                        cls='mdc-switch__native-control',
                        checked=bool(value)
                    ),
                    cls='mdc-switch__thumb-underlay',
                ),
                cls='mdc-switch mdc-switch--checked',
                data_mdc_auto_init='MDCSwitch',
            ),
            Label(
                label or name.capitalize(),
                **{'for': 'id_' + name},
            )
        )
