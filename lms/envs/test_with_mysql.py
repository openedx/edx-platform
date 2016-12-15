"""
Used when testing with MySQL.
"""
from openedx.stanford.lms.envs.test import *  # pylint: disable=wildcard-import
from openedx.stanford.lms.envs.aws import *  # pylint: disable=wildcard-import

# Dummy secret key for dev
SECRET_KEY = 'dev key'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'lms.djangoapps.verify_student',
)
