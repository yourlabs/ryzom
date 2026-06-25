import os
import socket
from pathlib import Path

REDIS_SERVER = None
CHANNELS_ENABLE = False

REDIS_SERVERS = [
    ('redis', 6379),
    ('127.0.0.1', 6379)
]

if 'CHANNELS_ENABLE' in os.environ:
    CHANNELS_ENABLE = bool(os.environ['CHANNELS_ENABLE'])

for server in REDIS_SERVERS:
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result_of_check = a_socket.connect_ex(server)
    except socket.gaierror:
        continue

    if result_of_check == 0:
        REDIS_SERVER = server
        CHANNELS_ENABLE = True
        break

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = '4am4pn_87&v0qaq%_-2me06et#@prq(yp6npk8g495!@7s1hoi'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # required for Subscription.qs ArrayField

    'ryzom_django_example',
    'ryzom_example_crud',

    # Enable components templates auto discover
    'ryzom_django',

    # Add py2js static file
    'py2js',

    # Transform select HTML tags into autocompletes webcomponents.
    # The autocomplete-light web component (css/js) ships in django-autocomplete-
    # light's `dal_alight` app; listing it here lets the staticfiles app-dirs
    # finder serve `dal_alight/autocomplete-light.{css,js}`.
    'dal_alight',
    'ryzom_django_autocomplete',

    # Enable form rendering with MDC components
    'ryzom_django_mdc',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# Enable Ryzom template backend
TEMPLATES = [
    {
        'BACKEND': 'ryzom_django.template_backend.Ryzom',
        'NAME': 'ryzom',
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

if CHANNELS_ENABLE:
    # daphne must precede staticfiles so `runserver` serves over ASGI (channels 4)
    INSTALLED_APPS = ['daphne'] + INSTALLED_APPS + [
        # Enable Reactive components models
        'ryzom_django_channels',
        'ryzom_django_channels_example',
        'channels',
        'channels_redis',
        'celery',
    ]

ROOT_URLCONF = 'ryzom_django_example.urls'
WS_HOST = ''
WS_PORT = ''  # empty -> client uses same-origin host/port for the ws:// URL
WS_URLPATTERNS = ROOT_URLCONF
SERVER_METHODS = []

# Client-pull (polling) transport — the no-server-push fallback (POLLING.md).
# RYZOM_TRANSPORT forces 'ws' or 'poll'; unset -> 'ws' when channels is on, else
# 'poll'. Set RYZOM_TRANSPORT=poll to run the live UI with no server-initiated
# communication even where the websocket infra is available.
RYZOM_TRANSPORT = os.environ.get('RYZOM_TRANSPORT') or None
POLL_URL = '/crud/products/poll/'   # where ddp_poll is mounted (demo)
POLL_INTERVAL = 2000                # client poll cadence, ms
POLL_TTL = 60                       # seconds before an idle polling client is swept

ASGI_APPLICATION = 'ryzom_django_example.asgi.application'

if CHANNELS_ENABLE:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_SERVER],
            },
        },
    }


DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'ryzom'),
        'PORT': os.getenv('DB_PORT', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# Default to the redis the detection loop above actually found (e.g. the
# `redis` service host under CI); fall back to localhost when none was probed.
_redis_host, _redis_port = REDIS_SERVER or ('127.0.0.1', 6379)
_redis_url = f'redis://{_redis_host}:{_redis_port}'
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', _redis_url)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', _redis_url)
