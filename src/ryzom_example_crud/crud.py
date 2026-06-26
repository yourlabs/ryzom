"""
CRUD demo — the User model, driven live by the generic ``ReactiveRouter``.

``UserCrud`` is the reactive list/detail/create suite (over the ``LiveUser``
Publishable proxy, see models.py). The classic ``UserRouter`` is kept solely for
``get_auth_urls()`` (home / login / logout on the plain App shell) — the reactive
list reuses the same shell, so login lands on it via ``reverse('user:list')``.
"""
from django.contrib.auth.models import User

from ryzom_django_channels.facets import BooleanFacet, SearchFacet
from ryzom_django_mdc.crud import Router
from ryzom_django_mdc.reactive import Action, Column, ReactiveRouter

from ryzom_example_crud.models import LiveUser

_NAV = [
    {'label': 'Home', 'url': '/home/'},
    {'label': 'Users', 'url': '/crud/users/'},
    {'label': 'Products (live)', 'url': '/crud/products/'},
]


# --- bulk / per-row action handlers ----------------------------------------

def _deactivate(queryset, request):
    for obj in queryset:
        obj.is_active = False
        obj.save()  # post_save -> DDP change push


def _delete_users(queryset, request):
    for obj in queryset:
        obj.delete()  # post_delete -> DDP remove push


def _yes_no(value):
    return '✓' if value else ''


class UserCrud(ReactiveRouter):
    model = LiveUser
    publication = 'users'
    namespace = 'user'                 # keep reverse('user:list') + /crud/users/

    site_title = 'User Admin'
    list_heading = 'Users — live'
    nav_items = _NAV
    order = ('username', 'id')
    paginate_by = 10

    facets = [
        SearchFacet('q', 'username'),
        BooleanFacet('is_staff', 'is_staff'),
        BooleanFacet('is_active', 'is_active'),
    ]
    filter_labels = {
        'q': 'Search username',
        'is_staff': 'staff only',
        'is_active': 'active only',
    }

    columns = [
        Column('username', link_detail=True),
        Column('email'),
        Column('first_name', label='First name'),
        Column('last_name', label='Last name'),
        Column('is_staff', label='Staff', cell=lambda o: _yes_no(o.is_staff)),
    ]

    create_fields = ['username', 'email', 'first_name', 'last_name']
    editable = True
    deletable = True
    detail_fields = ['username', 'email', 'first_name', 'last_name',
                     'date_joined', 'is_staff', 'is_active']

    actions = [
        Action('deactivate', 'Deactivate', _deactivate, scopes=('bulk', 'row')),
        Action('delete', 'Delete', _delete_users, scopes=('bulk', 'row'),
               confirm='Permanently delete the selected user(s)? '
                       'This cannot be undone.'),
    ]


class UserRouter(Router):
    """Classic Router kept only to serve the auth shell (home/login/logout).

    Its ``get_auth_urls()`` redirects login to ``reverse('user:list')`` — the
    reactive ``UserCrud`` list — so the two cooperate on one ``user`` namespace.
    """
    model = User
    open_access = True
    site_title = 'User Admin'

    @classmethod
    def get_nav_items(cls, request):
        return _NAV


urlpatterns, app_name = UserCrud.get_urls()
