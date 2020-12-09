"""
Specific overrides to the base prod settings to make development easier.
"""


import logging
from os.path import abspath, dirname, join
from corsheaders.defaults import default_headers as corsheaders_default_headers

from .production import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Don't use S3 in devstack, fall back to filesystem
del DEFAULT_FILE_STORAGE
COURSE_IMPORT_EXPORT_STORAGE = 'django.core.files.storage.FileSystemStorage'
USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

DEBUG = True
USE_I18N = True
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['debug'] = DEBUG
SITE_NAME = 'localhost:8001'
HTTPS = 'off'

CMS_BASE = 'localhost:18010'

################################ LOGGERS ######################################


# Disable noisy loggers
for pkg_name in ['common.djangoapps.track.contexts', 'common.djangoapps.track.middleware']:
    logging.getLogger(pkg_name).setLevel(logging.CRITICAL)

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

################################ EMAIL ########################################

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/edx/src/ace_messages/'

################################# LMS INTEGRATION #############################

LMS_BASE = 'localhost:18000'
LMS_ROOT_URL = 'http://{}'.format(LMS_BASE)
FEATURES['PREVIEW_LMS_BASE'] = "preview." + LMS_BASE

########################### PIPELINE #################################

# Skip packaging and optimization in development
PIPELINE['PIPELINE_ENABLED'] = False
STATICFILES_STORAGE = 'openedx.core.storage.DevelopmentStorage'

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Load development webpack donfiguration
WEBPACK_CONFIG_PATH = 'webpack.dev.config.js'

############################ PYFS XBLOCKS SERVICE #############################
# Set configuration for Django pyfilesystem

DJFS = {
    'type': 'osfs',
    'directory_root': 'cms/static/djpyfs',
    'url_root': '/static/djpyfs',
}

################################# CELERY ######################################

# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True

################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    # Profile panel is incompatible with wrapped views
    # See https://github.com/jazzband/django-debug-toolbar/issues/792
    'DISABLE_PANELS': (
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ),
    'SHOW_TOOLBAR_CALLBACK': 'cms.envs.devstack.should_show_debug_toolbar',
}


def should_show_debug_toolbar(request):
    # We always want the toolbar on devstack unless running tests from another Docker container
    hostname = request.get_host()
    if hostname.startswith('edx.devstack.studio:') or hostname.startswith('studio.devstack.edx:'):
        return False
    return True


################################ MILESTONES ################################
FEATURES['MILESTONES_APP'] = True

########################### ORGANIZATIONS #################################
# Although production studio.edx.org disables `ORGANIZATIONS_AUTOCREATE`,
# we purposefully leave auto-creation enabled in Devstack Studio for developer
# convenience, allowing devs to create test courses for any organization
# without having to first manually create said organizations in the admin panel.
ORGANIZATIONS_AUTOCREATE = True

################################ ENTRANCE EXAMS ################################
FEATURES['ENTRANCE_EXAMS'] = True

################################ COURSE LICENSES ################################
FEATURES['LICENSING'] = True
# Needed to enable licensing on video modules
XBLOCK_SETTINGS.update({'VideoBlock': {'licensing_enabled': True}})

################################ SEARCH INDEX ################################
FEATURES['ENABLE_COURSEWARE_INDEX'] = False
FEATURES['ENABLE_LIBRARY_INDEX'] = False
FEATURES['ENABLE_CONTENT_LIBRARY_INDEX'] = False
SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

################################ COURSE DISCUSSIONS ###########################
FEATURES['ENABLE_DISCUSSION_SERVICE'] = True

################################ CREDENTIALS ###########################
CREDENTIALS_SERVICE_USERNAME = 'credentials_worker'

########################## Certificates Web/HTML View #######################
FEATURES['CERTIFICATES_HTML_VIEW'] = True

########################## AUTHOR PERMISSION #######################
FEATURES['ENABLE_CREATOR_GROUP'] = False

################### FRONTEND APPLICATION PUBLISHER URL ###################
FEATURES['FRONTEND_APP_PUBLISHER_URL'] = 'http://localhost:18400'

