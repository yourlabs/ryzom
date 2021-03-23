from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from crudlfap import shortcuts as crudlfap
from ryzom_django_mdc.html import *


import django_tables2 as tables
from crudlfap.mixins import crud
from crudlfap.mixins import table


def geticon(arg):
    return getattr(arg, 'material_icon', getattr(arg, 'icon', None))


class A(A):
    attrs = dict(
        up_target='#main, .mdc-top-app-bar__title, #drawer .mdc-list',
        #up_transition='cross-fade',
    )


class PageMenu(Div):
    attrs = dict(cls='mdc-elevation--z2', style='margin-bottom: 10px')

    def to_html(self, *content, **context):
        if 'page-menu' not in context:
            return super().to_html(*content, **context)

        content = list(content)
        menu = context['page-menu']

        for v in menu:
            if v.urlname == context['view'].urlname:
                continue

            button = A(
                MDCTextButton(
                    v.label.capitalize(),
                    icon=geticon(v),
                    tag='span',
                    style=f'margin: 10px; color: {getattr(v, "color", "inherit")}',
                ),
                href=v.url,
                style='text-decoration: none',
            )
            if getattr(v, 'controller', None) == 'modal':
                button.attrs.up_modal = '.main-inner'
                del button.attrs['up-target']

            content.append(button)

        return super().to_html(
            *content,
            '<div class="mdc-elevation-overlay"></div><div class="mdc-button__ripple"></div>',
            **context,
        )



class Main(Main):
    pass


class Body(Body):
    style = 'margin: 0'

    def __init__(self, *content, **attrs):
        self.drawer = mdcDrawer(id='drawer')
        self.bar = mdcTopAppBar()
        self.main = Main(
            Div(
                *content,
                cls='main-inner',
            ),
            cls='main mdc-drawer-app-content',
            id='main',
        )
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
        'https://unpkg.com/unpoly@0.62.1/dist/unpoly.js',
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


class NarrowCard(Div):
    style = {
        'max-width': '25em',
        'margin': 'auto',
        'padding': '1em',
        'margin-top': '2em',
        'button': {
            'width': '100%',
        },
        '.MDCField label': {
            'width': '100%',
        }
    }


@template('crudlfap/form.html', App, NarrowCard)
@template('crudlfap/update.html', App, NarrowCard)
@template('crudlfap/create.html', App, NarrowCard)
@template('registration/login.html', App, NarrowCard)
class FormTemplate(Form):
    attrs = dict(
        up_target='#main, .mdc-top-app-bar__title, #drawer .mdc-list',
        method='post',
    )

    def to_html(self, view, form, **context):
        back=''
        if next_ := view.request.GET.get('next', ''):
            back = A(
                MDCButton(
                    _('Back'),
                    tag='span',
                ),
                href=next_,
            )
        return super().to_html(
            H3(view.title),
            form,
            CSRFInput(view.request),
            back,
            MDCButton(getattr(view, 'title_submit', _('Submit'))),
        )


@template('crudlfap/home.html', App)
class Home(Div):
    def to_html(self, **context):
        return super().to_html(H1('Welcome to Ryzom-CRUDLFA+'), **context)


@template('registration/logged_out.html', App, NarrowCard)
class LoggedOut(Div):
    def to_html(self, **context):
        return super().to_html(
            H1(_('Log out')),
            P(_('Thanks for spending some quality time with the Web site today.')),
            A(
                _('Log in again'),
                href=crudlfap.site.views['login'].url,
            ),
            **context,
        )


@template('crudlfap/detail.html', App, NarrowCard)
class ObjectDetail(Div):
    def to_html(self, **context):
        table = MDCDataTable()
        table.thead.attrs.style.display = 'none'
        table.table.attrs.style.width = '100%'
        table.attrs.data_mdc_auto_init = False

        for field in context['view'].display_fields:
            table.tbody.addchild(MDCDataTableTr(
                MDCDataTableTh(field['field'].verbose_name.capitalize()),
                MDCDataTableTd(field['value']),
            ))

        return super().to_html(table, **context)

    def context(self, *content, **context):
        context['page-menu'] = context['view'].router.get_menu(
            'object',
            context['view'].request,
            object=context['view'].object,
        )
        return super().context(*content, **context)


