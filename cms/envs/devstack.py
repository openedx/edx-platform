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
SESSION_COOKIE_NAME = 'studio_sessionid'

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
LMS_ROOT_URL = f'http://{LMS_BASE}'
FEATURES['PREVIEW_LMS_BASE'] = "preview." + LMS_BASE

FRONTEND_REGISTER_URL = LMS_ROOT_URL + '/register'
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

# When the celery task is eagerly, it is executed locally while sharing the
# thread and its request cache with the active Django Request. In that case,
# do not clear the cache.
CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = False

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
    'debug_toolbar.panels.history.HistoryPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    # Profile panel is incompatible with wrapped views
    # See https://github.com/jazzband/django-debug-toolbar/issues/792
    'DISABLE_PANELS': (
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ),
    'SHOW_TOOLBAR_CALLBACK': 'cms.envs.devstack.should_show_debug_toolbar',
}


def should_show_debug_toolbar(request):  # lint-amnesty, pylint: disable=missing-function-docstring
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
# Needed to enable licensing on video blocks
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
FEATURES['ENABLE_CREATOR_GROUP'] = True

########################## Library creation organizations restriction #######################
FEATURES['ENABLE_ORGANIZATION_STAFF_ACCESS_FOR_CONTENT_LIBRARIES'] = True

################### FRONTEND APPLICATION PUBLISHER URL ###################
FEATURES['FRONTEND_APP_PUBLISHER_URL'] = 'http://localhost:18400'

################### FRONTEND APPLICATION LIBRARY AUTHORING ###################
LIBRARY_AUTHORING_MICROFRONTEND_URL = 'http://localhost:3001'

################### FRONTEND APPLICATION COURSE AUTHORING ###################
COURSE_AUTHORING_MICROFRONTEND_URL = 'http://localhost:2001'

################### FRONTEND APPLICATION DISCUSSIONS ###################
DISCUSSIONS_MICROFRONTEND_URL = 'http://localhost:2002'

################### FRONTEND APPLICATION DISCUSSIONS FEEDBACK URL###################
DISCUSSIONS_MFE_FEEDBACK_URL = None

################################# DJANGO-REQUIRE ###############################

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

########################### OAUTH2 #################################
JWT_AUTH.update({
    'JWT_ISSUER': f'{LMS_ROOT_URL}/oauth2',
    'JWT_ISSUERS': [{
        'AUDIENCE': 'lms-key',
        'ISSUER': f'{LMS_ROOT_URL}/oauth2',
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

# pylint: enable=unicode-format-string  # lint-amnesty, pylint: disable=bad-option-value

IDA_LOGOUT_URI_LIST = [
    'http://localhost:18130/logout/',  # ecommerce
    'http://localhost:18150/logout/',  # credentials
]

ENTERPRISE_BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = "http://edx.devstack.lms/oauth2"

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
# set replica set of contentstore to none as we haven't setup any for cms in devstack
CONTENTSTORE['DOC_STORE_CONFIG']['replicaSet'] = None

#####################################################################
# set replica sets of moduelstore to none as we haven't setup any for cms in devstack
for store in MODULESTORE['default']['OPTIONS']['stores']:
    if 'DOC_STORE_CONFIG' in store and 'replicaSet' in store['DOC_STORE_CONFIG']:
        store['DOC_STORE_CONFIG']['replicaSet'] = None


#####################################################################
# Lastly, run any migrations, if needed.
MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

############# CORS headers for cross-domain requests #################
FEATURES['ENABLE_CORS_HEADERS'] = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = corsheaders_default_headers + (
    'use-jwt-cookie',
)

################### Special Exams (Proctoring) and Prereqs ###################
FEATURES['ENABLE_SPECIAL_EXAMS'] = True
FEATURES['ENABLE_PREREQUISITE_COURSES'] = True

# Used in edx-proctoring for ID generation in lieu of SECRET_KEY - dummy value
# (ref MST-637)
PROCTORING_USER_OBFUSCATION_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

############## CourseGraph devstack settings ############################

COURSEGRAPH_CONNECTION: dict = {
    "protocol": "bolt",
    "secure": False,
    "host": "edx.devstack.coursegraph",
    "port": 7687,
    "user": "neo4j",
    "password": "edx",
}

#################### Webpack Configuration Settings ##############################
WEBPACK_LOADER['DEFAULT']['TIMEOUT'] = 5

################ Using LMS SSO for login to Studio ################
SOCIAL_AUTH_EDX_OAUTH2_KEY = 'studio-sso-key'
SOCIAL_AUTH_EDX_OAUTH2_SECRET = 'studio-sso-secret'  # in stage, prod would be high-entropy secret
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = 'http://edx.devstack.lms:18000'  # routed internally server-to-server
SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = 'http://localhost:18000'  # used in browser redirect

# Don't form the return redirect URL with HTTPS on devstack
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

#################### Network configuration ####################
# Devstack is directly exposed to the caller
CLOSEST_CLIENT_IP_FROM_HEADERS = []

#################### Credentials Settings ####################
CREDENTIALS_INTERNAL_SERVICE_URL = 'http://localhost:18150'
CREDENTIALS_PUBLIC_SERVICE_URL = 'http://localhost:18150'

#################### Event bus backend ########################
# .. toggle_name: FEATURES['ENABLE_SEND_XBLOCK_EVENTS_OVER_BUS']
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Temporary configuration which enables sending xblock events over the event bus.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-02-21
# .. toggle_warning: For consistency in user experience, keep the value in sync with the setting of the same name
#   in the LMS and CMS.
# .. toggle_tickets: 'https://github.com/openedx/edx-platform/pull/31813'
FEATURES['ENABLE_SEND_XBLOCK_EVENTS_OVER_BUS'] = True
EVENT_BUS_PRODUCER = 'edx_event_bus_kafka.create_producer'
EVENT_BUS_KAFKA_SCHEMA_REGISTRY_URL = 'http://edx.devstack.schema-registry:8081'
EVENT_BUS_KAFKA_BOOTSTRAP_SERVERS = 'edx.devstack.kafka:29092'
EVENT_BUS_TOPIC_PREFIX = 'dev'

################# New settings must go ABOVE this line #################
########################################################################
# See if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error,wildcard-import
