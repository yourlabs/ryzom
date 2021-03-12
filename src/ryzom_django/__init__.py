from django.conf import settings

if settings.CHANNELS_ENABLE:
    default_app_config = 'ryzom_django.apps.ReactiveConfig'
else:
    default_app_config = 'ryzom_django.apps.BaseConfig'
