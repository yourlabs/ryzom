import sys

from crudlfap.settings import *  # noqa


DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
DATABASES['default']['NAME'] = 'ryzom'

# Find demo app modules when running under `ryzom runserver`
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

INSTALLED_APPS = [  # noqa: F405
    'ryz_ex',
    'todos',
    'channels',  # optional, but required for client-side interaction
    'ryzom',
    ] + INSTALLED_APPS + [  # noqa: F405
]

# CRUDLFA+ optional dependencies
OPTIONAL_APPS = [
    # {'debug_toolbar': {'after': 'django.contrib.staticfiles'}},
    {'django_extensions': {'before': 'crudlfap'}},
    {'collectdir': {'before': 'crudlfap'}},
]

OPTIONAL_MIDDLEWARE = [
    # {'debug_toolbar.middleware.DebugToolbarMiddleware': None}
]

MIDDLEWARE += [  # noqa: F405
    'ryzom.middleware.RyzomMiddleware',
]

if DEBUG:
    install_optional(OPTIONAL_APPS, INSTALLED_APPS)  # noqa: F405
    install_optional(OPTIONAL_MIDDLEWARE, MIDDLEWARE)  # noqa: F405

"""
AUTHENTICATION_BACKENDS += [  # noqa: F405
    'crudlfap_example.blog.crudlfap.AuthBackend',
]
"""

ROOT_URLCONF = 'ryz_ex.urls'

STATIC_ROOT = os.getenv(
    'STATIC_ROOT', Path(os.path.dirname(__file__)) / 'static')

ASGI_APPLICATION = 'ryz_ex.routing.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

# ryzom settings
RYZOM_APP = 'todos'
DDP_URLPATTERNS = 'todos.routing'
SERVER_METHODS = [
    'todos.methods'
]

CRUDLFAP_TEMPLATE_BACKEND["OPTIONS"]["globals"][  # noqa: F405
    "render_form"] = "ryz_ex.jinja2_ryzom.render_form"
#     "crudlfap.jinja2.render_form"

RYZOM_TEMPLATE_BACKEND = {
    "BACKEND": "ryzom.backends.ryzom.Ryzom",
    "OPTIONS": {
        "app_dirname": "components",
        "components_module": "ryzom.components.muicss",
        "components_prefix": "Mui",
        # "components_module": "ryzom.components.django",
        # "components_prefix": "Django",

        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.i18n",
        ],
        # "autoescape": True,
        # "auto_reload": DEBUG,
        # "translation_engine": "django.utils.translation",
        # "debug": False,
    }
}
TEMPLATES.append(RYZOM_TEMPLATE_BACKEND)

PYTEST_SKIP = os.getenv('PYTEST_SKIP', False)

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
