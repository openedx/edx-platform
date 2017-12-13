"""
Minimal Django settings for tests of common/lib.
Required in Django 1.9+ due to imports of models in stock Django apps.
"""

from __future__ import absolute_import, unicode_literals

import tempfile

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'openedx.core.djangoapps.video_config',
    'openedx.core.djangoapps.video_pipeline',
    'edxval',
)

MEDIA_ROOT = tempfile.mkdtemp()

SECRET_KEY = 'insecure-secret-key'

USE_TZ = True
