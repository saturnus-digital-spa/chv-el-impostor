import os
from pathlib import Path
from dotenv import load_dotenv

#       -       -       -       -       -       -       -       -       -       -       -

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#       -       -       -       -       -       -       -       -       -       -       -

# Load variables
load_dotenv(BASE_DIR / ".env")

#       -       -       -       -       -       -       -       -       -       -       -

# Get APP Mode
STAGE = os.getenv('STAGE')

# Set Django secret key
SECRET_KEY = os.getenv('SECRET_KEY')

#       -       -       -       -       -       -       -       -       -       -       -

# Internal Server IP
IP_SERVER = os.getenv('IP_SERVER')

# ENV Database
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# ENV Redis
REDIS_LOCATION = os.getenv('REDIS_LOCATION')
REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX')

# Security definitions
ADMIN_RESULTS_TOKEN = os.getenv('ADMIN_RESULTS_TOKEN', 'mongolico88!')

#       -       -       -       -       -       -       -       -       -       -       -

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "access-control-allow-origin",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

#       -       -       -       -       -       -       -       -       -       -       -

# CORS definitions
if STAGE == "PROD":

    ARRAY_ALLOWED_HOSTS = [
        IP_SERVER,
        "localhost",
    ]

    ARRAY_ALLOWED_HOSTS_HTTPS = [
        f"http://{IP_SERVER}",
        "http://localhost",
    ]

    DEBUG = False
    CORS_ALLOW_ALL_ORIGINS = True
    ALLOWED_HOSTS = ARRAY_ALLOWED_HOSTS
    CORS_ALLOWED_ORIGINS = ARRAY_ALLOWED_HOSTS_HTTPS
    CORS_ORIGIN_WHITELIST = ARRAY_ALLOWED_HOSTS_HTTPS

else:

    ARRAY_ALLOWED_HOSTS = [
        IP_SERVER,
        "localhost",
    ]

    ARRAY_ALLOWED_HOSTS_HTTPS = [
        f"http://{IP_SERVER}",
        "http://localhost",
    ]

    DEBUG = True
    CORS_ALLOW_ALL_ORIGINS = True
    ALLOWED_HOSTS = ARRAY_ALLOWED_HOSTS
    CORS_ALLOWED_ORIGINS = ARRAY_ALLOWED_HOSTS_HTTPS
    CORS_ORIGIN_WHITELIST = ARRAY_ALLOWED_HOSTS_HTTPS

#       -       -       -       -       -       -       -       -       -       -       -

INSTALLED_APPS = [
    'daphne',

    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Libs
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'channels',

    # Apps
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Webserver settings
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_LOCATION],
        },
    },
}

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

# Redis settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_LOCATION,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': REDIS_KEY_PREFIX
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Set restframework settings
if STAGE == "PROD":
    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
        ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ),
    }
else:
    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer', 
        ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ),
    }
