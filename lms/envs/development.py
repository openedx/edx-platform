"""
This settings file is optimized for local development.  It should work equally well for bare-metal development and for
running inside of development environments such as tutor.
"""

#Helpers for loading plugins and their settings.
from edx_django_utils.plugins import add_plugins
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

# Use the common file as the starting point.
from .common import *
from openedx.core.lib.derived import Derived, derive_settings

DEBUG = True

STORAGES['default']['BACKEND'] = 'django.core.files.storage.FileSystemStorage'

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

LMS_BASE = 'local.openedx.io:18000'
LMS_ROOT_URL = f'http://{LMS_BASE}'
ALLOWED_HOSTS = ['local.openedx.io']
#######################################################################################################################
#### DERIVE ANY DERIVED SETTINGS
####

derive_settings(__name__)
add_plugins(__name__, ProjectType.LMS, SettingsType.DEVSTACK)