################### FRONTEND APPLICATION LIBRARY AUTHORING ###################
LIBRARY_AUTHORING_MICROFRONTEND_URL = 'http://localhost:3001'

################################# DJANGO-REQUIRE ###############################

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

########################### OAUTH2 #################################
JWT_AUTH.update({
    'JWT_ISSUER': '{}/oauth2'.format(LMS_ROOT_URL),
    'JWT_ISSUERS': [{
        'AUDIENCE': 'lms-key',
        'ISSUER': '{}/oauth2'.format(LMS_ROOT_URL),
        'SECRET_KEY': 'lms-secret',
    }],
    'JWT_SECRET_KEY': 'lms-secret',
    'JWT_AUDIENCE': 'lms-key',
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "devstack_key", "e": "AQAB", "kty": "RSA", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu'
        '48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC'
        '4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzG'
        'y5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw"}]}'
    ),

    # TODO Remove this once CMS redirects to LMS for Login
    'JWT_PRIVATE_SIGNING_JWK': (
        '{"e": "AQAB", "d": "RQ6k4NpRU3RB2lhwCbQ452W86bMMQiPsa7EJiFJUg-qBJthN0FMNQVbArtrCQ0xA1BdnQHThFiUnHcXfsTZUwmwvTu'
        'iqEGR_MI6aI7h5D8vRj_5x-pxOz-0MCB8TY8dcuK9FkljmgtYvV9flVzCk_uUb3ZJIBVyIW8En7n7nV7JXpS9zey1yVLld2AbRG6W5--Pgqr9J'
        'CI5-bLdc2otCLuen2sKyuUDHO5NIj30qGTaKUL-OW_PgVmxrwKwccF3w5uGNEvMQ-IcicosCOvzBwdIm1uhdm9rnHU1-fXz8VLRHNhGVv7z6mo'
        'ghjNI0_u4smhUkEsYeshPv7RQEWTdkOQ", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu48BUI5VcVtUWIPqzRK_LDSlZYh'
        '9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC4Ee9qG5T38LFe8_oAuFCEntimW'
        'xN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzGy5ZLcTUomo4rZLjghVpq6KZxfS'
        '6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw", "q": "7KWj7l-ZkfCElyfvwsl7kiosvi-ppOO7Imsv90cribf88Dex'
        'cO67xdMPesjM9Nh5X209IT-TzbsOtVTXSQyEsy42NY72WETnd1_nAGLAmfxGdo8VV4ZDnRsA8N8POnWjRDwYlVBUEEeuT_MtMWzwIKU94bzkWV'
        'nHCY5vbhBYLeM", "p": "wPkfnjavNV1Hqb5Qqj2crBS9HQS6GDQIZ7WF9hlBb2ofDNe2K2dunddFqCOdvLXr7ydRcK51ZwSeHjcjgD1aJkHA'
        '9i1zqyboxgd0uAbxVDo6ohnlVqYLtap2tXXcavKm4C9MTpob_rk6FBfEuq4uSsuxFvCER4yG3CYBBa4gZVU", "kid": "devstack_key", "'
        'kty": "RSA"}'
    ),
})

# pylint: enable=unicode-format-string

IDA_LOGOUT_URI_LIST = [
    'http://localhost:18130/logout/',  # ecommerce
    'http://localhost:18150/logout/',  # credentials
]

############################### BLOCKSTORE #####################################
BLOCKSTORE_API_URL = "http://edx.devstack.blockstore:18250/api/v1/"

#####################################################################

# pylint: disable=wrong-import-order, wrong-import-position
from edx_django_utils.plugins import add_plugins
# pylint: disable=wrong-import-order, wrong-import-position
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

add_plugins(__name__, ProjectType.CMS, SettingsType.DEVSTACK)


OPENAPI_CACHE_TIMEOUT = 0

#####################################################################
# Lastly, run any migrations, if needed.
MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

###############################################################################
# See if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error,wildcard-import

############# CORS headers for cross-domain requests #################
FEATURES['ENABLE_CORS_HEADERS'] = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = corsheaders_default_headers + (
    'use-jwt-cookie',
)
