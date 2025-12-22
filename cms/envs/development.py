"""
This settings file is optimized for local development.  It should work equally well for bare-metal development and for
running inside of development environments such as tutor.

This file is currently in development itself and so may not work for everyone out of the box.  More updates, including
updated documentation will be added as we get closer to removing devstack.py
"""

#Helpers for loading plugins and their settings.
from edx_django_utils.plugins import add_plugins
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

# Use the common file as the starting point.
# pylint: disable=wildcard-import
from .common import *
from openedx.core.lib.derived import derive_settings

DEBUG = True

STORAGES['default']['BACKEND'] = 'django.core.files.storage.FileSystemStorage'
STORAGES['staticfiles']['BACKEND'] = 'openedx.core.storage.DevelopmentStorage'

# Disable pipeline compression in development
PIPELINE['PIPELINE_ENABLED'] = False

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
]

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

LMS_BASE = 'local.openedx.io:18000'
LMS_ROOT_URL = f'http://{LMS_BASE}'

CMS_BASE = 'studio.local.openedx.io:18000'
CMS_ROOT_URL = f'http://{CMS_BASE}'
ALLOWED_HOSTS = ['studio.local.openedx.io']

# Dealing with CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    "http://apps.local.openedx.io:1996",
    "http://apps.local.openedx.io:2000",
)

# Cookie Related Settings
SESSION_COOKIE_DOMAIN = '.local.openedx.io'

# MFE Development URLs
# This one needs a trailing slash to load correctly right now.
LEARNER_HOME_MICROFRONTEND_URL = 'http://apps.local.openedx.io:1996/learner-dashboard/'
# This one explicitly needs to not have a trailing slash because of how it's used to make other
# urls.
LEARNING_MICROFRONTEND_URL = "http://apps.local.openedx.io:2000/learning"

#######################################################################################################################
#### DERIVE ANY DERIVED SETTINGS
####

derive_settings(__name__)
add_plugins(__name__, ProjectType.LMS, SettingsType.DEVSTACK)
