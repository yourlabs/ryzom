import os
from pathlib import Path
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

    # Enable components templates auto discover
    'ryzom_django',
    'ryzom',
    # Enable Reactive components models
    # 'ryzom_django.apps.ReactiveConfig',

    # Enable form rendering with MDC components
    'ryzom_django_mdc',

    # Enable default templates too, until we implement them all
    'django.forms',
]

MIDDLEWARE = [
    # Enable Reactive middleware
    'ryzom_django.middleware.RyzomMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Enable Ryzom form rendering
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# Enable Ryzom template backend
TEMPLATES = [
    {
        "BACKEND": "ryzom_django.template_backend.Ryzom",
        "OPTIONS": {
            "app_dirname": "components",
            # "components_module": "ryzom.components.muicss",
            # "components_prefix": "Mui",
            # "components_module": "ryzom.components.django",
            # "components_prefix": "Django",
            # "context_processors": [
            #     "django.template.context_processors.debug",
            #     "django.template.context_processors.request",
            #     "django.contrib.auth.context_processors.auth",
            #     "django.contrib.messages.context_processors.messages",
            #     "django.template.context_processors.i18n",
            # ],
            # "autoescape": True,
            # "auto_reload": DEBUG,
            # "translation_engine": "django.utils.translation",
            # "debug": False,
        }
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

ROOT_URLCONF = 'ryzom_django_example.urls'

WSGI_APPLICATION = 'ryzom_django_example.wsgi.application'

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
