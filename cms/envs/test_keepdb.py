# -*- coding: utf-8 -*-
"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions which will be stored on disk. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /edx-platform  # The location of this repo
        /log  # Where we're going to write log files
"""

from .test import *  # pylint: disable=wildcard-import
from .aws import *  # pylint: disable=wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'edx.db',
        'TEST_NAME': TEST_ROOT / 'db' / 'edx.db',
        'ATOMIC_REQUESTS': True,
    },
    'student_module_history': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'student_module_history.db',
        'TEST_NAME': TEST_ROOT / 'db' / 'student_module_history.db'
    },
}
