from .test import *
from .aws import *

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'lms.djangoapps.verify_student',
)
