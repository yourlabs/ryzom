from django.conf import settings

if 'channels' in settings.INSTALLED_APPS:
    default_app_config = 'ryzom_django.apps.ReactiveConfig'
else:
    default_app_config = 'ryzom_django.apps.BaseConfig'
