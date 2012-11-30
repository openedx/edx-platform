"""
This config file is a copy of dev environment without the Debug
Toolbar. I it suitable to run against acceptance tests.

"""
from .dev import *

#  REMOVE DEBUG TOOLBAR

INSTALLED_APPS = tuple(e for e in INSTALLED_APPS if e != 'debug_toolbar')
MIDDLEWARE_CLASSES = tuple(e for e in MIDDLEWARE_CLASSES \
                           if e != 'debug_toolbar.middleware.DebugToolbarMiddleware')


########################### LETTUCE TESTING ##########################
MITX_FEATURES['DISPLAY_TOY_COURSES'] = True

INSTALLED_APPS += ('lettuce.django',)

LETTUCE_APPS = ('portal',)  # dummy app covers the home page, login, registration, and course enrollment
