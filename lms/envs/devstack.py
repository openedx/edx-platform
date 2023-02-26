"""
Specific overrides to the base prod settings to make development easier.
"""


# Silence noisy logs
import logging
from os.path import abspath, dirname, join

from corsheaders.defaults import default_headers as corsheaders_default_headers

# pylint: enable=unicode-format-string  # lint-amnesty, pylint: disable=bad-option-value
#####################################################################
from edx_django_utils.plugins import add_plugins

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

from .production import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Don't use S3 in devstack, fall back to filesystem
del DEFAULT_FILE_STORAGE
ORA2_FILEUPLOAD_BACKEND = 'django'


DEBUG = True
USE_I18N = True
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['debug'] = True
LMS_BASE = 'localhost:18000'
CMS_BASE = 'localhost:18010'
SITE_NAME = LMS_BASE

SESSION_COOKIE_NAME = 'lms_sessionid'

# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True
# When the celery task is run eagerly, it is executed locally while sharing the
# thread and its request cache with the active Django Request. In that case,
# do not clear the cache.
CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = False
HTTPS = 'off'

LMS_ROOT_URL = f'http://{LMS_BASE}'
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL
ENTERPRISE_API_URL = f'{LMS_INTERNAL_ROOT_URL}/enterprise/api/v1/'
IDA_LOGOUT_URI_LIST = [
    'http://localhost:18130/logout/',  # ecommerce
    'http://localhost:18150/logout/',  # credentials
    'http://localhost:18381/logout/',  # discovery
    'http://localhost:18010/logout/',  # studio
]

################################ LOGGERS ######################################

LOG_OVERRIDES = [
    ('common.djangoapps.track.contexts', logging.CRITICAL),
    ('common.djangoapps.track.middleware', logging.CRITICAL),
    ('lms.djangoapps.discussion.django_comment_client.utils', logging.CRITICAL),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

################################ EMAIL ########################################

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/edx/src/ace_messages/'

############################ PYFS XBLOCKS SERVICE #############################
# Set configuration for Django pyfilesystem

DJFS = {
    'type': 'osfs',
    'directory_root': 'lms/static/djpyfs',
    'url_root': '/static/djpyfs',
}

################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += [
    'lms.djangoapps.discussion.django_comment_client.utils.QueryCountDebugMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

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
    'debug_toolbar.panels.history.HistoryPanel',
    # ProfilingPanel has been intentionally removed for default devstack.py
    # runtimes for performance reasons. If you wish to re-enable it in your
    # local development environment, please create a new settings file
    # that imports and extends devstack.py.
)

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'lms.envs.devstack.should_show_debug_toolbar',
}


def should_show_debug_toolbar(request):  # lint-amnesty, pylint: disable=missing-function-docstring
    # We always want the toolbar on devstack unless running tests from another Docker container
    hostname = request.get_host()
    if hostname.startswith('edx.devstack.lms:') or hostname.startswith('lms.devstack.edx:'):
        return False
    return True

########################### PIPELINE #################################

PIPELINE['PIPELINE_ENABLED'] = False
STATICFILES_STORAGE = 'openedx.core.storage.DevelopmentStorage'

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Disable JavaScript compression in development
PIPELINE['JS_COMPRESSOR'] = None

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

PIPELINE['SASS_ARGUMENTS'] = '--debug-info'

# Load development webpack donfiguration
WEBPACK_CONFIG_PATH = 'webpack.dev.config.js'

########################### VERIFIED CERTIFICATES #################################

FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True

########################### External REST APIs #################################
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True
FEATURES['ENABLE_MOBILE_REST_API'] = True
FEATURES['ENABLE_VIDEO_ABSTRACTION_LAYER_API'] = True

########################## SECURITY #######################
FEATURES['ENABLE_MAX_FAILED_LOGIN_ATTEMPTS'] = False
FEATURES['SQUELCH_PII_IN_LOGS'] = False
FEATURES['PREVENT_CONCURRENT_LOGINS'] = False

########################### Milestones #################################
FEATURES['MILESTONES_APP'] = True

########################### Entrance Exams #################################
FEATURES['ENTRANCE_EXAMS'] = True

################################ COURSE LICENSES ################################
FEATURES['LICENSING'] = True


########################## Courseware Search #######################
FEATURES['ENABLE_COURSEWARE_SEARCH'] = False
FEATURES['ENABLE_COURSEWARE_SEARCH_FOR_COURSE_STAFF'] = True
SEARCH_ENGINE = 'search.elastic.ElasticSearchEngine'


########################## Dashboard Search #######################
FEATURES['ENABLE_DASHBOARD_SEARCH'] = False


########################## Certificates Web/HTML View #######################
FEATURES['CERTIFICATES_HTML_VIEW'] = True


