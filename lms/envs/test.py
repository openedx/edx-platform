"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /edx-platform  # The location of this repo
        /log  # Where we're going to write log files
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import


import logging
from collections import OrderedDict
from uuid import uuid4

import openid.oidutil
from django.utils.translation import gettext_lazy
from edx_django_utils.plugins import add_plugins
from path import Path as path

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType
from openedx.core.lib.derived import derive_settings
from openedx.core.lib.tempdir import mkdtemp_clean
from xmodule.modulestore.modulestore_settings import update_module_store_settings

from .common import *

from common.djangoapps.util.testing import patch_sessions, patch_testcase  # pylint: disable=wrong-import-order

# This patch disables the commit_on_success decorator during tests
# in TestCase subclasses.
patch_testcase()
patch_sessions()

# Allow all hosts during tests, we use a lot of different ones all over the codebase.
ALLOWED_HOSTS = [
    '*'
]

# Silence noisy logs to make troubleshooting easier when tests fail.
LOG_OVERRIDES = [
    ('factory.generate', logging.ERROR),
    ('factory.containers', logging.ERROR),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# mongo connection settings
MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

THIS_UUID = uuid4().hex[:5]

FEATURES['DISABLE_SET_JWT_COOKIES_FOR_TESTS'] = True

# can't test start dates with this True, but on the other hand,
# can test everything else :)
FEATURES['DISABLE_START_DATES'] = True

# Most tests don't use the discussion service, so we turn it off to speed them up.
# Tests that do can enable this flag, but must use the UrlResetMixin class to force urls.py
# to reload. For consistency in user-experience, keep the value of this setting in sync with
# the one in cms/envs/test.py
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

FEATURES['ENABLE_SERVICE_STATUS'] = True

FEATURES['ENABLE_VERIFIED_CERTIFICATES'] = True

# Toggles embargo on for testing
FEATURES['EMBARGO'] = True

# Enable the milestones app in tests to be consistent with it being enabled in production
FEATURES['MILESTONES_APP'] = True

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

FEATURES['ENABLE_BULK_ENROLLMENT_VIEW'] = True

FEATURES['ENABLE_BULK_USER_RETIREMENT'] = True

DEFAULT_MOBILE_AVAILABLE = True

# Need wiki for courseware views to work. TODO (vshnayder): shouldn't need it.
WIKI_ENABLED = True

# Enable a parental consent age limit for testing
PARENTAL_CONSENT_AGE_LIMIT = 13

# Local Directories
TEST_ROOT = path("test_root")
# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

STATUS_MESSAGE_PATH = TEST_ROOT / "status_message.json"

COURSES_ROOT = TEST_ROOT / "data"
DATA_DIR = COURSES_ROOT

COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"
# Where the content data is checked out.  This may not exist on jenkins.
GITHUB_REPO_ROOT = ENV_ROOT / "data"

USE_I18N = True
LANGUAGE_CODE = 'en'  # tests assume they will get English.

XQUEUE_INTERFACE = {
    "url": "http://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds

# Don't rely on a real staff grading backend
MOCK_STAFF_GRADING = True
MOCK_PEER_GRADING = True

COMMENTS_SERVICE_URL = 'http://localhost:4567'

DJFS = {
    'type': 'osfs',
    'directory_root': f'{DATA_DIR}/django-pyfs/static/django-pyfs',
    'url_root': '/static/django-pyfs',
}

############################ STATIC FILES #############################

# TODO (cpennington): We need to figure out how envs/test.py can inject things
# into common.py so that we don't have to repeat this sort of thing
STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
]
STATICFILES_DIRS += [
    (course_dir, COMMON_TEST_DATA_ROOT / course_dir)
    for course_dir in os.listdir(COMMON_TEST_DATA_ROOT)
    if os.path.isdir(COMMON_TEST_DATA_ROOT / course_dir)
]

# Avoid having to run collectstatic before the unit test suite
# If we don't add these settings, then Django templates that can't
# find pipelined assets will raise a ValueError.
# http://stackoverflow.com/questions/12816941/unit-testing-with-django-pipeline
STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'

# Don't use compression during tests
PIPELINE['JS_COMPRESSOR'] = None

update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'fs_root': TEST_ROOT / "data",
    },
    xml_store_options={
        'data_dir': mkdtemp_clean(dir=TEST_ROOT),  # never inadvertently load all the XML courses
    },
    doc_store_settings={
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'db': f'test_xmodule_{THIS_UUID}',
        'collection': 'test_modulestore',
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': f'test_xcontent_{THIS_UUID}',
        'port': MONGO_PORT_NUM,
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'ATOMIC_REQUESTS': True,
    },
    'student_module_history': {
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

CACHES = {
    # This is the cache used for most things.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },

    # The general cache is what you get if you use our util.cache. It's used for
    # things like caching the course.xml file for different A/B test groups.
    # We set it to be a DummyCache to force reloading of course.xml in dev.
    # In staging environments, we would grab VERSION from data uploaded by the
    # push process.
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },

    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'course_structure_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    # Blockstore caching tests require a cache that actually works:
    'blockstore': {
        'KEY_PREFIX': 'blockstore',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': 'edx_loc_mem_cache',
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

############################### BLOCKSTORE #####################################
# Blockstore tests
RUN_BLOCKSTORE_TESTS = os.environ.get('EDXAPP_RUN_BLOCKSTORE_TESTS', 'no').lower() in ('true', 'yes', '1')
BLOCKSTORE_API_URL = os.environ.get('EDXAPP_BLOCKSTORE_API_URL', "http://edx.devstack.blockstore-test:18251/api/v1/")
BLOCKSTORE_API_AUTH_TOKEN = os.environ.get('EDXAPP_BLOCKSTORE_API_AUTH_TOKEN', 'edxapp-test-key')
XBLOCK_RUNTIME_V2_EPHEMERAL_DATA_CACHE = 'blockstore'  # This must be set to a working cache for the tests to pass

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

############################# SECURITY SETTINGS ################################
# Default to advanced security in common.py, so tests can reset here to use
# a simpler security model
FEATURES['ENFORCE_PASSWORD_POLICY'] = False
FEATURES['ENABLE_MAX_FAILED_LOGIN_ATTEMPTS'] = False
FEATURES['SQUELCH_PII_IN_LOGS'] = False
FEATURES['PREVENT_CONCURRENT_LOGINS'] = False

######### Third-party auth ##########
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.azuread.AzureADOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'common.djangoapps.third_party_auth.identityserver3.IdentityServer3',
    'common.djangoapps.third_party_auth.dummy.DummyBackend',
    'common.djangoapps.third_party_auth.saml.SAMLAuthBackend',
    'common.djangoapps.third_party_auth.lti.LTIAuthBackend',
] + AUTHENTICATION_BACKENDS

THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS = {
    'custom1': {
        'secret_key': 'opensesame',
        'url': '/misc/my-custom-registration-form',
        'error_url': '/misc/my-custom-sso-error-page'
    },
}

############################## OAUTH2 Provider ################################
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True
OAUTH_ENFORCE_SECURE = False

########################### External REST APIs #################################
FEATURES['ENABLE_MOBILE_REST_API'] = True
FEATURES['ENABLE_VIDEO_ABSTRACTION_LAYER_API'] = True

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'django-cache'

CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = False

######################### MARKETING SITE ###############################

MKTG_URL_LINK_MAP = {
    'ABOUT': 'about',
    'CONTACT': 'contact',
    'HELP_CENTER': 'help-center',
    'COURSES': 'courses',
    'ROOT': 'root',
    'TOS': 'tos',
    'HONOR': 'honor',
    'PRIVACY': 'privacy',
    'CAREERS': 'careers',
    'NEWS': 'news',
    'PRESS': 'press',
    'BLOG': 'blog',
    'DONATE': 'donate',
    'SITEMAP.XML': 'sitemap_xml',

    # Verified Certificates
    'WHAT_IS_VERIFIED_CERT': 'verified-certificate',
}

SUPPORT_SITE_LINK = 'https://example.support.edx.org'
PASSWORD_RESET_SUPPORT_LINK = 'https://support.example.com/password-reset-help.html'
ACTIVATION_EMAIL_SUPPORT_LINK = 'https://support.example.com/activation-email-help.html'
LOGIN_ISSUE_SUPPORT_LINK = 'https://support.example.com/login-issue-help.html'
ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS = OrderedDict([
    ("utm_campaign", "edX.org Referral"),
    ("utm_source", "edX.org"),
    ("utm_medium", "Footer"),
])

############################ STATIC FILES #############################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))

_NEW_STATICFILES_DIRS = []
# Strip out any static files that aren't in the repository root
# so that the tests can run with only the edx-platform directory checked out
for static_dir in STATICFILES_DIRS:
    # Handle both tuples and non-tuple directory definitions
    try:
        _, data_dir = static_dir
    except ValueError:
        data_dir = static_dir

    if data_dir.startswith(REPO_ROOT):
        _NEW_STATICFILES_DIRS.append(static_dir)
STATICFILES_DIRS = _NEW_STATICFILES_DIRS

FILE_UPLOAD_TEMP_DIR = TEST_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

BLOCK_STRUCTURES_SETTINGS['PRUNING_ACTIVE'] = True

########################### Server Ports ###################################

# These ports are carefully chosen so that if the browser needs to
# access them, they will be available through the SauceLabs SSH tunnel
XQUEUE_PORT = 8040
YOUTUBE_PORT = 8031
LTI_PORT = 8765
VIDEO_SOURCE_PORT = 8777

FEATURES['PREVIEW_LMS_BASE'] = "preview.localhost"
############### Module Store Items ##########
PREVIEW_DOMAIN = FEATURES['PREVIEW_LMS_BASE'].split(':')[0]
HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS = {
    PREVIEW_DOMAIN: 'draft-preferred'
}


################### Make tests faster

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

### This enables the Metrics tab for the Instructor dashboard ###########
FEATURES['CLASS_DASHBOARD'] = True

################### Make tests quieter

# OpenID spews messages like this to stderr, we don't need to see them:
# Generated checkid_setup request to http://testserver/openid/provider/login/
# With assocication {HMAC-SHA1}{51d49995}{s/kRmA==}

openid.oidutil.log = lambda message, level=0: None


# Include a non-ascii character in PLATFORM_NAME and PLATFORM_DESCRIPTION to uncover possible
# UnicodeEncodeErrors in tests. Also use lazy text to reveal possible json dumps errors
PLATFORM_NAME = gettext_lazy("édX")
PLATFORM_DESCRIPTION = gettext_lazy("Open édX Platform")

SITE_NAME = "edx.org"

TEST_THEME = COMMON_ROOT / "test" / "test-theme"

# add extra template directory for test-only templates
MAKO_TEMPLATE_DIRS_BASE.extend([
    COMMON_ROOT / 'test' / 'templates',
    COMMON_ROOT / 'test' / 'test_sites',
    REPO_ROOT / 'openedx' / 'core' / 'djangolib' / 'tests' / 'templates',
])


# Setting for the testing of Software Secure Result Callback
VERIFY_STUDENT["SOFTWARE_SECURE"] = {
    "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
    "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
}

VIDEO_CDN_URL = {
    'CN': 'http://api.xuetangx.com/edx/video?s3_url='
}

######### dashboard git log settings #########
MONGODB_LOG = {
    'host': MONGO_HOST,
    'port': MONGO_PORT_NUM,
    'user': '',
    'password': '',
    'db': 'xlog',
}

NOTES_DISABLED_TABS = []

# Enable EdxNotes for tests.
FEATURES['ENABLE_EDXNOTES'] = True

# Enable courseware search for tests
FEATURES['ENABLE_COURSEWARE_SEARCH'] = True

# Enable dashboard search for tests
FEATURES['ENABLE_DASHBOARD_SEARCH'] = True

# Use MockSearchEngine as the search engine for test scenario
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"

FACEBOOK_APP_SECRET = "Test"
FACEBOOK_APP_ID = "Test"
FACEBOOK_API_VERSION = "v2.8"

####################### ELASTICSEARCH TESTS #######################
# Enable this when testing elasticsearch-based code which couldn't be tested using the mock engine
ENABLE_ELASTICSEARCH_FOR_TESTS = os.environ.get(
    'EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS', 'no').lower() in ('true', 'yes', '1')

TEST_ELASTICSEARCH_USE_SSL = os.environ.get(
    'EDXAPP_TEST_ELASTICSEARCH_USE_SSL', 'no').lower() in ('true', 'yes', '1')
TEST_ELASTICSEARCH_HOST = os.environ.get('EDXAPP_TEST_ELASTICSEARCH_HOST', 'edx.devstack.elasticsearch710')
TEST_ELASTICSEARCH_PORT = int(os.environ.get('EDXAPP_TEST_ELASTICSEARCH_PORT', '9200'))

######### custom courses #########
INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
FEATURES['CUSTOM_COURSES_EDX'] = True

# Set dummy values for profile image settings.
PROFILE_IMAGE_BACKEND = {
    'class': 'openedx.core.storage.OverwriteStorage',
    'options': {
        'location': MEDIA_ROOT,
        'base_url': 'http://example-storage.com/profile-images/',
    },
}
PROFILE_IMAGE_DEFAULT_FILENAME = 'default'
PROFILE_IMAGE_DEFAULT_FILE_EXTENSION = 'png'
PROFILE_IMAGE_HASH_SEED = 'secret'
PROFILE_IMAGE_MAX_BYTES = 1024 * 1024
PROFILE_IMAGE_MIN_BYTES = 100

# Enable the LTI provider feature for testing
FEATURES['ENABLE_LTI_PROVIDER'] = True
INSTALLED_APPS.append('lms.djangoapps.lti_provider.apps.LtiProviderConfig')
AUTHENTICATION_BACKENDS.append('lms.djangoapps.lti_provider.users.LtiBackend')

# Financial assistance page
FEATURES['ENABLE_FINANCIAL_ASSISTANCE_FORM'] = True

COURSE_BLOCKS_API_EXTRA_FIELDS = [
    ('course', 'course_visibility'),
    ('course', 'other_course_settings'),
]

COURSE_CATALOG_URL_ROOT = 'https://catalog.example.com'
COURSE_CATALOG_API_URL = f'{COURSE_CATALOG_URL_ROOT}/api/v1'

COMPREHENSIVE_THEME_DIRS = [REPO_ROOT / "themes", REPO_ROOT / "common/test"]
COMPREHENSIVE_THEME_LOCALE_PATHS = [REPO_ROOT / "themes/conf/locale", ]
ENABLE_COMPREHENSIVE_THEMING = True

LMS_ROOT_URL = "http://localhost:8000"

# Needed for derived settings used by cms only.
FRONTEND_LOGIN_URL = '/login'
FRONTEND_LOGOUT_URL = '/logout'
FRONTEND_REGISTER_URL = '/register'

# Programs Learner Portal URL
LEARNER_PORTAL_URL_ROOT = 'http://localhost:8734'

ECOMMERCE_API_URL = 'https://ecommerce.example.com/api/v2/'
ECOMMERCE_PUBLIC_URL_ROOT = None
ENTERPRISE_API_URL = 'http://enterprise.example.com/enterprise/api/v1/'
ENTERPRISE_CONSENT_API_URL = 'http://enterprise.example.com/consent/api/v1/'

ACTIVATION_EMAIL_FROM_ADDRESS = 'test_activate@edx.org'

TEMPLATES[0]['OPTIONS']['debug'] = True
TEMPLATES.append(
    {
        # This separate copy of the Mako backend is used to test rendering previews in the 'lms.main' namespace
        'NAME': 'preview',
        'BACKEND': 'common.djangoapps.edxmako.backend.Mako',
        'APP_DIRS': False,
        'DIRS': MAKO_TEMPLATE_DIRS_BASE,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
            'debug': False,
            'namespace': 'lms.main',
        }
    }
)

