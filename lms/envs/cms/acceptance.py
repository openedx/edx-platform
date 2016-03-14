"""
This config file is a copy of dev environment without the Debug
Toolbar. I it suitable to run against acceptance tests.

"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .dev import *

#  REMOVE DEBUG TOOLBAR

INSTALLED_APPS = tuple(e for e in INSTALLED_APPS if e != 'debug_toolbar')
INSTALLED_APPS = tuple(e for e in INSTALLED_APPS if e != 'debug_toolbar_mongo')

MIDDLEWARE_CLASSES = tuple(e for e in MIDDLEWARE_CLASSES
                           if e != 'debug_toolbar.middleware.DebugToolbarMiddleware')


########################### LETTUCE TESTING ##########################
FEATURES['DISPLAY_TOY_COURSES'] = True

INSTALLED_APPS += ('lettuce.django',)
# INSTALLED_APPS += ('portal',)

LETTUCE_APPS = ('portal',)  # dummy app covers the home page, login, registration, and course enrollment
