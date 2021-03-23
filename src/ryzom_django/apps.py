from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class BaseConfig(AppConfig):
    name = 'ryzom_django'

    def ready(self):
        autodiscover_modules('html')
        super().ready()
