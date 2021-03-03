from django import apps

default_app_config = 'ryzom_django_mdc.BaseConfig'


class BaseConfig(apps.AppConfig):
    name = 'ryzom_django_mdc'