@template('crudlfap/list.html', App)
class ObjectList(Div):
    def context(self, *content, **context):
        context['page-menu'] = context['view'].router.get_menu(
            'model',
            context['view'].request,
        )
        return super().context(*content, **context)

    def to_html(self, **context):
        table_checkbox = MDCCheckboxInput()
        table_checkbox.attrs.addcls = 'mdc-data-table__header-row-checkbox'

        thead = MDCDataTableThead(tr=MDCDataTableHeaderTr(
            MDCDataTableTh(
                table_checkbox,
                addcls='mdc-data-table__header-cell--checkbox',
            )
        ))
        for column in context['view'].table.columns:
            th = MDCDataTableTh(
                wrapper=Div(
                    cls='mdc-data-table__header-cell-wrapper',
                    label=Div(
                        cls='mdc-data-table__header-cell-label',
                        style='font-weight: 500',
                        text=Text(column.header),
                    ),
                )
            )

            # sorting
            if column.orderable:
                th.attrs.addcls = 'mdc-data-table__header-cell--with-sort'
                sort = context['view'].request.GET.get('sort', '')
                if column.is_ordered:
                    th.attrs.addcls = 'mdc-data-table__header-cell--sorted'
                get = context['view'].request.GET.copy()
                get['sort'] = column.order_by_alias.next
                href = ''.join([
                    context['view'].request.path_info,
                    '?',
                    get.urlencode(),
                ])
                th.wrapper.content += [
                    A(
                        cls='mdc-icon-button material-icons mdc-data-table__sort-icon-button',
                        aria_label='Sort by dessert',
                        aria_describedby='dessert-status-label',
                        up_target='table',
                        href=href,
                        text=Text(
                            'arrow_upward'
                            if column.order_by_alias.is_descending
                            else 'arrow_downward'
                        ),
                    ),
                    Div(
                        cls='mdc-data-table__sort-status-label',
                        aria_hidden='true',
                        id='dessert-status-label',
                    ),
                ]

            thead.tr.addchild(th)
        thead.tr.content[-1].attrs.style['text-align'] = 'right'

        table = MDCDataTable(thead=thead, style='min-width: 100%; border-width: 0')
        for row in context['view'].table.paginated_rows:

            checkboxinput = MDCCheckboxInput()
            checkboxinput.attrs.addcls = 'mdc-data-table__row-checkbox'
            tr = MDCDataTableTr(
                MDCDataTableTd(
                    checkboxinput,
                    addcls='mdc-data-table__cell--checkbox',
                )
            )

            for column, cell in row.items():
                # todo: localize values
                tr.addchild(MDCDataTableTd(cell))
                # if is numeric
                #td.attrs.addcls = 'mdc-data-table__header-cell--numeric'
            table.tbody.addchild(tr)

        perpage = Div(
            Div(
                _('Rows per page'),
                cls='mdc-data-table__pagination-rows-per-page-label'
            ),
            select=MDCSelectPerPage(
                addcls='mdc-select--outlined mdc-select--no-label mdc-data-table__pagination-rows-per-page-select',
                select=Select(*[
                    Option(
                        str(i),
                        value=i,
                        selected=context['view'].table.page.paginator.per_page == i
                    )
                    for i in (3, 5, 7, 10, 25, 100)
                ])
            ),
            cls='mdc-data-table__pagination-rows-per-page',
        )

        url = '?'.join([
            context['view'].request.path_info,
            context['view'].request.GET.copy().urlencode(),
        ])

        def pageurl(n):
            get = context['view'].request.GET.copy()
            get['page'] = n
            return context['view'].request.path_info + '?' + get.urlencode()

        page = context['view'].table.page
        navigation = Div(
            Div(
                cls='mdc-data-table__pagination-total',
                text=Text(''.join([
                    str(page.start_index()),
                    '-',
                    str(page.paginator.per_page * page.number),
                    ' / ',
                    str(page.paginator.count),
                ]))
            ),
            A(
                cls='mdc-icon-button material-icons mdc-data-table__pagination-button',
                disabled=page.number == 1,
                href=pageurl(1),
                icon=Div(cls='mdc-button__icon', text=Text('first_page')),
                up_target='.mdc-data-table',
            ),
            A(
                cls='mdc-icon-button material-icons mdc-data-table__pagination-button',
                disabled=not page.has_previous(),
                icon=Div(cls='mdc-button__icon', text=Text('chevron_left')),
                href=pageurl(
                    page.number - 1
                    if page.has_previous()
                    else 1
                ),
                up_target='.mdc-data-table',
            ),
            A(
                cls='mdc-icon-button material-icons mdc-data-table__pagination-button',
                disabled=not page.has_next(),
                icon=Div(cls='mdc-button__icon', text=Text('chevron_right')),
                href=pageurl(
                    page.number + 1
                    if page.has_next()
                    else page.paginator.num_pages
                ),
                up_target='.mdc-data-table',
            ),
            A(
                cls='mdc-icon-button material-icons mdc-data-table__pagination-button',
                disabled=page.paginator.num_pages == page.number,
                icon=Div(cls='mdc-button__icon', text=Text('last_page')),
                href=pageurl(page.paginator.num_pages),
                up_target='.mdc-data-table',
            ),
            cls='mdc-data-table__pagination-navigation',
        )
        pagination = MDCDataTablePagination(
            perpage=perpage,
            navigation=navigation,
        )
        table.addchild(pagination)

        search_form = None
        if search_form := getattr(context['view'], 'search_form', None):
            search_form = InlineForm(
                search_form,
                method='get',
                action=url,
                up_autosubmit=True,
                up_delay='200ms',
                up_target='.mdc-data-table, .mdc-chip-set',
            )
            for k, v in context['view'].request.GET.items():
                if k == 'q':
                    continue
                search_form.addchild(Input(
                    name=k,
                    value=v,
                    type='hidden',
                ))

        toggle = None
        filterset = getattr(context['view'], 'filterset', None)
        if filterset and filterset.form.fields:
            toggle = MDCDrawerToggle(
                Button(
                    'filter_list',
                    cls='material-icons mdc-icon-button',
                    style='--mdc-ripple-fg-size:28px; --mdc-ripple-top:10px;',
                ),
                data_drawer_id='page-drawer',
            )
        filter_row = Div(
            toggle=toggle,
            search=search_form or '',
            chips=Div(cls='mdc-chip-set', role='grid', style='display: inline-block')
        )

        form = Form(
            method='get',
            action=url,
            up_autosubmit=True,
            up_delay='200ms',
            up_target='.mdc-drawer__content',
        )
        if 'sort' in context['view'].request.GET:
            form.addchild(Input(
                name='sort',
                value=context['view'].request.GET['sort'],
                type='hidden'
            ))
        if 'q' in context['view'].request.GET:
            form.addchild(Input(
                name='q',
                value=context['view'].request.GET['q'],
                type='hidden'
            ))
        def remove_filter_url(name):
            get = context['view'].request.GET.copy()
            if name in get:
                del get[name]
            return context['view'].request.path_info + '?' + get.urlencode()

        drawer = None
        if filterset and filterset.form.fields:
            for bf in filterset.form.visible_fields():
                filterfield = MDCFilterField(
                    label=bf.label,
                    widget=bf.to_component()
                )
                value = context['view'].request.GET.get(bf.name, '')
                if value:
                    chip = MDCChip(
                        Span(
                            role='button',
                            tabindex='0',
                            cls='mdc-chip__primary-action',
                            text=Span(
                                bf.label,
                                ': ',
                                str(bf.form.cleaned_data[bf.name]),
                                cls='mdc-chip__text',
                            ),
                        ),
                        icon=I(
                            'cancel',
                            cls='material-icons mdc-chip__icon mdc-chip__icon--trailing',
                            tabindex='-1',
                            role='button',
                        ),
                        tag='a',
                        href=remove_filter_url(bf.name),
                        up_target='main',
                    )
                    filter_row.chips.addchild(chip)
                else:
                    filterfield.widget.style.display = 'none'
                form.addchild(filterfield)

            drawer = Aside(
                MDCDrawerToggle(
                    MDCButton(_('Close'), icon='close'),
                    data_drawer_id='page-drawer',
                    style='text-align: right',
                ),
                Div(
                    form,
                    cls='mdc-drawer-app-content',
                ),
                id='page-drawer',
                cls='mdc-drawer mdc-drawer--dismissible',
                style='padding: 1em',
            )

        return super().to_html(
            drawer or '',
            PageMenu(),
            Div(
                filter_row,
                table,
                cls='mdc-drawer__content'
            ),
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


class RyzomColumn(tables.Column):
    empty_values = ()

    def __init__(self, **kwargs):
        kwargs.setdefault('default', True)
        super().__init__(**kwargs)

    def render(self, record, table, value, **kwargs):
        from crudlfap.site import site
        buttons = []
        views = site[type(record)].get_menu(
            'object',
            table.request,
            object=record
        )
        for view in views:
            button = Component(
                f'<button class="material-icons mdc-icon-button" ryzom-id="308bade28a8c11ebad3800e18cb957e9" style="color: {view.color}; --mdc-ripple-fg-size:28px; --mdc-ripple-fg-scale:1.7142857142857142; --mdc-ripple-left:10px; --mdc-ripple-top:10px;">{geticon(view)}</button>',
                title=view.title.capitalize(),
                href=view.url + '?next=' + table.request.path_info,
                style='text-decoration: none',
                tag='a',
            )
            if getattr(view, 'controller', None) == 'modal':
                button.attrs.up_modal = '.main-inner'
            else:
                button.attrs['up-target'] = A.attrs['up-target']
            buttons.append(button)
        html = Div(*buttons, style='display:flex;flex-direction:row-reverse').render()
        return mark_safe(html)


def action_column(table):
    return dict(
        crudlfap=RyzomColumn(
            verbose_name=_('Actions'),
            orderable=False,
        )
    )
table.TableMixin.get_table_meta_action_columns = action_column


def field_display(view,  name):
    value_getter = '_'.join(['get', name, 'display'])
    if hasattr(view.object, value_getter):
        return getattr(view.object, value_getter)()
    value = getattr(view.object, name)
    if hasattr(value, 'get_absolute_url'):
        return A(
            str(value),
            href=value.get_absolute_url(),
        ).render()
    return value


crud.DetailMixin.get_field_display = field_display


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
