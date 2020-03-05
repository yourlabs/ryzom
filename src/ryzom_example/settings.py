from crudlfap.settings import *  # noqa

INSTALLED_APPS = [  # noqa: F405
    'ryzom_example.ryz_ex',
    'ryzom_example.todos',
    'channels',
    'ryzom',
    ] + INSTALLED_APPS + [  # noqa: F405
]

# CRUDLFA+ optional dependencies
OPTIONAL_APPS = [
    {'debug_toolbar': {'after': 'django.contrib.staticfiles'}},
    {'django_extensions': {'before': 'crudlfap'}},
    {'collectdir': {'before': 'crudlfap'}},
]

OPTIONAL_MIDDLEWARE = [
    {'debug_toolbar.middleware.DebugToolbarMiddleware': None}
]

MIDDLEWARE += [  # noqa: F405
    'ryzom.middleware.RyzomMiddleware',
]

# install_optional(OPTIONAL_APPS, INSTALLED_APPS)  # noqa: F405
# install_optional(OPTIONAL_MIDDLEWARE, MIDDLEWARE)  # noqa: F405

"""
AUTHENTICATION_BACKENDS += [  # noqa
    'crudlfap_example.blog.crudlfap.AuthBackend',
]
"""

ROOT_URLCONF = 'ryzom_example.ryz_ex.urls'

# Database
# https://docs.django.com/en/2.1/ref/settings/#databases
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

STATIC_ROOT = os.getenv(
    'STATIC_ROOT', Path(os.path.dirname(__file__)) / 'static')

ASGI_APPLICATION = 'ryzom_example.ryz_ex.routing.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

# ryzom settings
RYZOM_APP = 'ryzom_example.todos'
DDP_URLPATTERNS = 'ryzom_example.todos.routing'
SERVER_METHODS = [
        'ryzom_example.todos.methods'
    ]

CRUDLFAP_TEMPLATE_BACKEND["OPTIONS"]["globals"][  # noqa: F405
    "render_form"] = "ryzom_example.ryz_ex.jinja2_ryzom.render_form"
#     "crudlfap.jinja2.render_form"

# RYZOM_COMPONENTS_MODULE = 'ryzom.components.django'
# RYZOM_COMPONENTS_PREFIX = 'Django'
RYZOM_COMPONENTS_MODULE = 'ryzom.components.muicss'
RYZOM_COMPONENTS_PREFIX = 'Mui'

PYTEST_SKIP = True

"""
CRUDLFAP_TEMPLATE_BACKEND = {
    "BACKEND": "django_jinja.backend.Jinja2",
    "APP_DIRS": True,
    "OPTIONS": {
        "app_dirname": "jinja2",
        "match_extension": None,
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.i18n",
        ],
        "extensions": [
            "jinja2.ext.do",
            "jinja2.ext.loopcontrols",
            "jinja2.ext.with_",
            "jinja2.ext.i18n",
            "jinja2.ext.autoescape",
            "django_jinja.builtins.extensions.CsrfExtension",
            "django_jinja.builtins.extensions.CacheExtension",
            "django_jinja.builtins.extensions.TimezoneExtension",
            "django_jinja.builtins.extensions.UrlsExtension",
            "django_jinja.builtins.extensions.StaticFilesExtension",
            "django_jinja.builtins.extensions.DjangoFiltersExtension",
        ],
        "constants": TEMPLATE_CONSTANTS,
        "globals": {
            "pagination_filter_params": "crudlfap.jinja2.pagination_filter_params",  # noqa
            "crudlfap_site": "crudlfap.site.site",
            "getattr": getattr,
            "str": str,
            "int": int,
            "isinstance": isinstance,
            "type": type,
            "render_form": "crudlfap.jinja2.render_form",
            "render_button": "bootstrap3.forms.render_button",
            "ryzom": "ryzom.components.component_html",
        },
        "newstyle_gettext": True,
        "bytecode_cache": {
            "name": "default",
            "backend": "django_jinja.cache.BytecodeCache",
            "enabled": False,
        },
        "autoescape": True,
        "auto_reload": DEBUG,
        "translation_engine": "django.utils.translation",
        "debug": False,
    }
}
"""