########################## VIDEO TRANSCRIPTS STORAGE ############################
VIDEO_TRANSCRIPTS_SETTINGS = dict(
    VIDEO_TRANSCRIPTS_MAX_BYTES=3 * 1024 * 1024,    # 3 MB
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-transcripts/',
)

####################### Authentication Settings ##########################
JWT_AUTH.update({
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "BTZ9HA6K", "e": "AQAB", "kty": "RSA", "n": "o5cn3ljSRi6FaDEKTn0PS-oL9EFyv1pI7dRgffQLD1qf5D6'
        'sprmYfWWokSsrWig8u2y0HChSygR6Jn5KXBqQn6FpM0dDJLnWQDRXHLl3Ey1iPYgDSmOIsIGrV9ZyNCQwk03wAgWbfdBTig3QSDYD-sTNOs3pc'
        '4UD_PqAvU2nz_1SS2ZiOwOn5F6gulE1L0iE3KEUEvOIagfHNVhz0oxa_VRZILkzV-zr6R_TW1m97h4H8jXl_VJyQGyhMGGypuDrQ9_vaY_RLEu'
        'lLCyY0INglHWQ7pckxBtI5q55-Vio2wgewe2_qYcGsnBGaDNbySAsvYcWRrqDiFyzrJYivodqTQ"}]}'
    ),
    'JWT_PRIVATE_SIGNING_JWK': (
        '{"e": "AQAB", "d": "HIiV7KNjcdhVbpn3KT-I9n3JPf5YbGXsCIedmPqDH1d4QhBofuAqZ9zebQuxkRUpmqtYMv0Zi6ECSUqH387GYQF_Xv'
        'FUFcjQRPycISd8TH0DAKaDpGr-AYNshnKiEtQpINhcP44I1AYNPCwyoxXA1fGTtmkKChsuWea7o8kytwU5xSejvh5-jiqu2SF4GEl0BEXIAPZs'
        'gbzoPIWNxgO4_RzNnWs6nJZeszcaDD0CyezVSuH9QcI6g5QFzAC_YuykSsaaFJhZ05DocBsLczShJ9Omf6PnK9xlm26I84xrEh_7x4fVmNBg3x'
        'WTLh8qOnHqGko93A1diLRCrKHOvnpvgQ", "n": "o5cn3ljSRi6FaDEKTn0PS-oL9EFyv1pI7dRgffQLD1qf5D6sprmYfWWokSsrWig8u2y0H'
        'ChSygR6Jn5KXBqQn6FpM0dDJLnWQDRXHLl3Ey1iPYgDSmOIsIGrV9ZyNCQwk03wAgWbfdBTig3QSDYD-sTNOs3pc4UD_PqAvU2nz_1SS2ZiOwO'
        'n5F6gulE1L0iE3KEUEvOIagfHNVhz0oxa_VRZILkzV-zr6R_TW1m97h4H8jXl_VJyQGyhMGGypuDrQ9_vaY_RLEulLCyY0INglHWQ7pckxBtI5'
        'q55-Vio2wgewe2_qYcGsnBGaDNbySAsvYcWRrqDiFyzrJYivodqTQ", "q": "3T3DEtBUka7hLGdIsDlC96Uadx_q_E4Vb1cxx_4Ss_wGp1Lo'
        'z3N3ZngGyInsKlmbBgLo1Ykd6T9TRvRNEWEtFSOcm2INIBoVoXk7W5RuPa8Cgq2tjQj9ziGQ08JMejrPlj3Q1wmALJr5VTfvSYBu0WkljhKNCy'
        '1KB6fCby0C9WE", "p": "vUqzWPZnDG4IXyo-k5F0bHV0BNL_pVhQoLW7eyFHnw74IOEfSbdsMspNcPSFIrtgPsn7981qv3lN_staZ6JflKfH'
        'ayjB_lvltHyZxfl0dvruShZOx1N6ykEo7YrAskC_qxUyrIvqmJ64zPW3jkuOYrFs7Ykj3zFx3Zq1H5568G0", "kid": "BTZ9HA6K", "kty"'
        ': "RSA"}'
    ),
})
# pylint: enable=unicode-format-string  # lint-amnesty, pylint: disable=bad-option-value
####################### Plugin Settings ##########################

