"""
CRUD demo — User model wired up via the generic Router.
"""
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from ryzom_django_mdc.crudlfap import Router


class UserRouter(Router):
    model = User
    open_access = True  # demo bypass — no permission checks
    site_title = 'User Admin'
    table_fields = ['username', 'email', 'first_name', 'last_name']
    detail_fields = ['username', 'email', 'first_name', 'last_name',
                     'date_joined', 'is_staff', 'is_active']
    form_fields = ['username', 'email', 'first_name', 'last_name']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filter_fields = ['is_staff', 'is_active']

    @classmethod
    def get_nav_items(cls, request):
        return [
            {'label': 'Home', 'url': '/home/'},
            {'label': 'Users', 'url': reverse_lazy('user:list')},
        ]


urlpatterns, app_name = UserRouter.get_urls()
