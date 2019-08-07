from crudlfap.settings import *  # noqa

INSTALLED_APPS = [  # noqa
    'channels',
    'ryzom',
    ] + INSTALLED_APPS + [
    'todos',
]

MIDDLEWARE += [
    'ryzom.middleware.RyzomMiddleware',
]

install_optional(OPTIONAL_APPS, INSTALLED_APPS)  # noqa
install_optional(OPTIONAL_MIDDLEWARE, MIDDLEWARE)  # noqa

"""
AUTHENTICATION_BACKENDS += [  # noqa
    'crudlfap_example.blog.crudlfap.AuthBackend',
]
"""

ROOT_URLCONF = 'project.urls'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
""" This should be provided as ENV variables as expected by crudlfap.settings.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_ddp_test_project',
        'USER': 'ryzom',
        'PASSWORD': 'ryzom',
        'HOST': 'localhost',
    }
}
"""

ASGI_APPLICATION = 'project.routing.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

# ryzom settings
DDP_URLPATTERNS = 'todos.routing'
SERVER_METHODS = [
        'todos.methods'
    ]