add_plugins(__name__, ProjectType.LMS, SettingsType.TEST)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = os.environ.get("SYSTEM_WIDE_ROLE_CLASSES", [])

###################### Grade Downloads ######################
# These keys are used for all of our asynchronous downloadable files, including
# the ones that contain information other than grades.

GRADES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': '/tmp/edx-s3/grades',
}

# Configuration used for generating PDF Receipts/Invoices

PDF_RECEIPT_TAX_ID = 'add here'
PDF_RECEIPT_FOOTER_TEXT = 'add your own specific footer text here'
PDF_RECEIPT_DISCLAIMER_TEXT = 'add your own specific disclaimer text here'
PDF_RECEIPT_BILLING_ADDRESS = 'add your own billing address here with appropriate line feed characters'
PDF_RECEIPT_TERMS_AND_CONDITIONS = 'add your own terms and conditions'
PDF_RECEIPT_TAX_ID_LABEL = 'Tax ID'

PROFILE_MICROFRONTEND_URL = "http://profile-mfe/abc/"
ORDER_HISTORY_MICROFRONTEND_URL = "http://order-history-mfe/"
ACCOUNT_MICROFRONTEND_URL = "http://account-mfe"
AUTHN_MICROFRONTEND_URL = "http://authn-mfe"
AUTHN_MICROFRONTEND_DOMAIN = "authn-mfe"
LEARNING_MICROFRONTEND_URL = "http://learning-mfe"

