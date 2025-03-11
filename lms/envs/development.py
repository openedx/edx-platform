"""
This settings file is optimized for local development.  It should work equally well for bare-metal development and for
running inside of development environments such as tutor.
"""

# Use the common file as the starting point.
from .common import *
from openedx.core.lib.derived import Derived, derive_settings

DEBUG = True

STATICFILES_STORAGE = 'openedx.core.storage.DevelopmentStorage'

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

#######################################################################################################################
#### DERIVE ANY DERIVED SETTINGS
####

derive_settings(__name__)
