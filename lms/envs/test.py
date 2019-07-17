# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

import logging
import os
from collections import OrderedDict
from random import choice
from string import digits, ascii_letters, punctuation
from uuid import uuid4

import openid.oidutil
from django.utils.translation import ugettext_lazy
from path import Path as path
from six.moves import range

from openedx.core.djangoapps.plugins import plugin_settings, constants as plugin_constants
from openedx.core.lib.derived import derive_settings
from openedx.core.lib.tempdir import mkdtemp_clean

from .common import *

from util.db import NoOpMigrationModules  # pylint: disable=wrong-import-order
from util.testing import patch_sessions, patch_testcase  # pylint: disable=wrong-import-order

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

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000-9000'

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

FEATURES['ENABLE_SHOPPING_CART'] = True

FEATURES['ENABLE_VERIFIED_CERTIFICATES'] = True

# Toggles embargo on for testing
FEATURES['EMBARGO'] = True

FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = True

# Enable the milestones app in tests to be consistent with it being enabled in production
FEATURES['MILESTONES_APP'] = True

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

FEATURES['ENABLE_BULK_ENROLLMENT_VIEW'] = True

FEATURES['ENABLE_API_DOCS'] = True

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
    'directory_root': '{}/django-pyfs/static/django-pyfs'.format(DATA_DIR),
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
        'db': 'test_xmodule_{}'.format(THIS_UUID),
        'collection': 'test_modulestore',
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': 'test_xcontent_{}'.format(THIS_UUID),
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

if os.environ.get('DISABLE_MIGRATIONS'):
    # Create tables directly from apps' models. This can be removed once we upgrade
    # to Django 1.9, which allows setting MIGRATION_MODULES to None in order to skip migrations.
    MIGRATION_MODULES = NoOpMigrationModules()

# Make sure we test with the extended history table
FEATURES['ENABLE_CSMH_EXTENDED'] = True
INSTALLED_APPS.append('coursewarehistoryextended')

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
}

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
    'third_party_auth.dummy.DummyBackend',
    'third_party_auth.saml.SAMLAuthBackend',
    'third_party_auth.lti.LTIAuthBackend',
] + AUTHENTICATION_BACKENDS

THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS = {
    'custom1': {
        'secret_key': 'opensesame',
        'url': '/misc/my-custom-registration-form',
        'error_url': '/misc/my-custom-sso-error-page'
    },
}

OPENID_CREATE_USERS = False
OPENID_UPDATE_DETAILS_FROM_SREG = True
OPENID_USE_AS_ADMIN_LOGIN = False
OPENID_PROVIDER_TRUSTED_ROOTS = ['*']

############################## OAUTH2 Provider ################################
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True
# don't cache courses for testing
OIDC_COURSE_HANDLER_CACHE_TIMEOUT = 0
OAUTH_ENFORCE_SECURE = False

########################### External REST APIs #################################
FEATURES['ENABLE_MOBILE_REST_API'] = True
FEATURES['ENABLE_VIDEO_ABSTRACTION_LAYER_API'] = True

###################### Payment ##############################3
# Enable fake payment processing page
FEATURES['ENABLE_PAYMENT_FAKE'] = True

# Configure the payment processor to use the fake processing page
# Since both the fake payment page and the shoppingcart app are using
# the same settings, we can generate this randomly and guarantee
# that they are using the same secret.
RANDOM_SHARED_SECRET = ''.join(
    choice(ascii_letters + digits + punctuation)
    for x in range(250)
)

CC_PROCESSOR_NAME = 'CyberSource2'
CC_PROCESSOR['CyberSource2']['SECRET_KEY'] = RANDOM_SHARED_SECRET
CC_PROCESSOR['CyberSource2']['ACCESS_KEY'] = "0123456789012345678901"
CC_PROCESSOR['CyberSource2']['PROFILE_ID'] = "edx"
CC_PROCESSOR['CyberSource2']['PURCHASE_ENDPOINT'] = "/shoppingcart/payment_fake"

FEATURES['STORE_BILLING_INFO'] = True

########################### SYSADMIN DASHBOARD ################################
FEATURES['ENABLE_SYSADMIN_DASHBOARD'] = True
GIT_REPO_DIR = TEST_ROOT / "course_repos"

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

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

SUPPORT_SITE_LINK = 'https://support.example.com'
PASSWORD_RESET_SUPPORT_LINK = 'https://support.example.com/password-reset-help.html'
ACTIVATION_EMAIL_SUPPORT_LINK = 'https://support.example.com/activation-email-help.html'
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
PLATFORM_NAME = ugettext_lazy(u"édX")
PLATFORM_DESCRIPTION = ugettext_lazy(u"Open édX Platform")

SITE_NAME = "edx.org"

