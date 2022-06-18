import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'opaquekeys',                   # Or path to database file if using sqlite3.
        'USER': '',                             # Not used with sqlite3.
        'PASSWORD': '',                         # Not used with sqlite3.
        'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
    }
}

SECRET_KEY = 'the-secret-key'

ROOT_URLCONF = 'urls'

INSTALLED_APPS = tuple()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
