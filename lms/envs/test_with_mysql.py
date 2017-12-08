"""
Used when testing with MySQL.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .test import *
from .aws import *

# Dummy secret key for dev
SECRET_KEY = 'dev key'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
]