########################## Course Discovery #######################
LANGUAGE_MAP = {
    'terms': dict(ALL_LANGUAGES),
    'name': 'Language',
}
COURSE_DISCOVERY_MEANINGS = {
    'org': {
        'name': 'Organization',
    },
    'modes': {
        'name': 'Course Type',
        'terms': {
            'honor': 'Honor',
            'verified': 'Verified',
        },
    },
    'language': LANGUAGE_MAP,
}

FEATURES['ENABLE_COURSE_DISCOVERY'] = False
# Setting for overriding default filtering facets for Course discovery
# COURSE_DISCOVERY_FILTERS = ["org", "language", "modes"]
FEATURES['COURSES_ARE_BROWSEABLE'] = True
HOMEPAGE_COURSE_MAX = 9

# Software secure fake page feature flag
FEATURES['ENABLE_SOFTWARE_SECURE_FAKE'] = True

# Setting for the testing of Software Secure Result Callback
VERIFY_STUDENT["SOFTWARE_SECURE"] = {
    "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
    "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
}
DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH = "verify_student_disable_account_activation_requirement"

# Skip enrollment start date filtering
SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True


########################## Shopping cart ##########################
FEATURES['ENABLE_COSMETIC_DISPLAY_PRICE'] = True

######################### Program Enrollments #####################
FEATURES['ENABLE_ENROLLMENT_RESET'] = True

########################## Third Party Auth #######################

if FEATURES.get('ENABLE_THIRD_PARTY_AUTH') and (
        'common.djangoapps.third_party_auth.dummy.DummyBackend' not in AUTHENTICATION_BACKENDS
):
    AUTHENTICATION_BACKENDS = ['common.djangoapps.third_party_auth.dummy.DummyBackend'] + list(AUTHENTICATION_BACKENDS)

############## ECOMMERCE API CONFIGURATION SETTINGS ###############
ECOMMERCE_PUBLIC_URL_ROOT = 'http://localhost:18130'
ECOMMERCE_API_URL = 'http://edx.devstack.ecommerce:18130/api/v2'

############## Comments CONFIGURATION SETTINGS ###############
COMMENTS_SERVICE_URL = 'http://edx.devstack.forum:4567'

############## Credentials CONFIGURATION SETTINGS ###############
CREDENTIALS_INTERNAL_SERVICE_URL = 'http://edx.devstack.credentials:18150'
CREDENTIALS_PUBLIC_SERVICE_URL = 'http://localhost:18150'

############## Exams CONFIGURATION SETTINGS ####################
EXAMS_SERVICE_URL = 'http://localhost:8740/api/v1'

TOKEN_SIGNING.update({
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "localdev_exam_token_key", "e": "AQAB", "kty": "RSA", "n": "o5cn3ljSRi6FaDEKTn0PS-oL9EFyv1pI'
        '7dRgffQLD1qf5D6sprmYfWWokSsrWig8u2y0HChSygR6Jn5KXBqQn6FpM0dDJLnWQDRXHLl3Ey1iPYgDSmOIsIGrV9ZyNCQwk03wAgWbfdBTig'
        '3QSDYD-sTNOs3pc4UD_PqAvU2nz_1SS2ZiOwOn5F6gulE1L0iE3KEUEvOIagfHNVhz0oxa_VRZILkzV-zr6R_TW1m97h4H8jXl_VJyQGyhMGGy'
        'puDrQ9_vaY_RLEulLCyY0INglHWQ7pckxBtI5q55-Vio2wgewe2_qYcGsnBGaDNbySAsvYcWRrqDiFyzrJYivodqTQ"}]}'
    )
})

############################### BLOCKSTORE #####################################
BLOCKSTORE_API_URL = "http://edx.devstack.blockstore:18250/api/v1/"

########################## PROGRAMS LEARNER PORTAL ##############################
LEARNER_PORTAL_URL_ROOT = 'http://localhost:8734'

########################## ENTERPRISE LEARNER PORTAL ##############################
ENTERPRISE_LEARNER_PORTAL_NETLOC = 'localhost:8734'
ENTERPRISE_LEARNER_PORTAL_BASE_URL = 'http://' + ENTERPRISE_LEARNER_PORTAL_NETLOC

########################## ENTERPRISE ADMIN PORTAL ##############################
ENTERPRISE_ADMIN_PORTAL_NETLOC = 'localhost:1991'
ENTERPRISE_ADMIN_PORTAL_BASE_URL = 'http://' + ENTERPRISE_ADMIN_PORTAL_NETLOC

########################## GRADEBOOK APP ##############################
WRITABLE_GRADEBOOK_URL = 'http://localhost:1994'

