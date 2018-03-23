"""
This is the local_settings file for platform API doc.
"""

from lms.envs.common import *

# Generate a SECRET_KEY for this build
from random import choice
characters = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
SECRET_KEY = ''.join([choice(characters) for i in range(50)])

# for use in openedx/core/djangoapps/profile_images/images.py
PROFILE_IMAGE_MAX_BYTES = 1000
PROFILE_IMAGE_MIN_BYTES = 1000

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "edx.db",
        'ATOMIC_REQUESTS': True,
    },
    'student_module_history': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "student_module_history.db",
        'ATOMIC_REQUESTS': True,
    }
}

XQUEUE_INTERFACE = {
    "url": "http://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

from openedx.core.lib.derived import derive_settings
derive_settings(__name__)