# set up some testing for microsites
FEATURES['USE_MICROSITES'] = True
MICROSITE_ROOT_DIR = COMMON_ROOT / 'test' / 'test_sites'
MICROSITE_CONFIGURATION = {
    "test_site": {
        "domain_prefix": "test-site",
        "university": "test_site",
        "platform_name": "Test Site",
        "logo_image_url": "test_site/images/header-logo.png",
        "email_from_address": "test_site@edx.org",
        "ACTIVATION_EMAIL_FROM_ADDRESS": "test_activate@edx.org",
        "payment_support_email": "test_site@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "test_site.localhost",
        "course_org_filter": "TestSiteX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_site/css/test_site.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "This is a Test Site Overlay Text.",
        "course_index_overlay_logo_file": "test_site/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Test Site Overlay HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
        "COURSE_CATALOG_VISIBILITY_PERMISSION": "see_in_catalog",
        "COURSE_ABOUT_VISIBILITY_PERMISSION": "see_about_page",
        "ENABLE_SHOPPING_CART": True,
        "ENABLE_PAID_COURSE_REGISTRATION": True,
        "SESSION_COOKIE_DOMAIN": "test_site.localhost",
        "LINKEDIN_COMPANY_ID": "test",
        "FACEBOOK_APP_ID": "12345678908",
        "urls": {
            'ABOUT': 'test-site/about',
            'PRIVACY': 'test-site/privacy',
            'TOS_AND_HONOR': 'test-site/tos-and-honor',
        },
    },
    "site_with_logistration": {
        "domain_prefix": "logistration",
        "university": "logistration",
        "platform_name": "Test logistration",
        "logo_image_url": "test_site/images/header-logo.png",
        "email_from_address": "test_site@edx.org",
        "ACTIVATION_EMAIL_FROM_ADDRESS": "test_activate@edx.org",
        "payment_support_email": "test_site@edx.org",
        "ENABLE_MKTG_SITE": False,
        "ENABLE_COMBINED_LOGIN_REGISTRATION": True,
        "SITE_NAME": "test_site.localhost",
        "course_org_filter": "LogistrationX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_site/css/test_site.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "Logistration.",
        "course_index_overlay_logo_file": "test_site/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Logistration HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
        "COURSE_CATALOG_VISIBILITY_PERMISSION": "see_in_catalog",
        "COURSE_ABOUT_VISIBILITY_PERMISSION": "see_about_page",
        "ENABLE_SHOPPING_CART": True,
        "ENABLE_PAID_COURSE_REGISTRATION": True,
        "SESSION_COOKIE_DOMAIN": "test_logistration.localhost",
    },
    "default": {
        "university": "default_university",
        "domain_prefix": "www",
    }
}

MICROSITE_TEST_HOSTNAME = 'test-site.testserver'
MICROSITE_LOGISTRATION_HOSTNAME = 'logistration.testserver'

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

######### custom courses #########
INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
FEATURES['CUSTOM_COURSES_EDX'] = True

# Set dummy values for profile image settings.
PROFILE_IMAGE_BACKEND = {
    'class': 'storages.backends.overwrite.OverwriteStorage',
    'options': {
        'location': MEDIA_ROOT,
        'base_url': 'http://example-storage.com/profile-images/',
    },
}
PROFILE_IMAGE_DEFAULT_FILENAME = 'default'
PROFILE_IMAGE_DEFAULT_FILE_EXTENSION = 'png'
PROFILE_IMAGE_SECRET_KEY = 'secret'
PROFILE_IMAGE_MAX_BYTES = 1024 * 1024
PROFILE_IMAGE_MIN_BYTES = 100

# Enable the LTI provider feature for testing
FEATURES['ENABLE_LTI_PROVIDER'] = True
INSTALLED_APPS.append('lti_provider.apps.LtiProviderConfig')
AUTHENTICATION_BACKENDS.append('lti_provider.users.LtiBackend')

# ORGANIZATIONS
FEATURES['ORGANIZATIONS_APP'] = True

# Financial assistance page
FEATURES['ENABLE_FINANCIAL_ASSISTANCE_FORM'] = True

COURSE_CATALOG_API_URL = 'https://catalog.example.com/api/v1'

COMPREHENSIVE_THEME_DIRS = [REPO_ROOT / "themes", REPO_ROOT / "common/test"]
COMPREHENSIVE_THEME_LOCALE_PATHS = [REPO_ROOT / "themes/conf/locale", ]
ENABLE_COMPREHENSIVE_THEMING = True

LMS_ROOT_URL = "http://localhost:8000"

FRONTEND_LOGOUT_URL = LMS_ROOT_URL + '/logout'

ECOMMERCE_API_URL = 'https://ecommerce.example.com/api/v2/'
ECOMMERCE_PUBLIC_URL_ROOT = None
ENTERPRISE_API_URL = 'http://enterprise.example.com/enterprise/api/v1/'
ENTERPRISE_CONSENT_API_URL = 'http://enterprise.example.com/consent/api/v1/'

ACTIVATION_EMAIL_FROM_ADDRESS = 'test_activate@edx.org'

TEMPLATES[0]['OPTIONS']['debug'] = True

########################### DRF default throttle rates ############################
# Increasing rates to enable test cases hitting registration view succesfully.
# Lower rate is causing view to get blocked, causing test case failure.
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['registration_validation'] = '100/minute'

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
# pylint: disable=unicode-format-string
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
# pylint: enable=unicode-format-string
####################### Plugin Settings ##########################

plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.LMS, plugin_constants.SettingsType.TEST)

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
ACCOUNT_MICROFRONTEND_URL = "http://account-mfe/"

########################## limiting dashboard courses ######################

DASHBOARD_COURSE_LIMIT = 250
