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
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'ryzom_django_example',

    # Enable components templates auto discover
    'ryzom_django',

    # Add py2js static file
    'py2js',

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
    # Enable Reactive components models
    INSTALLED_APPS += [
        'ryzom_django_channels',
        'ryzom_django_channels_example',
        'channels',
        'channels_redis',
    ]

ROOT_URLCONF = 'ryzom_django_example.urls'
WS_URLPATTERNS = ROOT_URLCONF
SERVER_METHODS = []

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
        'NAME': os.getenv('DB_NAME', 'ryzom_django_example'),
        'HOST': os.getenv('DB_HOST'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
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

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
