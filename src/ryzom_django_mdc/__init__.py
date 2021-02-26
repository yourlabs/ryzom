from django import apps

default_app_config = 'ryzom_django_mdc.BaseConfig'


class BaseConfig(apps.AppConfig):
    name = 'ryzom_django_mdc'

    def ready(self):
        # add django.forms.Form.to_html() to travestite django forms into
        # components
        from ryzom_django_mdc.forms import form_to_html
