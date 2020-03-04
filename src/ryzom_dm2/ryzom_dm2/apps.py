from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class RyzomConfig(AppConfig):
    name = 'ryzom_dm2'


class RyzomAdminConfig(AdminConfig):
    default_site = 'ryzom_dm2.admin.RyzomAdminSite'