########################## ORA STAFF GRADING APP ##############################
ORA_GRADING_MICROFRONTEND_URL = 'http://localhost:1993'

########################## LEARNER HOME APP ##############################
LEARNER_HOME_MICROFRONTEND_URL = 'http://localhost:1996'

###################### Cross-domain requests ######################
FEATURES['ENABLE_CORS_HEADERS'] = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = ()
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = corsheaders_default_headers + (
    'use-jwt-cookie',
)

LOGIN_REDIRECT_WHITELIST.extend([
    CMS_BASE,
    # Allow redirection to all micro-frontends.
    # Please add your MFE if is not already listed here.
    # Note: For this to work, the MFE must set BASE_URL in its .env.development to:
    #   BASE_URL=http://localhost:$PORT
    # as opposed to:
    #   BASE_URL=localhost:$PORT
    'localhost:18000',  # lms
    'localhost:18130',  # ecommerce
    'localhost:1997',  # frontend-app-account
    'localhost:1976',  # frontend-app-program-console
    'localhost:1994',  # frontend-app-gradebook
    'localhost:2000',  # frontend-app-learning
    'localhost:2001',  # frontend-app-course-authoring
    'localhost:3001',  # frontend-app-library-authoring
    'localhost:18400',  # frontend-app-publisher
    'localhost:1993',  # frontend-app-ora-grading
    'localhost:1996',  # frontend-app-learner-dashboard
    ENTERPRISE_LEARNER_PORTAL_NETLOC,  # frontend-app-learner-portal-enterprise
    ENTERPRISE_ADMIN_PORTAL_NETLOC,  # frontend-app-admin-portal
])

###################### JWTs ######################
JWT_AUTH.update({
    'JWT_AUDIENCE': 'lms-key',
    'JWT_ISSUER': f'{LMS_ROOT_URL}/oauth2',
    'JWT_ISSUERS': [{
        'AUDIENCE': 'lms-key',
        'ISSUER': f'{LMS_ROOT_URL}/oauth2',
        'SECRET_KEY': 'lms-secret',
    }],
    'JWT_SECRET_KEY': 'lms-secret',
    'JWT_SIGNING_ALGORITHM': 'RS512',
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
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "devstack_key", "e": "AQAB", "kty": "RSA", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu'
        '48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC'
        '4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzG'
        'y5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw"}]}'
    ),
})
add_plugins(__name__, ProjectType.LMS, SettingsType.DEVSTACK)


######################### Django Rest Framework ########################

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += (
    'rest_framework.renderers.BrowsableAPIRenderer',
)

OPENAPI_CACHE_TIMEOUT = 0

#####################################################################
# set replica set of contentstore to none as we haven't setup any for lms in devstack
CONTENTSTORE['DOC_STORE_CONFIG']['replicaSet'] = None

#####################################################################
# set replica sets of moduelstore to none as we haven't setup any for lms in devstack
for store in MODULESTORE['default']['OPTIONS']['stores']:
    if 'DOC_STORE_CONFIG' in store and 'replicaSet' in store['DOC_STORE_CONFIG']:
        store['DOC_STORE_CONFIG']['replicaSet'] = None


#####################################################################
# Lastly, run any migrations, if needed.
MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)


SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

EDXNOTES_INTERNAL_API = 'http://edx.devstack.edxnotesapi:18120/api/v1'
EDXNOTES_CLIENT_NAME = 'edx_notes_api-backend-service'

############## Settings for Microfrontends  #########################
LEARNING_MICROFRONTEND_URL = 'http://localhost:2000'
ACCOUNT_MICROFRONTEND_URL = 'http://localhost:1997'
COMMUNICATIONS_MICROFRONTEND_URL = 'http://localhost:1984'
AUTHN_MICROFRONTEND_URL = 'http://localhost:1999'
AUTHN_MICROFRONTEND_DOMAIN = 'localhost:1999'

################### FRONTEND APPLICATION DISCUSSIONS ###################
DISCUSSIONS_MICROFRONTEND_URL = 'http://localhost:2002'

################### FRONTEND APPLICATION DISCUSSIONS FEEDBACK URL###################
DISCUSSIONS_MFE_FEEDBACK_URL = None

############## Docker based devstack settings #######################

FEATURES.update({
    'AUTOMATIC_AUTH_FOR_TESTING': True,
    'ENABLE_DISCUSSION_SERVICE': True,
    'SHOW_HEADER_LANGUAGE_SELECTOR': True,

    # Enable enterprise integration by default.
    # See https://github.com/openedx/edx-enterprise/blob/master/docs/development.rst for
    # more background on edx-enterprise.
    # Toggle this off if you don't want anything to do with enterprise in devstack.
    'ENABLE_ENTERPRISE_INTEGRATION': True,
})

