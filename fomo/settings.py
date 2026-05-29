from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = False

ALLOWED_HOSTS = ["fomo-projekt.tech", "www.fomo-projekt.tech", "51.83.252.122", "localhost", "127.0.0.1", "fomo-projekt.tech"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "todo",
]

AUTH_USER_MODEL = "todo.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "task_list"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "fomo.urls"
WSGI_APPLICATION = "fomo.wsgi.application"


OVH_MYSQL_HOST = os.getenv("OVH_MYSQL_HOST")
OVH_MYSQL_PORT = os.getenv("OVH_MYSQL_PORT", "3306")
OVH_MYSQL_USER = os.getenv("OVH_MYSQL_USER")
OVH_MYSQL_PASSWORD = os.getenv("OVH_MYSQL_PASSWORD")
OVH_MYSQL_DB = os.getenv("OVH_MYSQL_DB")

if OVH_MYSQL_HOST and OVH_MYSQL_USER and OVH_MYSQL_PASSWORD and OVH_MYSQL_DB:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": OVH_MYSQL_DB,
            "USER": OVH_MYSQL_USER,
            "PASSWORD": OVH_MYSQL_PASSWORD,
            "HOST": OVH_MYSQL_HOST,
            "PORT": OVH_MYSQL_PORT,
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# (opcjonalnie, ale polecam w dev)
STATICFILES_DIRS = []
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