########################## limiting dashboard courses ######################

DASHBOARD_COURSE_LIMIT = 250

########################## Settings for proctoring ######################
PROCTORING_SETTINGS = {
    'LINK_URLS': {
        'faq': 'https://support.example.com/proctoring-faq.html'
    }
}
PROCTORING_USER_OBFUSCATION_KEY = 'test_key'

# Used in edx-proctoring for ID generation in lieu of SECRET_KEY - dummy value
# (ref MST-637)
PROCTORING_USER_OBFUSCATION_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

############### Settings for Django Rate limit #####################

RATELIMIT_RATE = '2/m'

##### LOGISTRATION RATE LIMIT SETTINGS #####
LOGISTRATION_RATELIMIT_RATE = '5/5m'
LOGISTRATION_PER_EMAIL_RATELIMIT_RATE = '6/5m'
LOGISTRATION_API_RATELIMIT = '5/m'
LOGIN_AND_REGISTER_FORM_RATELIMIT = '5/5m'

REGISTRATION_VALIDATION_RATELIMIT = '5/minute'
REGISTRATION_RATELIMIT = '5/minute'

RESET_PASSWORD_TOKEN_VALIDATE_API_RATELIMIT = '2/m'
RESET_PASSWORD_API_RATELIMIT = '2/m'

CORS_ORIGIN_WHITELIST = ['https://sandbox.edx.org']

# enable /api/v1/save/course/ api for testing
ENABLE_SAVE_FOR_LATER = True

# rate limit for /api/v1/save/course/ api
SAVE_FOR_LATER_IP_RATE_LIMIT = '5/d'
SAVE_FOR_LATER_EMAIL_RATE_LIMIT = '5/m'
