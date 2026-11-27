"""
Django settings for config project.
Restructured per the CSIT327 Vertical Slicing + Supabase guide.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env (DATABASE_URL lives there, not in this file)
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-change-me")

# "True", "1", "yes", or "on" turn debug on; anything else keeps it off.
DEBUG = os.environ.get("DEBUG", "True").strip().lower() in {"1", "true", "yes", "on"}

# Comma-separated list, for example: ALLOWED_HOSTS=127.0.0.1,localhost
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Feature apps (vertical slices)
    'apps.login',
    'apps.register',
    'apps.home',
    'apps.user_profile',
    'apps.user_settings',

    'apps.medicines',
    'apps.pharmacies',
    'apps.scans',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # project-level templates/<feature>/ folders
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.user_settings.context_processors.genrx_settings',
                'apps.user_profile.context_processors.user_avatar',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database — Supabase PostgreSQL, read from .env via DATABASE_URL
# Falls back to local SQLite ONLY if DATABASE_URL is not set, so the
# project can still run before you plug in your real Supabase credentials.

# Set DJANGO_SQLITE=1 to force the local SQLite file, for example when
# running the test suite. Clearing DATABASE_URL in PowerShell does not work:
# assigning "" deletes the variable, so .env loads the Supabase URL again.
USE_SQLITE = os.environ.get("DJANGO_SQLITE", "").strip().lower() in {
    "1", "true", "yes", "on",
}

if os.environ.get("DATABASE_URL") and not USE_SQLITE:
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ["DATABASE_URL"],
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Cookies and CSRF ---------------------------------------------------
# Browsers scope cookies by host, not by port, so every other Django project
# served from 127.0.0.1 shares the default "csrftoken" and "sessionid" names.
# A leftover cookie from another project (or from an earlier run with a
# different SECRET_KEY) fails validation and causes
# "CSRF token from POST incorrect". Unique names keep GeneRX's tokens apart.
SESSION_COOKIE_NAME = "genrx_sessionid"
CSRF_COOKIE_NAME = "genrx_csrftoken"

# Origins allowed to submit POST forms when the app is opened through a LAN
# address, for example http://192.168.1.20:8000 during a classroom demo.
# Add hosts to ALLOWED_HOSTS as well, or the request is rejected first.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) — one project-level static/ folder,
# with a feature subfolder per app (per the vertical slicing guide).
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Uploaded prescription images. Served by Django only while DEBUG is on.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Auth redirect settings (namespaced URL names: "app_name:url_name") ---
LOGIN_URL = 'login:login'
LOGIN_REDIRECT_URL = 'home:home'
LOGOUT_REDIRECT_URL = 'login:login'
