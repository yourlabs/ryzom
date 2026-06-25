from types import SimpleNamespace

from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.text import capfirst
from django.views import View

from ryzom_django_mdc.html import *


# ---------------------------------------------------------------------------
# Tier 2 — Permission-aware navigation primitives
# ---------------------------------------------------------------------------

class ActionButton(A):
    """Single bound view rendered as a plain navigation link."""

    def __init__(self, view, **attrs):
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
            href=view.url,
            style='text-decoration: none',
            **attrs,
        )


class ModalLayer(Component):
    """Open a confirm/destructive action in an MDCDialog instead of navigating.

    Renders a trigger button plus a pre-rendered ``MDCDialog`` whose form POSTs
    straight to the action URL; on success the server redirects and the page
    reloads. Replaces the former Unpoly ``up-layer`` mechanism — no AJAX.
    """
    tag = 'modal-layer'

    def __init__(self, view, request=None, _next=None, _next_destructible=False,
                 **attrs):
        label = view.label.capitalize()
        color = getattr(view, 'color', 'inherit')

        # A destructive action launched from the object's own page can't return
        # to a now-deleted object — send it to the list instead.
        dangerous = _next_destructible and getattr(view, 'destructive', False)
        next_url = str(view.router['list'].url) if dangerous else _next

        super().__init__(
            Span(
                MDCTextButton(
                    label,
                    icon=getattr(view, 'icon', None),
                    tag='span',
                    style={'margin': '10px', 'color': color},
                ),
                cls='modal-layer__trigger',
                style='cursor: pointer',
            ),
            MDCDialog(
                f'{label}?',
                Form(
                    P(f'Are you sure you want to {view.label.lower()} this?'),
                    CSRFInput(request) if request is not None else None,
                    Input(type='hidden', name='_next', value=next_url)
                    if next_url else None,
                    Div(
                        MDCButton(
                            'Cancel', tag='button', type='button',
                            data_mdc_dialog_action='close',
                        ),
                        MDCButtonRaised(
                            label, tag='button', type='submit',
                            style=f'background: {color}',
                        ),
                        cls='mdc-dialog__actions',
                        style='display: flex; justify-content: space-around; gap: 1em',
                    ),
                    method='post',
                    action=view.url,
                ),
                actions=Span(),
            ),
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            trigger = this.querySelector('.modal-layer__trigger')
            if trigger:
                trigger.addEventListener('click', this.open.bind(this))

        def open(self, event):
            event.preventDefault()
            dialog = this.querySelector('mdc-dialog')
            if dialog:
                dialog.open()


def _action_surface(view, request=None, _next=None, _next_destructible=False):
    """Pick the surface for a bound view: modal → ModalLayer, else a link."""
    if getattr(view, 'controller', None) == 'modal':
        return ModalLayer(view, request=request, _next=_next,
                          _next_destructible=_next_destructible)
    return ActionButton(view)


class ActionMenu(Div):
    """Row of action surfaces for a single permission-scoped menu."""
    attrs = {'class': 'mdc-elevation--z2', 'style': 'margin-bottom: 10px'}

    def __init__(self, views, current_urlname=None, request=None, _next=None,
                 _next_destructible=False, **attrs):
        buttons = [
            _action_surface(view, request=request, _next=_next,
                            _next_destructible=_next_destructible)
            for view in views
            if getattr(view, 'urlname', None) != current_urlname
        ]
        super().__init__(*buttons, **attrs)


class ActionDropdown(Component):
    """Per-row action menu: one action → button; many → icon-button + dropdown."""

    def __init__(self, views, request=None, _next=None, _next_destructible=False,
                 **attrs):
        views = list(views)

        if not views:
            super().__init__(**attrs)

        elif len(views) == 1:
            super().__init__(
                _action_surface(views[0], request=request, _next=_next,
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
            if document.readyState == 'complete':
                this.init()
            else:
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


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

class NarrowCard(Div):
    style = {
        'max-width': '95vw',
        'margin': 'auto',
        'padding': '1em',
        'margin-top': '2em',
    }


class FormContainer(Div):
    style = {
        'max-width': '580px',
        'margin': 'auto',
    }
    sass = '''
    .FormContainer
        .mdc-text-field, .mdc-form-field, .mdc-select, form
            width: 100%
            max-width: 90vw
    '''


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _field_label(field_name):
    return capfirst(field_name.replace('_', ' '))


def _field_value(obj, field_name):
    value = getattr(obj, field_name, '')
    if callable(value):
        value = value()
    return '' if value is None else str(value)


def _url_replace(request, **new_params):
    """Return request path with updated query params. Drops 'page' unless set."""
    params = request.GET.copy()
    for k, v in new_params.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    params.pop('page', None)
    qs = params.urlencode()
    return request.path + ('?' + qs if qs else '')


def _url_drop(request, *drop_keys):
    """Return URL with specified keys removed, page reset."""
    params = request.GET.copy()
    for k in drop_keys:
        params.pop(k, None)
    params.pop('page', None)
    qs = params.urlencode()
    return request.path + ('?' + qs if qs else '')


# ---------------------------------------------------------------------------
# Tier 1 — CRUD screen components
# ---------------------------------------------------------------------------

class SortableHeader(MDCDataTableTh):
    """Column header that cycles sort: none → asc → desc → none."""

    def __init__(self, field_name, request, **attrs):
        sort = request.GET.get('sort', '')
        label = _field_label(field_name)

        if sort == field_name:
            next_sort = f'-{field_name}'
            sort_icon = MDCIcon('arrow_upward',
                                style='font-size:14px;vertical-align:middle;margin-left:2px')
        elif sort == f'-{field_name}':
            next_sort = None  # drop sort
            sort_icon = MDCIcon('arrow_downward',
                                style='font-size:14px;vertical-align:middle;margin-left:2px')
        else:
            next_sort = field_name
            sort_icon = None

        url = _url_replace(request, sort=next_sort)

        super().__init__(
            A(label, href=url,
              style='text-decoration:none;color:inherit;cursor:pointer'),
            sort_icon,
            **attrs,
        )


class SearchBar(Div):
    """Free-text search; submits on Enter (single text input) with a full reload."""

    style = {'margin': '8px 0'}

    def __init__(self, request, **attrs):
        q = request.GET.get('q', '')
        preserved = {k: v for k, v in request.GET.items() if k not in ('q', 'page')}
        hidden = [Input(type='hidden', name=k, value=v) for k, v in preserved.items()]

        super().__init__(
            Form(
                MDCTextFieldOutlined(
                    Input(type='search', name='q', value=q or ''),
                    label='Search',
                ),
                *hidden,
                action=request.path,
                method='get',
                style='display:flex;align-items:center',
            ),
            **attrs,
        )


class FilterChips(Div):
    """Chips for active filters; clicking a chip removes that filter."""

    style = {'display': 'flex', 'flex-wrap': 'wrap', 'gap': '4px', 'margin': '4px 0'}

    def __init__(self, active_filters, request, **attrs):
        chips = [
            A(
                MDCChip(
                    f'{_field_label(field)}: {value}',
                    ticon=MDCIcon('cancel', style='font-size:16px'),
                ),
                href=_url_drop(request, f'f_{field}'),
                style='text-decoration:none',
            )
            for field, value in active_filters.items()
        ]
        super().__init__(*chips, **attrs)


class FilterDrawer(Div):
    """Collapsible filter panel; applies via its submit button (full reload)."""

    style = {'margin': '8px 0'}

    def __init__(self, router, request, **attrs):
        filter_fields = getattr(router, 'filter_fields', None) or []
        preserved = {
            k: v for k, v in request.GET.items()
            if k not in [f'f_{f}' for f in filter_fields] + ['page']
        }
        hidden = [Input(type='hidden', name=k, value=v) for k, v in preserved.items()]

        inputs = []
        for field_name in filter_fields:
            from django.db.models import BooleanField as _BF
            val = request.GET.get(f'f_{field_name}', '')
            try:
                field_obj = router.model._meta.get_field(field_name)
                is_bool = isinstance(field_obj, _BF)
            except Exception:
                is_bool = False

            if is_bool:
                inputs.append(
                    Div(
                        Label(_field_label(field_name),
                              style='display:block;font-size:12px;margin-bottom:2px'),
                        Select(
                            Option('Any', value=''),
                            Option('Yes', value='true',
                                   selected='selected' if val == 'true' else None),
                            Option('No', value='false',
                                   selected='selected' if val == 'false' else None),
                            name=f'f_{field_name}',
                            style='padding:4px;border:1px solid #ccc;border-radius:4px',
                        ),
                        style='margin:4px',
                    )
                )
            else:
                inputs.append(
                    MDCTextFieldOutlined(
                        Input(type='text', name=f'f_{field_name}', value=val or ''),
                        label=_field_label(field_name),
                        style='margin:4px',
                    )
                )

        form = Form(
            *inputs,
            *hidden,
            MDCButton('Apply', tag='button', type='submit',
                      style='margin:4px;align-self:flex-end'),
            action=request.path,
            method='get',
            style='display:flex;flex-wrap:wrap;gap:8px;padding:8px 0;align-items:flex-end',
        )

        super().__init__(
            ToggleNextElement(
                Button(
                    MDCIcon('filter_list'),
                    ' Filters',
                    cls='mdc-button',
                    type='button',
                ),
            ),
            Div(form, style='display:none'),
            **attrs,
        )


class Pagination(Div):
    """First/prev/next/last navigation + per-page links."""

    style = {
        'display': 'flex',
        'align-items': 'center',
        'justify-content': 'flex-end',
        'padding': '8px 0',
        'gap': '4px',
        'font-size': '13px',
    }

    def __init__(self, page, request, **attrs):
        paginator = page.paginator
        current = page.number
        total_pages = paginator.num_pages
        total_count = paginator.count
        per_page = paginator.per_page

        start = (current - 1) * per_page + 1
        end = min(current * per_page, total_count)

        def page_link(icon, n, disabled):
            style = 'display:inline-flex;align-items:center;padding:4px;'
            if disabled:
                return Span(MDCIcon(icon, style='font-size:20px'),
                            style=style + 'opacity:0.35;cursor:default')
            params = request.GET.copy()
            params['page'] = n
            url = request.path + '?' + params.urlencode()
            return A(MDCIcon(icon, style='font-size:20px'), href=url,
                     style=style + 'text-decoration:none;color:inherit;cursor:pointer')

        per_page_options = [10, 25, 50, 100]

        super().__init__(
            Span(f'{start}–{end} of {total_count}',
                 style='margin:0 8px;white-space:nowrap'),
            page_link('first_page', 1, not page.has_previous()),
            page_link('chevron_left', current - 1, not page.has_previous()),
            page_link('chevron_right', current + 1, not page.has_next()),
            page_link('last_page', total_pages, not page.has_next()),
            Span('|', style='margin:0 4px;opacity:0.4'),
            Span('Rows:', style='white-space:nowrap'),
            *[
                A(
                    str(n),
                    href=_url_replace(request, per_page=str(n)),
                    style=(
                        'margin:0 3px;text-decoration:none;font-weight:bold'
                        if n == per_page else
                        'margin:0 3px;text-decoration:none;opacity:0.6'
                    ),
                )
                for n in per_page_options
            ],
            **attrs,
        )


class BulkActionBar(Component):
    """Hidden bar of bulk actions; appears when rows are selected."""

    tag = 'bulk-action-bar'
    style = {
        'padding': '8px 12px',
        'background': 'var(--mdc-theme-primary-light, #e8f4fd)',
        'border': '1px solid var(--mdc-theme-primary, #6200ee)',
        'border-radius': '4px',
        'margin-top': '8px',
        'display': 'flex',
        'gap': '8px',
        'align-items': 'center',
    }

    def __init__(self, list_actions, **attrs):
        buttons = [
            A(
                MDCButton(getattr(v, 'label', '').capitalize(), tag='span'),
                href=v.url,
                data_base_href=v.url,
                style='text-decoration:none',
            )
            for v in list_actions
        ]
        super().__init__(
            Span('Selected:', style='font-size:13px;margin-right:4px'),
            *buttons,
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.setup()
            else:
                window.addEventListener('load', this.setup.bind(this))

        def setup(self):
            this.style.display = 'none'
            parent = this.parentElement
            if parent:
                parent.addEventListener('change', this.onSelectionChange.bind(this))

        def onSelectionChange(self, event):
            if event.target.type != 'checkbox':
                return
            if not event.target.dataset.pk:
                return
            parent = this.parentElement
            checked = parent.querySelectorAll('input[type="checkbox"][data-pk]:checked')
            if checked.length > 0:
                this.style.display = 'flex'
                pks = ''
                i = 0
                while i < checked.length:
                    if pks:
                        pks = pks + ','
                    pks = pks + checked[i].dataset.pk
                    i = i + 1
                links = this.querySelectorAll('a[data-base-href]')
                j = 0
                while j < links.length:
                    base = links[j].getAttribute('data-base-href')
                    if base.indexOf('?') >= 0:
                        links[j].href = base + '&pks=' + pks
                    else:
                        links[j].href = base + '?pks=' + pks
                    j = j + 1
            else:
                this.style.display = 'none'


class TableRow(MDCDataTableTr):
    """One data table row: optional checkbox, field cells, per-row ActionDropdown."""

    def __init__(self, obj, fields, row_actions=None, _next=None,
                 show_checkbox=False, request=None, **attrs):
        cells = []
        if show_checkbox:
            cells.append(MDCDataTableTd(
                MDCCheckboxInput(data_pk=str(obj.pk)),
                style='width:1px',
            ))
        cells += [
            MDCDataTableTd(_field_value(obj, f), data_label=_field_label(f))
            for f in fields
        ]
        cells.append(MDCDataTableTd(
            ActionDropdown(row_actions or [], request=request, _next=_next),
            style='text-align:right',
        ))
        super().__init__(*cells, **attrs)


class ObjectList(Div):
    """List page: ActionMenu, optional search/filter, sortable table, pagination."""

    def __init__(self, router, request, queryset=None, **attrs):
        fields = (router.get_table_fields()
                  if callable(getattr(router, 'get_table_fields', None))
                  else router.table_fields)

        # --- Queryset pipeline ---
        qs = queryset if queryset is not None else router.get_queryset(None)

        # Search
        from django.db.models import Q as _Q, BooleanField as _BF
        search_fields = getattr(router, 'search_fields', None) or []
        q = request.GET.get('q', '').strip()
        if q and search_fields:
            filt = _Q()
            for sf in search_fields:
                filt |= _Q(**{f'{sf}__icontains': q})
            qs = qs.filter(filt)

        # Per-field filters
        filter_fields = getattr(router, 'filter_fields', None) or []
        active_filters = {}
        for ff in filter_fields:
            val = request.GET.get(f'f_{ff}', '').strip()
            if not val:
                continue
            try:
                field_obj = router.model._meta.get_field(ff)
                if isinstance(field_obj, _BF):
                    bool_val = val.lower() in ('true', '1', 'yes')
                    qs = qs.filter(**{ff: bool_val})
                else:
                    qs = qs.filter(**{f'{ff}__icontains': val})
                active_filters[ff] = val
            except Exception:
                pass

        # Sort
        sort = request.GET.get('sort', '')
        if sort:
            sort_field = sort.lstrip('-')
            if sort_field in fields:
                qs = qs.order_by(sort)

        # Paginate
        try:
            per_page = min(max(int(request.GET.get('per_page', '25')), 1), 200)
        except (ValueError, TypeError):
            per_page = 25
        try:
            page_num = max(int(request.GET.get('page', '1')), 1)
        except (ValueError, TypeError):
            page_num = 1
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page_num)

        # --- Build table ---
        model_actions = router.get_menu('model', request)
        list_actions = router.get_menu('list_action', request)
        show_checkbox = bool(list_actions)

        header_cells = []
        if show_checkbox:
            header_cells.append(MDCDataTableTh('', style='width:1px'))
        header_cells += [SortableHeader(f, request) for f in fields]
        header_cells.append(MDCDataTableTh('Actions', style='text-align:right'))

        thead = MDCDataTableThead(tr=MDCDataTableHeaderTr(*header_cells))
        table = MDCDataTableResponsive(
            thead=thead,
            style={'min-width': '100%', 'border-width': 0},
        )

        for obj in page_obj:
            row_actions = router.get_menu('object', request, object=obj)
            table.tbody.addchild(
                TableRow(obj, fields, row_actions, request=request,
                         _next=request.path, show_checkbox=show_checkbox)
            )

        # --- Assemble list body ---
        body = []

        if search_fields:
            body.append(SearchBar(request))

        if filter_fields:
            body.append(FilterDrawer(router, request))

        if active_filters:
            body.append(FilterChips(active_filters, request))

        body.append(
            Div(table, cls='mdc-drawer__content', style='overflow-y:unset')
        )
        body.append(Pagination(page_obj, request))

        if list_actions:
            body.append(BulkActionBar(list_actions))

        super().__init__(
            ActionMenu(model_actions, request=request, _next=request.path),
            Div(*body),
            **attrs,
        )


class ObjectDetail(Div):
    """Detail page: field→value table + object-level ActionMenu."""

    def __init__(self, router, request, obj, **attrs):
        if callable(getattr(router, 'get_detail_fields', None)):
            fields = router.get_detail_fields()
        else:
            fields = getattr(router, 'detail_fields', None) or router.table_fields

        table = MDCDataTable()
        table.thead.attrs.style = 'display: none'
        table.table.attrs.style = 'width: 100%'
        table.attrs['data-mdc-auto-init'] = 'false'

        for field in fields:
            value = _field_value(obj, field)
            # Link to get_absolute_url for related objects (ForeignKey values)
            try:
                related = getattr(obj, field)
                if related and hasattr(related, 'get_absolute_url'):
                    value = A(str(related), href=related.get_absolute_url())
            except Exception:
                pass
            table.tbody.addchild(MDCDataTableTr(
                MDCDataTableTh(_field_label(field)),
                MDCDataTableTd(value),
            ))

        object_actions = router.get_menu('object', request, object=obj)

        super().__init__(
            ActionMenu(
                object_actions,
                request=request,
                _next=request.path,
                _next_destructible=True,
            ),
            NarrowCard(table),
            NarrowCard(HistoryList(obj)),
            **attrs,
        )


class ObjectForm(FormContainer):
    """Create / update form page: title + Django form + CSRF + _next + submit."""

    def __init__(self, view, form, **attrs):
        request = view.request
        _next = request.GET.get('_next', request.POST.get('_next', ''))

        back = None
        if next_ := request.GET.get('next', ''):
            back = A(MDCButton('Back', tag='span'), href=next_)

        super().__init__(
            H3(getattr(view, 'title', '')),
            Form(
                form,
                CSRFInput(request),
                Input(type='hidden', name='_next', value=_next) if _next else None,
                back,
                MDCButtonRaised(
                    getattr(view, 'title_submit', 'Submit'),
                    tag='button',
                    type='submit',
                ),
                method='post',
                action=request.path_info,
            ),
            **attrs,
        )


# ---------------------------------------------------------------------------
# Full-page document — used by Router views
# ---------------------------------------------------------------------------

class CRUDDocument(Html):
    """Full-page document. Navigation is plain server-rendered (no Unpoly)."""


# ---------------------------------------------------------------------------
# Tier 0 — App shell: Messages, TopAppBar, NavDrawer, App
# ---------------------------------------------------------------------------

class Messages(Component):
    """Django flash messages rendered as auto-fading toasts."""

    tag = 'app-messages'
    sass = '''
app-messages
    position: fixed
    bottom: 16px
    left: 50%
    transform: translateX(-50%)
    z-index: 9997
    display: flex
    flex-direction: column
    gap: 8px
    align-items: center
    pointer-events: none
.app-message
    background: #323232
    color: #fff
    padding: 12px 24px
    border-radius: 4px
    font-size: 14px
    box-shadow: 0 3px 6px rgba(0,0,0,.3)
    opacity: 0
    animation: msgFadeInOut 4s ease forwards
    pointer-events: auto
.app-message--success
    background: #388e3c
.app-message--error
    background: #c62828
.app-message--warning
    background: #f57f17
    color: #000
@keyframes msgFadeInOut
    0%
        opacity: 0
        transform: translateY(8px)
    10%
        opacity: 1
        transform: translateY(0)
    80%
        opacity: 1
    100%
        opacity: 0
'''

    def __init__(self, messages=(), **attrs):
        items = [
            Div(str(m), cls=f'app-message app-message--{m.tags}')
            for m in messages
        ]
        super().__init__(*items, **attrs)

    class HTMLElement:
        def connectedCallback(self):
            msgs = this.querySelectorAll('.app-message')
            i = 0
            while i < msgs.length:
                msgs[i].addEventListener('animationend', this.removeMsg)
                i = i + 1

        def removeMsg(self, event):
            event.target.remove()


class TopAppBar(Component):
    """Fixed top bar with title and hamburger menu toggle."""

    tag = 'top-app-bar'
    sass = '''
top-app-bar
    position: fixed
    top: 0
    left: 0
    right: 0
    height: 64px
    background: var(--mdc-theme-primary, #6200ee)
    color: #fff
    display: flex
    align-items: center
    padding: 0 8px
    z-index: 100
    box-shadow: 0 2px 4px rgba(0,0,0,.25)
.app-bar__title
    flex: 1
    font-size: 20px
    font-weight: 500
    margin-left: 12px
    white-space: nowrap
    overflow: hidden
    text-overflow: ellipsis
.app-bar__toggle
    background: none
    border: none
    cursor: pointer
    color: #fff
    padding: 8px
    border-radius: 50%
    display: flex
    align-items: center
    justify-content: center
'''

    def __init__(self, title='', **attrs):
        super().__init__(
            Button(
                MDCIcon('menu'),
                cls='app-bar__toggle',
                type='button',
                aria_label='Menu',
            ),
            Span(title, cls='app-bar__title'),
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            if document.readyState == 'complete':
                this.init()
            else:
                window.addEventListener('load', this.init.bind(this))

        def init(self):
            btn = this.querySelector('.app-bar__toggle')
            if btn:
                btn.addEventListener('click', this.toggleDrawer.bind(this))

        def toggleDrawer(self):
            drawer = document.querySelector('nav-drawer')
            if drawer:
                drawer.toggle()


class NavDrawer(Component):
    """Slide-in navigation drawer with backdrop; toggled by TopAppBar."""

    tag = 'nav-drawer'
    sass = '''
nav-drawer
    position: fixed
    top: 0
    left: 0
    bottom: 0
    width: 256px
    background: #fff
    z-index: 200
    box-shadow: 2px 0 8px rgba(0,0,0,.2)
    transform: translateX(-260px)
    transition: transform 0.25s ease
    overflow-y: auto
    display: flex
    flex-direction: column
nav-drawer.open
    transform: translateX(0)
.nav-drawer__header
    padding: 20px 16px 16px
    background: var(--mdc-theme-primary, #6200ee)
    color: #fff
.nav-drawer__header-title
    font-size: 18px
    font-weight: 500
.nav-drawer__user
    font-size: 13px
    opacity: .85
    margin-top: 4px
    border-top: 1px solid rgba(255,255,255,.25)
    padding-top: 6px
.nav-drawer__item
    display: block
    padding: 12px 16px
    text-decoration: none
    color: inherit
    font-size: 14px
.nav-drawer__item:hover
    background: rgba(0,0,0,.04)
.nav-drawer-backdrop
    display: none
    position: fixed
    top: 0
    left: 0
    right: 0
    bottom: 0
    background: rgba(0,0,0,.4)
    z-index: 199
.nav-drawer-backdrop.visible
    display: block
'''

    def __init__(self, nav_items=(), title='', username=None, **attrs):
        items = [
            A(
                item.get('label', ''),
                href=item.get('url', '#'),
                cls='nav-drawer__item',
            )
            for item in nav_items
        ]
        user_node = Div(username, cls='nav-drawer__user') if username else None
        super().__init__(
            Div(
                Div(title, cls='nav-drawer__header-title'),
                user_node,
                cls='nav-drawer__header',
            ),
            *items,
            **attrs,
        )

    class HTMLElement:
        def connectedCallback(self):
            backdrop = document.createElement('div')
            backdrop.className = 'nav-drawer-backdrop'
            document.body.appendChild(backdrop)
            this._backdrop = backdrop
            backdrop.addEventListener('click', this.close.bind(this))

        def toggle(self):
            if this.classList.contains('open'):
                this.close()
            else:
                this.open()

        def open(self):
            this.classList.add('open')
            this._backdrop.classList.add('visible')

        def close(self):
            this.classList.remove('open')
            this._backdrop.classList.remove('visible')


_APP_GLOBAL_CSS = '''
body { margin: 0; font-family: Roboto, sans-serif; }
.app-main-content { padding-top: 72px; min-height: calc(100vh - 72px); }
'''


class App(CRUDDocument):
    """Full app shell: NavDrawer + TopAppBar + Messages + content."""

    def __init__(self, *content, request=None, title='', nav_items=(),
                 su_url=None, extra_head=(), **attrs):
        from django.contrib.messages import get_messages as _get_msgs
        messages = list(_get_msgs(request)) if request else []

        all_nav = list(nav_items)

        if request is not None:
            # Impersonation "back to your account" link
            if su_url and getattr(request, 'session', {}).get('become_user'):
                realname = request.session.get('become_user_realname', 'your account')
                all_nav.append({
                    'label': f'← Back to {realname}',
                    'url': su_url,
                })

            # Login / logout at the bottom of the drawer
            user = getattr(request, 'user', None)
            try:
                from django.urls import reverse as _rev
                if user and user.is_authenticated:
                    all_nav.append({'label': 'Logout', 'url': _rev('logout')})
                else:
                    all_nav.append({'label': 'Login', 'url': _rev('login')})
            except Exception:
                pass

        user = getattr(request, 'user', None) if request else None
        username = None
        if user and getattr(user, 'is_authenticated', False):
            username = user.get_full_name() or user.username

        super().__init__(
            NavDrawer(nav_items=all_nav, title=title, username=username),
            TopAppBar(title=title),
            Messages(messages),
            Div(*content, cls='app-main-content'),
            extra_head=[Style(_APP_GLOBAL_CSS), *extra_head],
            **attrs,
        )


# ---------------------------------------------------------------------------
# Tier 3 — Auth / domain extras
# ---------------------------------------------------------------------------

class Home(Div):
    """Welcome page shown at the site root."""

    style = {
        'max-width': '600px',
        'margin': '4em auto',
        'padding': '0 1em',
        'text-align': 'center',
    }

    def __init__(self, request, site_title='App', **attrs):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            name = user.get_full_name() or user.username
            heading = H1(f'Welcome back, {name}!')
            cta = None
        else:
            heading = H1(f'Welcome to {site_title}')
            try:
                login_url = reverse('login')
            except Exception:
                login_url = '/login/'
            cta = A(
                MDCButtonRaised('Login to continue', tag='span'),
                href=login_url,
                style='text-decoration:none',
            )
        super().__init__(heading, cta, **attrs)


class LoggedOut(NarrowCard):
    """Shown after a successful logout."""

    def __init__(self, **attrs):
        try:
            login_url = reverse('login')
        except Exception:
            login_url = '/login/'
        super().__init__(
            H1('You have been logged out.'),
            P('Thanks for visiting. See you next time.'),
            A(
                MDCButton('Log in again', tag='span'),
                href=login_url,
                style='text-decoration:none',
            ),
            **attrs,
        )


class LoginPage(NarrowCard):
    """Login form wrapped in the app shell."""

    def __init__(self, form, request, **attrs):
        super().__init__(
            H2('Sign in', style='margin: 0 0 1em'),
            Form(
                form,
                CSRFInput(request),
                MDCButtonRaised(
                    'Sign in',
                    tag='button',
                    type='submit',
                    style='margin-top:1em',
                ),
                method='post',
                action=request.path_info,
                style='display:flex;flex-direction:column;gap:8px',
            ),
            **attrs,
        )


class HistoryList(Div):
    """Admin LogEntry history for one object, most recent first."""

    style = {'margin-top': '2em'}

    def __init__(self, obj, **attrs):
        try:
            from django.contrib.admin.models import LogEntry
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(obj)
            entries = list(
                LogEntry.objects.filter(content_type=ct, object_id=obj.pk)
                .select_related('user').order_by('-action_time')[:20]
            )
        except Exception:
            entries = []

        if not entries:
            super().__init__(**attrs)
            return

        # action_flag: 1=add, 2=change, 3=delete
        _icons = {1: 'add_circle', 2: 'edit', 3: 'delete'}
        _colors = {1: '#388e3c', 2: '#1565c0', 3: '#c62828'}

        thead = MDCDataTableThead(tr=MDCDataTableHeaderTr(
            MDCDataTableTh('', style='width:1px'),
            MDCDataTableTh('When'),
            MDCDataTableTh('Who'),
            MDCDataTableTh('What'),
        ))
        table = MDCDataTableResponsive(thead=thead, style={'min-width': '100%'})
        for e in entries:
            icon = _icons.get(e.action_flag, 'info')
            color = _colors.get(e.action_flag, 'inherit')
            table.tbody.addchild(MDCDataTableTr(
                MDCDataTableTd(MDCIcon(icon, style=f'font-size:18px;color:{color}')),
                MDCDataTableTd(e.action_time.strftime('%Y-%m-%d %H:%M')),
                MDCDataTableTd(str(e.user)),
                MDCDataTableTd(e.change_message or e.get_action_flag_display()),
            ))

        super().__init__(
            H3('History', style='margin:0 0 0.5em;font-size:16px;font-weight:500'),
            table,
            **attrs,
        )


# ---------------------------------------------------------------------------
# Generic Router — auto-generates CRUD views + URLs for any Django model
# ---------------------------------------------------------------------------

class Router:
    """Subclass and set `model` to get a full CRUD suite with zero boilerplate.

    Usage::

        class BookRouter(Router):
            model = Book
            open_access = True
            table_fields = ['title', 'author']
            search_fields = ['title', 'author__name']
            filter_fields = ['published', 'in_stock']

        urlpatterns, app_name = BookRouter.get_urls()
    """

    model = None
    open_access = False
    table_fields = None    # None → auto-derived from model meta
    detail_fields = None   # None → same as table_fields
    form_fields = None     # None → auto-derived (excludes id, password, ptr)
    search_fields = None   # None → no search bar
    filter_fields = None   # None → no filter drawer
    document = None        # None → App shell (override to swap document class)
    site_title = 'App'
    su_url = None          # URL for "switch back" when impersonating

    def __class_getitem__(cls, key):
        model_name = cls.model._meta.model_name
        return SimpleNamespace(url=reverse(f'{model_name}:{key}'))

    @classmethod
    def _auto_fields(cls, skip_names=None):
        from django.db.models import AutoField
        from django.db.models.fields.related import ForeignObjectRel, ManyToManyField
        skip = {'password'} | (skip_names or set())
        fields = []
        for f in cls.model._meta.get_fields():
            if isinstance(f, (ForeignObjectRel, ManyToManyField, AutoField)):
                continue
            if f.name.endswith('_ptr') or f.name in skip:
                continue
            fields.append(f.name)
        return fields

    @classmethod
    def get_table_fields(cls):
        return cls.table_fields if cls.table_fields is not None else cls._auto_fields()

    @classmethod
    def get_detail_fields(cls):
        return cls.detail_fields if cls.detail_fields is not None else cls.get_table_fields()

    @classmethod
    def get_form_fields(cls):
        return cls.form_fields if cls.form_fields is not None else cls._auto_fields()

    @classmethod
    def get_nav_items(cls, request):
        """Return a list of {'label': ..., 'url': ...} dicts for the nav drawer."""
        return []

    @classmethod
    def get_queryset(cls, view):
        return cls.model.objects.order_by('pk')

    @classmethod
    def has_perm(cls, request, action, obj=None):
        if cls.open_access:
            return True
        app_label = cls.model._meta.app_label
        model_name = cls.model._meta.model_name
        return request.user.has_perm(f'{app_label}.{action}_{model_name}', obj)

    @classmethod
    def get_menu(cls, name, request, object=None):
        model_name = cls.model._meta.model_name
        if name == 'model':
            views = []
            if cls.has_perm(request, 'add'):
                views.append(SimpleNamespace(
                    label='Create', icon='add', color='var(--mdc-theme-primary)',
                    url=reverse(f'{model_name}:create'),
                    controller=None, urlname='create', router=cls,
                ))
            return views
        if name == 'object' and object is not None:
            pk = object.pk
            views = []
            if cls.has_perm(request, 'view', object):
                views.append(SimpleNamespace(
                    label='Detail', icon='visibility', color='inherit',
                    url=reverse(f'{model_name}:detail', kwargs={'pk': pk}),
                    controller=None, urlname='detail', router=cls,
                ))
            if cls.has_perm(request, 'change', object):
                views.append(SimpleNamespace(
                    label='Edit', icon='edit', color='inherit',
                    url=reverse(f'{model_name}:update', kwargs={'pk': pk}),
                    controller=None, urlname='update', router=cls,
                ))
            if cls.has_perm(request, 'delete', object):
                views.append(SimpleNamespace(
                    label='Delete', icon='delete', color='#c00',
                    url=reverse(f'{model_name}:delete', kwargs={'pk': pk}),
                    controller='modal', urlname='delete',
                    destructive=True, router=cls,
                ))
            return views
        # 'list_action': base Router has no bulk actions; subclasses may add them
        return []

    @classmethod
    def _response(cls, component, view):
        request = getattr(view, 'request', None)
        if cls.document is not None:
            doc = cls.document(component)
        else:
            doc = App(
                component,
                request=request,
                title=cls.site_title,
                nav_items=cls.get_nav_items(request),
                su_url=cls.su_url,
            )
        return HttpResponse(doc.to_html(view=view))

    @classmethod
    def get_urls(cls):
        router = cls
        model = cls.model
        model_name = model._meta.model_name
        verbose = str(model._meta.verbose_name).capitalize()
        verbose_plural = str(model._meta.verbose_name_plural).capitalize()
        form_class = modelform_factory(model, fields=cls.get_form_fields())

        class ListView(View):
            def get(self, request):
                qs = router.get_queryset(self)
                component = Div(
                    H2(verbose_plural, style='margin: 1em 0 0.5em'),
                    ObjectList(router, request, qs),
                    style='max-width: 960px; margin: 0 auto; padding: 0 1em',
                )
                return router._response(component, self)

        class DetailView(View):
            def get(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                component = Div(
                    H2(str(obj), style='margin: 1em 0 0.5em'),
                    ObjectDetail(router, request, obj),
                    style='max-width: 960px; margin: 0 auto; padding: 0 1em',
                )
                return router._response(component, self)

        class CreateView(View):
            title = f'Create {verbose}'
            title_submit = 'Create'

            def get(self, request):
                return router._response(ObjectForm(self, form_class()), self)

            def post(self, request):
                form = form_class(request.POST)
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(reverse(f'{model_name}:list'))
                return router._response(ObjectForm(self, form), self)

        class UpdateView(View):
            title = f'Edit {verbose}'
            title_submit = 'Save'

            def get(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                return router._response(ObjectForm(self, form_class(instance=obj)), self)

            def post(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                form = form_class(request.POST, instance=obj)
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(
                        reverse(f'{model_name}:detail', kwargs={'pk': obj.pk})
                    )
                return router._response(ObjectForm(self, form), self)

        class DeleteView(View):
            def get(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                _next = request.GET.get('_next', reverse(f'{model_name}:list'))
                component = Div(
                    H2(f'Delete {obj}?', style='margin: 1em 0 0.5em'),
                    Form(
                        CSRFInput(request),
                        Input(type='hidden', name='_next', value=_next),
                        MDCButtonRaised(
                            'Confirm delete',
                            style='background: #c00',
                            type='submit',
                        ),
                        A(
                            MDCButton('Cancel', tag='span'),
                            href=reverse(f'{model_name}:list'),
                            style='text-decoration: none',
                        ),
                        method='post',
                        style='margin-top: 1em; display: flex; gap: 1em',
                    ),
                    style='max-width: 480px; margin: 2em auto; padding: 0 1em',
                )
                return router._response(component, self)

            def post(self, request, pk):
                obj = get_object_or_404(model, pk=pk)
                obj.delete()
                _next = request.POST.get('_next') or reverse(f'{model_name}:list')
                return HttpResponseRedirect(_next)

        for view_cls in [ListView, DetailView, CreateView, UpdateView, DeleteView]:
            view_cls.model = model

        patterns = [
            path('', ListView.as_view(), name='list'),
            path('create/', CreateView.as_view(), name='create'),
            path('<int:pk>/', DetailView.as_view(), name='detail'),
            path('<int:pk>/update/', UpdateView.as_view(), name='update'),
            path('<int:pk>/delete/', DeleteView.as_view(), name='delete'),
        ]
        return patterns, model_name

    @classmethod
    def get_auth_urls(cls):
        """Return URL patterns for login / logout / home using the App shell.

        Include alongside get_urls()::

            urlpatterns += UserRouter.get_auth_urls()
            urlpatterns, app_name = UserRouter.get_urls()
        """
        from django.contrib.auth import authenticate as _auth
        from django.contrib.auth import login as _login
        from django.contrib.auth import logout as _logout
        from django.contrib.auth.forms import AuthenticationForm
        router = cls

        class HomeView_(View):
            def get(self, request):
                component = Div(
                    Home(request, site_title=router.site_title),
                    style='max-width: 600px; margin: 0 auto',
                )
                return router._response(component, self)

        class LoginView_(View):
            def get(self, request):
                if getattr(request, 'user', None) and request.user.is_authenticated:
                    return HttpResponseRedirect(
                        request.GET.get('next', router._default_list_url())
                    )
                form = AuthenticationForm()
                return router._response(LoginPage(form, request), self)

            def post(self, request):
                form = AuthenticationForm(data=request.POST)
                if form.is_valid():
                    _login(request, form.get_user())
                    return HttpResponseRedirect(
                        request.POST.get('next', router._default_list_url())
                    )
                return router._response(LoginPage(form, request), self)

        class LogoutView_(View):
            def get(self, request):
                _logout(request)
                return router._response(LoggedOut(), self)

            def post(self, request):
                _logout(request)
                return router._response(LoggedOut(), self)

        for view_cls in [HomeView_, LoginView_, LogoutView_]:
            view_cls.model = None

        return [
            path('home/', HomeView_.as_view(), name='home'),
            path('login/', LoginView_.as_view(), name='login'),
            path('logout/', LogoutView_.as_view(), name='logout'),
        ]

    @classmethod
    def _default_list_url(cls):
        """Return the list URL for this router's model, or '/' on failure."""
        try:
            return reverse(f'{cls.model._meta.model_name}:list')
        except Exception:
            return '/'