ENABLE_MKTG_SITE = os.environ.get('ENABLE_MARKETING_SITE', False)
MARKETING_SITE_ROOT = os.environ.get('MARKETING_SITE_ROOT', 'http://localhost:8080')

MKTG_URLS = {
    'ABOUT': '/about',
    'ACCESSIBILITY': '/accessibility',
    'AFFILIATES': '/affiliate-program',
    'BLOG': '/blog',
    'CAREERS': '/careers',
    'CONTACT': '/support/contact_us',
    'COURSES': '/course',
    'DONATE': '/donate',
    'ENTERPRISE': '/enterprise',
    'FAQ': '/student-faq',
    'HONOR': '/edx-terms-service',
    'HOW_IT_WORKS': '/how-it-works',
    'MEDIA_KIT': '/media-kit',
    'NEWS': '/news-announcements',
    'PRESS': '/press',
    'PRIVACY': '/edx-privacy-policy',
    'ROOT': MARKETING_SITE_ROOT,
    'SCHOOLS': '/schools-partners',
    'SITE_MAP': '/sitemap',
    'TRADEMARKS': '/trademarks',
    'TOS': '/edx-terms-service',
    'TOS_AND_HONOR': '/edx-terms-service',
    'WHAT_IS_VERIFIED_CERT': '/verified-certificate',
}

ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS = {}

ENTERPRISE_BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = "http://edx.devstack.lms:18000/oauth2"

CREDENTIALS_SERVICE_USERNAME = 'credentials_worker'

COURSE_CATALOG_URL_ROOT = 'http://edx.devstack.discovery:18381'
COURSE_CATALOG_API_URL = f'{COURSE_CATALOG_URL_ROOT}/api/v1'

SYSTEM_WIDE_ROLE_CLASSES = os.environ.get("SYSTEM_WIDE_ROLE_CLASSES", SYSTEM_WIDE_ROLE_CLASSES)
SYSTEM_WIDE_ROLE_CLASSES.append(
    'system_wide_roles.SystemWideRoleAssignment',
)

if FEATURES.get('ENABLE_ENTERPRISE_INTEGRATION'):
    SYSTEM_WIDE_ROLE_CLASSES.append(
        'enterprise.SystemWideEnterpriseUserRoleAssignment',
    )

#####################################################################

# django-session-cookie middleware
DCS_SESSION_COOKIE_SAMESITE = 'Lax'
DCS_SESSION_COOKIE_SAMESITE_FORCE_ALL = True

########################## THEMING  #######################
# If you want to enable theming in devstack, uncomment this section and add any relevant
# theme directories to COMPREHENSIVE_THEME_DIRS

# We have to import the private method here because production.py calls
# derive_settings('lms.envs.production') which runs _make_mako_template_dirs with
# the settings from production, which doesn't include these theming settings. Thus,
# the templating engine is unable to find the themed templates because they don't exist
# in it's path. Re-calling derive_settings doesn't work because the settings was already
# changed from a function to a list, and it can't be derived again.

# from .common import _make_mako_template_dirs
# ENABLE_COMPREHENSIVE_THEMING = True
# COMPREHENSIVE_THEME_DIRS = [
#     "/edx/app/edxapp/edx-platform/themes/"
# ]
# TEMPLATES[1]["DIRS"] = _make_mako_template_dirs
# derive_settings(__name__)

# Uncomment the lines below if you'd like to see SQL statements in your devstack LMS log.
# LOGGING['handlers']['console']['level'] = 'DEBUG'
# LOGGING['loggers']['django.db.backends'] = {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False}

################### Special Exams (Proctoring) and Prereqs ###################
FEATURES['ENABLE_SPECIAL_EXAMS'] = True
FEATURES['ENABLE_PREREQUISITE_COURSES'] = True

# Used in edx-proctoring for ID generation in lieu of SECRET_KEY - dummy value
# (ref MST-637)
PROCTORING_USER_OBFUSCATION_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

#################### Webpack Configuration Settings ##############################
WEBPACK_LOADER['DEFAULT']['TIMEOUT'] = 5

#################### Network configuration ####################
# Devstack is directly exposed to the caller
CLOSEST_CLIENT_IP_FROM_HEADERS = []

#################### Event bus backend ########################
EVENT_BUS_PRODUCER = 'edx_event_bus_kafka.create_producer'
EVENT_BUS_KAFKA_SCHEMA_REGISTRY_URL = 'http://edx.devstack.schema-registry:8081'
EVENT_BUS_KAFKA_BOOTSTRAP_SERVERS = 'edx.devstack.kafka:29092'
EVENT_BUS_TOPIC_PREFIX = 'dev'

################# New settings must go ABOVE this line #################
########################################################################
# See if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error,wildcard-import
