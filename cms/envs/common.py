# -*- coding: utf-8 -*-
"""
This is the common settings file, intended to set sane defaults. If you have a
piece of configuration that's dependent on a set of feature flags being set,
then create a function that returns the calculated value based on the value of
FEATURES[...]. Modules that extend this one can change the feature
configuration in an environment specific config file and re-calculate those
values.

We should make a method that calls all these config methods so that you just
make one call at the end of your site-specific dev file to reset all the
dependent variables (like INSTALLED_APPS) for you.

Longer TODO:
1. Right now our treatment of static content in general and in particular
   course-specific static content is haphazard.
2. We should have a more disciplined approach to feature flagging, even if it
   just means that we stick them in a dict called FEATURES.
3. We need to handle configuration for multiple courses. This could be as
   multiple sites, but we do need a way to map their data assets.

When refering to XBlocks, we use the entry-point name. For example,
|   setup(
|       name='xblock-foobar',
|       version='0.1',
|       packages=[
|           'foobar_xblock',
|       ],
|       entry_points={
|           'xblock.v1': [
|               'foobar-block = foobar_xblock:FoobarBlock',
|           #    ^^^^^^^^^^^^ This is the one you want.
|           ]
|       },
|   )
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=unused-import

from __future__ import absolute_import

import imp
import os
import sys
from datetime import timedelta
import lms.envs.common
# Although this module itself may not use these imported variables, other dependent modules may.
from lms.envs.common import (
    USE_TZ, ALL_LANGUAGES, update_module_store_settings, ASSET_IGNORE_REGEX,
    PARENTAL_CONSENT_AGE_LIMIT, REGISTRATION_EMAIL_PATTERNS_ALLOWED,
    # The following PROFILE_IMAGE_* settings are included as they are
    # indirectly accessed through the email opt-in API, which is
    # technically accessible through the CMS via legacy URLs.
    PROFILE_IMAGE_BACKEND, PROFILE_IMAGE_DEFAULT_FILENAME, PROFILE_IMAGE_DEFAULT_FILE_EXTENSION,
    PROFILE_IMAGE_SECRET_KEY, PROFILE_IMAGE_MIN_BYTES, PROFILE_IMAGE_MAX_BYTES, PROFILE_IMAGE_SIZES_MAP,
    # The following setting is included as it is used to check whether to
    # display credit eligibility table on the CMS or not.
    COURSE_MODE_DEFAULTS, DEFAULT_COURSE_ABOUT_IMAGE_URL,

    # User-uploaded content
    MEDIA_ROOT,
    MEDIA_URL,

    # Lazy Gettext
    _,

    # Django REST framework configuration
    REST_FRAMEWORK,

    STATICI18N_OUTPUT_DIR,

    # Heartbeat
    HEARTBEAT_CHECKS,
    HEARTBEAT_EXTENDED_CHECKS,
    HEARTBEAT_CELERY_TIMEOUT,

    # Default site to use if no site exists matching request headers
    SITE_ID,

    # constants for redirects app
    REDIRECT_CACHE_TIMEOUT,
    REDIRECT_CACHE_KEY_PREFIX,

    # This is required for the migrations in oauth_dispatch.models
    # otherwise it fails saying this attribute is not present in Settings
    # Although Studio does not enable OAuth2 Provider capability, the new approach
    # to generating test databases will discover and try to create all tables
    # and this setting needs to be present
    OAUTH2_PROVIDER_APPLICATION_MODEL,
    JWT_AUTH,

    USERNAME_REGEX_PARTIAL,
    USERNAME_PATTERN,

    # django-debug-toolbar
    DEBUG_TOOLBAR_PATCH_SETTINGS,

    COURSE_ENROLLMENT_MODES,
    CONTENT_TYPE_GATE_GROUP_IDS,

    DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH,

    GENERATE_PROFILE_SCORES,

    # Methods to derive settings
    _make_mako_template_dirs,
    _make_locale_paths,
)
from path import Path as path
from django.core.urlresolvers import reverse_lazy

from lms.djangoapps.lms_xblock.mixin import LmsBlockMixin
from cms.lib.xblock.authoring_mixin import AuthoringMixin
from xmodule.modulestore.edit_info import EditInfoMixin
from openedx.core.djangoapps.theming.helpers_dirs import (
    get_themes_unchecked,
    get_theme_base_dirs_from_settings
)
from openedx.core.lib.license import LicenseMixin
from openedx.core.lib.derived import derived, derived_collection_entry
from openedx.core.release import doc_version

################ Enable credit eligibility feature ####################
ENABLE_CREDIT_ELIGIBILITY = True

################################ Block Structures ###################################
BLOCK_STRUCTURES_SETTINGS = dict(
    # Delay, in seconds, after a new edit of a course is published
    # before updating the block structures cache.  This is needed
    # for a better chance at getting the latest changes when there
    # are secondary reads in sharded mongoDB clusters. See TNL-5041
    # for more info.
    COURSE_PUBLISH_TASK_DELAY=30,

    # Delay, in seconds, between retry attempts if a task fails.
    TASK_DEFAULT_RETRY_DELAY=30,

    # Maximum number of retries per task.
    TASK_MAX_RETRIES=5,

    # Backend storage options
    PRUNING_ACTIVE=False,
)

############################ FEATURE CONFIGURATION #############################

PLATFORM_NAME = _('Your Platform Name Here')
PLATFORM_DESCRIPTION = _('Your Platform Description Here')

PLATFORM_FACEBOOK_ACCOUNT = "http://www.facebook.com/YourPlatformFacebookAccount"
PLATFORM_TWITTER_ACCOUNT = "@YourPlatformTwitterAccount"

# Dummy secret key for dev/test
SECRET_KEY = 'dev key'
FAVICON_PATH = 'images/favicon.ico'
STUDIO_NAME = _("Your Platform Studio")
STUDIO_SHORT_NAME = _("Studio")
FEATURES = {
    'GITHUB_PUSH': False,

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the ones in lms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,

    # .. documented_elsewhere: true
    # .. documented_elsewhere_name: ENABLE_STUDENT_NOTES
    'ENABLE_STUDENT_NOTES': True,

    # DO NOT SET TO True IN THIS FILE
    # Doing so will cause all courses to be released on production
    'DISABLE_START_DATES': False,  # When True, all courses will be active, regardless of start date

    # email address for studio staff (eg to request course creation)
    'STUDIO_REQUEST_EMAIL': '',

    # Segment - must explicitly turn it on for production
    'CMS_SEGMENT_KEY': None,

    # Enable URL that shows information about the status of various services
    'ENABLE_SERVICE_STATUS': False,

    # Don't autoplay videos for course authors
    'AUTOPLAY_VIDEOS': False,

    # Move the course author to next page when a video finishes. Set to True to
    # show an auto-advance button in videos. If False, videos never auto-advance.
    'ENABLE_AUTOADVANCE_VIDEOS': False,

    # If set to True, new Studio users won't be able to author courses unless
    # an Open edX admin has added them to the course creator group.
    'ENABLE_CREATOR_GROUP': True,

    # Turn off account locking if failed login attempts exceeds a limit
    'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': False,

    # Allow editing of short description in course settings in cms
    'EDITABLE_SHORT_DESCRIPTION': True,

    # Hide any Personally Identifiable Information from application logs
    'SQUELCH_PII_IN_LOGS': False,

    # Toggles the embargo functionality, which blocks users
    # based on their location.
    'EMBARGO': False,

    # Turn on/off Microsites feature
    'USE_MICROSITES': False,

    # Allow creating courses with non-ascii characters in the course id
    'ALLOW_UNICODE_COURSE_ID': False,

    # Prevent concurrent logins per user
    'PREVENT_CONCURRENT_LOGINS': False,

    # Turn off Video Upload Pipeline through Studio, by default
    'ENABLE_VIDEO_UPLOAD_PIPELINE': False,

    # let students save and manage their annotations
    # for consistency in user-experience, keep the value of this feature flag
    # in sync with the one in lms/envs/common.py
    'ENABLE_EDXNOTES': False,

    # Show a new field in "Advanced settings" that can store custom data about a
    # course and that can be read from themes
    'ENABLE_OTHER_COURSE_SETTINGS': False,

    # Enable support for content libraries. Note that content libraries are
    # only supported in courses using split mongo.
    'ENABLE_CONTENT_LIBRARIES': True,

    # Milestones application flag
    'MILESTONES_APP': False,

    # Prerequisite courses feature flag
    'ENABLE_PREREQUISITE_COURSES': False,

    # Toggle course entrance exams feature
    'ENTRANCE_EXAMS': False,

    # Toggle platform-wide course licensing
    'LICENSING': False,

    # Enable the courseware search functionality
    'ENABLE_COURSEWARE_INDEX': False,

    # Enable content libraries search functionality
    'ENABLE_LIBRARY_INDEX': False,

    # Enable course reruns, which will always use the split modulestore
    'ALLOW_COURSE_RERUNS': True,

    # Certificates Web/HTML Views
    'CERTIFICATES_HTML_VIEW': False,

    # Teams feature
    'ENABLE_TEAMS': True,

    # Show video bumper in Studio
    'ENABLE_VIDEO_BUMPER': False,

    # Show issue open badges in Studio
    'ENABLE_OPENBADGES': False,

    # How many seconds to show the bumper again, default is 7 days:
    'SHOW_BUMPER_PERIODICITY': 7 * 24 * 3600,

    # Enable credit eligibility feature
    'ENABLE_CREDIT_ELIGIBILITY': ENABLE_CREDIT_ELIGIBILITY,

    # Special Exams, aka Timed and Proctored Exams
    'ENABLE_SPECIAL_EXAMS': False,

    'ORGANIZATIONS_APP': False,

    # Show the language selector in the header
    'SHOW_HEADER_LANGUAGE_SELECTOR': False,

    # At edX it's safe to assume that English transcripts are always available
    # This is not the case for all installations.
    # The default value in {lms,cms}/envs/common.py and xmodule/tests/test_video.py should be consistent.
    'FALLBACK_TO_ENGLISH_TRANSCRIPTS': True,

    # Set this to False to facilitate cleaning up invalid xml from your modulestore.
    'ENABLE_XBLOCK_XML_VALIDATION': True,

    # Allow public account creation
    'ALLOW_PUBLIC_ACCOUNT_CREATION': True,

    # Whether or not the dynamic EnrollmentTrackUserPartition should be registered.
    'ENABLE_ENROLLMENT_TRACK_USER_PARTITION': True,

    # Whether to send an email for failed password reset attempts or not. This is mainly useful for notifying users
    # that they don't have an account associated with email addresses they believe they've registered with.
    'ENABLE_PASSWORD_RESET_FAILURE_EMAIL': False,

    # Whether archived courses (courses with end dates in the past) should be
    # shown in Studio in a separate list.
    'ENABLE_SEPARATE_ARCHIVED_COURSES': True,

    # For acceptance and load testing
    'AUTOMATIC_AUTH_FOR_TESTING': False,

    # Prevent auto auth from creating superusers or modifying existing users
    'RESTRICT_AUTOMATIC_AUTH': True,

    # Set this to true to make API docs available at /api-docs/.
    'ENABLE_API_DOCS': False,
}

ENABLE_JASMINE = False

# List of logout URIs for each IDA that the learner should be logged out of when they logout of the LMS. Only applies to
# IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = []

############################# SOCIAL MEDIA SHARING #############################
SOCIAL_SHARING_SETTINGS = {
    # Note: Ensure 'CUSTOM_COURSE_URLS' has a matching value in lms/envs/common.py
    'CUSTOM_COURSE_URLS': False
}

SOCIAL_MEDIA_FOOTER_URLS = {}

# This is just a placeholder image.
# Site operators can customize this with their organization's image.
FOOTER_ORGANIZATION_IMAGE = "images/logo.png"

############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /edx-platform/cms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
OPENEDX_ROOT = REPO_ROOT / "openedx"
CMS_ROOT = REPO_ROOT / "cms"
LMS_ROOT = REPO_ROOT / "lms"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /edx-platform is in
COURSES_ROOT = ENV_ROOT / "data"

GITHUB_REPO_ROOT = ENV_ROOT / "data"

sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'djangoapps')

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoLite2-Country.mmdb"

DATA_DIR = COURSES_ROOT

######################## BRANCH.IO ###########################
BRANCH_IO_KEY = ''

######################## GOOGLE ANALYTICS ###########################
GOOGLE_ANALYTICS_ACCOUNT = None

############################# TEMPLATE CONFIGURATION #############################
# Mako templating
import tempfile
MAKO_MODULE_DIR = os.path.join(tempfile.gettempdir(), 'mako_cms')
MAKO_TEMPLATE_DIRS_BASE = [
    PROJECT_ROOT / 'templates',
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
    COMMON_ROOT / 'static',  # required to statically include common Underscore templates
    OPENEDX_ROOT / 'core' / 'djangoapps' / 'cors_csrf' / 'templates',
    OPENEDX_ROOT / 'core' / 'djangoapps' / 'dark_lang' / 'templates',
    OPENEDX_ROOT / 'core' / 'lib' / 'license' / 'templates',
    CMS_ROOT / 'djangoapps' / 'pipeline_js' / 'templates',
]

CONTEXT_PROCESSORS = (
    'django.template.context_processors.request',
    'django.template.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.i18n',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.template.context_processors.csrf',
    'help_tokens.context_processor',
    'openedx.core.djangoapps.site_configuration.context_processors.configuration_context',
)

# Django templating
TEMPLATES = [
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Don't look for template source files inside installed applications.
        'APP_DIRS': False,
        # Instead, look for template source files in these dirs.
        'DIRS': _make_mako_template_dirs,
        # Options specific to this backend.
        'OPTIONS': {
            'loaders': (
                # We have to use mako-aware template loaders to be able to include
                # mako templates inside django templates (such as main_django.html).
                'openedx.core.djangoapps.theming.template_loaders.ThemeTemplateLoader',
                'edxmako.makoloader.MakoFilesystemLoader',
                'edxmako.makoloader.MakoAppDirectoriesLoader',
            ),
            'context_processors': CONTEXT_PROCESSORS,
            # Change 'debug' in your environment settings files - not here.
            'debug': False
        }
    },
    {
        'NAME': 'mako',
        'BACKEND': 'edxmako.backend.Mako',
        'APP_DIRS': False,
        'DIRS': _make_mako_template_dirs,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
            'debug': False,
        }
    },
    {
        # This separate copy of the Mako backend is used to render previews using the LMS templates
        'NAME': 'preview',
        'BACKEND': 'edxmako.backend.Mako',
        'APP_DIRS': False,
        'DIRS': lms.envs.common.MAKO_TEMPLATE_DIRS_BASE,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
            'debug': False,
            'namespace': 'lms.main',
        }
    },
]
derived_collection_entry('TEMPLATES', 0, 'DIRS')
derived_collection_entry('TEMPLATES', 1, 'DIRS')
DEFAULT_TEMPLATE_ENGINE = TEMPLATES[0]

#################################### AWS #######################################
# S3BotoStorage insists on a timeout for uploaded assets. We should make it
# permanent instead, but rather than trying to figure out exactly where that
# setting is, I'm just bumping the expiration time to something absurd (100
# years). This is only used if DEFAULT_FILE_STORAGE is overriden to use S3
# in the global settings.py
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'

##############################################################################

EDX_ROOT_URL = ''
LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/home/'
LOGIN_URL = reverse_lazy('login_redirect_to_lms')

# use the ratelimit backend to prevent brute force attacks
AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'openedx.core.djangoapps.oauth_dispatch.dot_overrides.backends.EdxRateLimitedAllowAllUsersModelBackend',
    'bridgekeeper.backends.RulePermissionBackend',
]

STATIC_ROOT_BASE = '/edx/var/edxapp/staticfiles'

# License for serving content in China
ICP_LICENSE = None
ICP_LICENSE_INFO = {}

LOGGING_ENV = 'sandbox'

LMS_BASE = 'localhost:18000'
LMS_ROOT_URL = "https://localhost:18000"
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL
LMS_ENROLLMENT_API_PATH = "/api/enrollment/v1/"
ENTERPRISE_API_URL = LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS = {}
FRONTEND_LOGIN_URL = LOGIN_URL
FRONTEND_LOGOUT_URL = lambda settings: settings.LMS_ROOT_URL + '/logout'
derived('FRONTEND_LOGOUT_URL')

CMS_BASE = 'localhost:18010'

LOG_DIR = '/edx/var/log/edx'

LOCAL_LOGLEVEL = "INFO"

MAINTENANCE_BANNER_TEXT = 'Sample banner message'

WIKI_ENABLED = True

CERT_QUEUE = 'certificates'
# List of logout URIs for each IDA that the learner should be logged out of when they logout of
# Studio. Only applies to IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = []

ELASTIC_SEARCH_CONFIG = [
    {
        'use_ssl': False,
        'host': 'localhost',
        'port': 9200
    }
]

# These are standard regexes for pulling out info like course_ids, usage_ids, etc.
# They are used so that URLs with deprecated-format strings still work.
from lms.envs.common import (
    COURSE_KEY_PATTERN, COURSE_KEY_REGEX, COURSE_ID_PATTERN, USAGE_KEY_PATTERN, ASSET_KEY_PATTERN
)

######################### CSRF #########################################

# Forwards-compatibility with Django 1.7
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52
# It is highly recommended that you override this in any environment accessed by
# end users
CSRF_COOKIE_SECURE = False

CROSS_DOMAIN_CSRF_COOKIE_DOMAIN = ''
CROSS_DOMAIN_CSRF_COOKIE_NAME = ''

#################### CAPA External Code Evaluation #############################
XQUEUE_INTERFACE = {
    'url': 'http://localhost:18040',
    'basic_auth': ['edx', 'edx'],
    'django_auth': {
        'username': 'lms',
        'password': 'password'
    }
}

################################# Middleware ###################################

MIDDLEWARE_CLASSES = [
    'openedx.core.lib.x_forwarded_for.middleware.XForwardedForMiddleware',

    'crum.CurrentRequestUserMiddleware',

    # A newer and safer request cache.
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'edx_django_utils.monitoring.middleware.MonitoringMemoryMiddleware',

    # Cookie monitoring
    'openedx.core.lib.request_utils.CookieMetricsMiddleware',

    'openedx.core.djangoapps.header_control.middleware.HeaderControlMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',

    # Allows us to define redirects via Django admin
    'django_sites_extensions.middleware.RedirectMiddleware',

    # Instead of SessionMiddleware, we use a more secure version
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware',

    'method_override.middleware.MethodOverrideMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'openedx.core.djangoapps.cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'student.middleware.UserStandingMiddleware',
    'openedx.core.djangoapps.contentserver.middleware.StaticContentServer',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',

    # This is used to set or update the user language preferences.
    'openedx.core.djangoapps.lang_pref.middleware.LanguagePreferenceMiddleware',

    # Allows us to dark-launch particular languages
    'openedx.core.djangoapps.dark_lang.middleware.DarkLangMiddleware',

    'openedx.core.djangoapps.embargo.middleware.EmbargoMiddleware',

    # Detects user-requested locale from 'accept-language' header in http request
    'django.middleware.locale.LocaleMiddleware',

    'codejail.django_integration.ConfigureCodeJailMiddleware',

    # catches any uncaught RateLimitExceptions and returns a 403 instead of a 500
    'ratelimitbackend.middleware.RateLimitMiddleware',

    # for expiring inactive sessions
    'openedx.core.djangoapps.session_inactivity_timeout.middleware.SessionInactivityTimeout',

    'openedx.core.djangoapps.theming.middleware.CurrentSiteThemeMiddleware',

    # use Django built in clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'waffle.middleware.WaffleMiddleware',

    # Enables force_django_cache_miss functionality for TieredCache.
    'edx_django_utils.cache.middleware.TieredCacheMiddleware',

    # Outputs monitoring metrics for a request.
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',

    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',

    # Handles automatically storing user ids in django-simple-history tables when possible.
    'simple_history.middleware.HistoryRequestMiddleware',

    # This must be last so that it runs first in the process_response chain
    'openedx.core.djangoapps.site_configuration.middleware.SessionCookieDomainOverrideMiddleware',
]

# Clickjacking protection can be disabled by setting this to 'ALLOW'
X_FRAME_OPTIONS = 'DENY'

# Platform for Privacy Preferences header
P3P_HEADER = 'CP="Open EdX does not have a P3P policy."'

############# XBlock Configuration ##########

# Import after sys.path fixup
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore import prefer_xmodules
from xmodule.x_module import XModuleMixin

# These are the Mixins that should be added to every XBlock.
# This should be moved into an XBlock Runtime/Application object
# once the responsibility of XBlock creation is moved out of modulestore - cpennington
XBLOCK_MIXINS = (
    LmsBlockMixin,
    InheritanceMixin,
    XModuleMixin,
    EditInfoMixin,
    AuthoringMixin,
)

XBLOCK_SELECT_FUNCTION = prefer_xmodules

# Paths to wrapper methods which should be applied to every XBlock's FieldData.
XBLOCK_FIELD_DATA_WRAPPERS = ()

############################ ORA 2 ############################################

# By default, don't use a file prefix
ORA2_FILE_PREFIX = None

# Default File Upload Storage bucket and prefix. Used by the FileUpload Service.
FILE_UPLOAD_STORAGE_BUCKET_NAME = 'SET-ME-PLEASE (ex. bucket-name)'
FILE_UPLOAD_STORAGE_PREFIX = 'submissions_attachments'

############################ Modulestore Configuration ################################

DOC_STORE_CONFIG = {
    'host': 'localhost',
    'db': 'xmodule',
    'collection': 'modulestore',
    # If 'asset_collection' defined, it'll be used
    # as the collection name for asset metadata.
    # Otherwise, a default collection name will be used.
}

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    # connection strings are duplicated temporarily for
    # backward compatibility
    'OPTIONS': {
        'db': 'edxapp',
        'host': 'localhost',
        'password': 'edxapp',
        'port': 27017,
        'user': 'edxapp',
        'ssl': False
    },
    'ADDITIONAL_OPTIONS': {},
    'DOC_STORE_CONFIG': DOC_STORE_CONFIG
}

MODULESTORE_BRANCH = 'draft-preferred'

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
        'OPTIONS': {
            'mappings': {},
            'stores': [
                {
                    'NAME': 'split',
                    'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': DATA_DIR,
                        'render_template': 'edxmako.shortcuts.render_to_string',
                    }
                },
                {
                    'NAME': 'draft',
                    'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': DATA_DIR,
                        'render_template': 'edxmako.shortcuts.render_to_string',
                    }
                }
            ]
        }
    }
}

# Modulestore-level field override providers. These field override providers don't
# require student context.
MODULESTORE_FIELD_OVERRIDE_PROVIDERS = ()

DATABASES = {
    # edxapp's edxapp-migrate scripts and the edxapp_migrate play
    # will ensure that any DB not named read_replica will be migrated
    # for both the lms and cms.
    'default': {
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 0,
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'edxapp',
        'OPTIONS': {},
        'PASSWORD': 'password',
        'PORT': '3306',
        'USER': 'edxapp001'
    },
    'read_replica': {
        'CONN_MAX_AGE': 0,
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'dxapp',
        'OPTIONS': {},
        'PASSWORD': 'password',
        'PORT': '3306',
        'USER': 'edxapp001'
    },
    'student_module_history': {
        'CONN_MAX_AGE': 0,
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'edxapp_csmh',
        'OPTIONS': {},
        'PASSWORD': 'password',
        'PORT': '3306',
        'USER': 'edxapp'
    }
}

#################### Python sandbox ############################################

CODE_JAIL = {
    # from https://github.com/edx/codejail/blob/master/codejail/django_integration.py#L24, '' should be same as None
    'python_bin': '/edx/app/edxapp/venvs/edxapp-sandbox/bin/python',
    # User to run as in the sandbox.
    'user': 'sandbox',

    # Configurable limits.
    'limits': {
        # How many CPU seconds can jailed code use?
        'CPU': 1,
        # Limit the memory of the jailed process to something high but not
        # infinite (512MiB in bytes)
        'VMEM': 536870912,
        # Time in seconds that the jailed process has to run.
        'REALTIME': 3,
        'PROXY': 0,
        # Needs to be non-zero so that jailed code can use it as their temp directory.(1MiB in bytes)
        'FSIZE': 1048576,
    },
}

# Some courses are allowed to run unsafe code. This is a list of regexes, one
# of them must match the course id for that course to run unsafe code.
#
# For example:
#
#   COURSES_WITH_UNSAFE_CODE = [
#       r"Harvard/XY123.1/.*"
#   ]

COURSES_WITH_UNSAFE_CODE = []

############################ DJANGO_BUILTINS ################################
# Change DEBUG in your environment settings files, not here
DEBUG = False
SESSION_COOKIE_SECURE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_COOKIE_DOMAIN = ""
SESSION_COOKIE_NAME = 'sessionid'

# Site info
SITE_NAME = "localhost"
HTTPS = 'on'
ROOT_URLCONF = 'cms.urls'

COURSE_IMPORT_EXPORT_BUCKET = ''
ALTERNATE_WORKER_QUEUES = 'lms'

STATIC_URL_BASE = '/static/'

X_FRAME_OPTIONS = 'DENY'

GIT_REPO_EXPORT_DIR = '/edx/var/edxapp/export_course_repos'

# Email
TECH_SUPPORT_EMAIL = 'technical@example.com'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'registration@example.com'
DEFAULT_FEEDBACK_EMAIL = 'feedback@example.com'
TECH_SUPPORT_EMAIL = 'technical@example.com'
CONTACT_EMAIL = 'info@example.com'
BUGS_EMAIL = 'bugs@example.com'
SERVER_EMAIL = 'devops@example.com'
UNIVERSITY_EMAIL = 'university@example.com'
PRESS_EMAIL = 'press@example.com'
ADMINS = []
MANAGERS = ADMINS

# Initialize to 'release', but read from JSON in production.py
EDX_PLATFORM_REVISION = 'release'

# Static content
STATIC_URL = '/static/studio/'
STATIC_ROOT = ENV_ROOT / "staticfiles" / 'studio'

STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",

    # This is how you would use the textbook images locally
    # ("book", ENV_ROOT / "book_images"),
]

# Locale/Internationalization
CELERY_TIMEZONE = 'UTC'
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGES_BIDI = lms.envs.common.LANGUAGES_BIDI

LANGUAGE_COOKIE = lms.envs.common.LANGUAGE_COOKIE

LANGUAGES = lms.envs.common.LANGUAGES
LANGUAGE_DICT = dict(LANGUAGES)

# Languages supported for custom course certificate templates
CERTIFICATE_TEMPLATE_LANGUAGES = {
    'en': 'English',
    'es': 'Español',
}

USE_I18N = True
USE_L10N = True

STATICI18N_ROOT = PROJECT_ROOT / "static"

LOCALE_PATHS = _make_locale_paths
derived('LOCALE_PATHS')

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

COURSE_IMPORT_EXPORT_STORAGE = 'django.core.files.storage.FileSystemStorage'

##### EMBARGO #####
EMBARGO_SITE_REDIRECT_URL = None

############################### PIPELINE #######################################

PIPELINE = {
    'PIPELINE_ENABLED': True,
    # Don't use compression by default
    'CSS_COMPRESSOR': None,
    'JS_COMPRESSOR': None,
    # Don't wrap JavaScript as there is code that depends upon updating the global namespace
    'DISABLE_WRAPPER': True,
    # Specify the UglifyJS binary to use
    'UGLIFYJS_BINARY': 'node_modules/.bin/uglifyjs',
    'COMPILERS': (),
    'YUI_BINARY': 'yui-compressor',
}

STATICFILES_STORAGE = 'openedx.core.storage.ProductionStorage'

# List of finder classes that know how to find static files in various locations.
# Note: the pipeline finder is included to be able to discover optimized files
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openedx.core.lib.xblock_pipeline.finder.XBlockPipelineFinder',
    'pipeline.finders.PipelineFinder',
]

from openedx.core.lib.rooted_paths import rooted_glob

PIPELINE['STYLESHEETS'] = {
    'style-vendor': {
        'source_filenames': [
            'css/vendor/normalize.css',
            'css/vendor/font-awesome.css',
            'css/vendor/html5-input-polyfills/number-polyfill.css',
            'js/vendor/CodeMirror/codemirror.css',
            'css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css',
            'css/vendor/jquery.qtip.min.css',
            'js/vendor/markitup/skins/simple/style.css',
            'js/vendor/markitup/sets/wiki/style.css',
        ],
        'output_filename': 'css/cms-style-vendor.css',
    },
    'style-vendor-tinymce-content': {
        'source_filenames': [
            'css/tinymce-studio-content-fonts.css',
            'js/vendor/tinymce/js/tinymce/skins/studio-tmce4/content.min.css',
            'css/tinymce-studio-content.css'
        ],
        'output_filename': 'css/cms-style-vendor-tinymce-content.css',
    },
    'style-vendor-tinymce-skin': {
        'source_filenames': [
            'js/vendor/tinymce/js/tinymce/skins/studio-tmce4/skin.min.css'
        ],
        'output_filename': 'css/cms-style-vendor-tinymce-skin.css',
    },
    'style-main-v1': {
        'source_filenames': [
            'css/studio-main-v1.css',
        ],
        'output_filename': 'css/studio-main-v1.css',
    },
    'style-main-v1-rtl': {
        'source_filenames': [
            'css/studio-main-v1-rtl.css',
        ],
        'output_filename': 'css/studio-main-v1-rtl.css',
    },
    'style-main-v2': {
        'source_filenames': [
            'css/studio-main-v2.css',
        ],
        'output_filename': 'css/studio-main-v2.css',
    },
    'style-main-v2-rtl': {
        'source_filenames': [
            'css/studio-main-v2-rtl.css',
        ],
        'output_filename': 'css/studio-main-v2-rtl.css',
    },
    'style-xmodule-annotations': {
        'source_filenames': [
            'css/vendor/ova/annotator.css',
            'css/vendor/ova/edx-annotator.css',
            'css/vendor/ova/video-js.min.css',
            'css/vendor/ova/rangeslider.css',
            'css/vendor/ova/share-annotator.css',
            'css/vendor/ova/richText-annotator.css',
            'css/vendor/ova/tags-annotator.css',
            'css/vendor/ova/flagging-annotator.css',
            'css/vendor/ova/diacritic-annotator.css',
            'css/vendor/ova/grouping-annotator.css',
            'css/vendor/ova/ova.css',
            'js/vendor/ova/catch/css/main.css'
        ],
        'output_filename': 'css/cms-style-xmodule-annotations.css',
    },
}

base_vendor_js = [
    'js/src/utility.js',
    'js/src/logger.js',
    'common/js/vendor/jquery.js',
    'common/js/vendor/jquery-migrate.js',
    'js/vendor/jquery.cookie.js',
    'js/vendor/url.min.js',
    'common/js/vendor/underscore.js',
    'common/js/vendor/underscore.string.js',
    'common/js/vendor/backbone.js',
    'js/vendor/URI.min.js',

    # Make some edX UI Toolkit utilities available in the global "edx" namespace
    'edx-ui-toolkit/js/utils/global-loader.js',
    'edx-ui-toolkit/js/utils/string-utils.js',
    'edx-ui-toolkit/js/utils/html-utils.js',

    # Load Bootstrap and supporting libraries
    'common/js/vendor/popper.js',
    'common/js/vendor/bootstrap.js',

    # Finally load RequireJS
    'common/js/vendor/require.js'
]

# test_order: Determines the position of this chunk of javascript on
# the jasmine test page
PIPELINE['JAVASCRIPT'] = {
    'base_vendor': {
        'source_filenames': base_vendor_js,
        'output_filename': 'js/cms-base-vendor.js',
    },
    'module-js': {
        'source_filenames': (
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/descriptors/js/*.js') +
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/modules/js/*.js') +
            rooted_glob(COMMON_ROOT / 'static/', 'common/js/discussion/*.js')
        ),
        'output_filename': 'js/cms-modules.js',
        'test_order': 1
    },
}

STATICFILES_IGNORE_PATTERNS = (
    "*.py",
    "*.pyc",

    # It would be nice if we could do, for example, "**/*.scss",
    # but these strings get passed down to the `fnmatch` module,
    # which doesn't support that. :(
    # http://docs.python.org/2/library/fnmatch.html
    "sass/*.scss",
    "sass/*/*.scss",
    "sass/*/*/*.scss",
    "sass/*/*/*/*.scss",

    # Ignore tests
    "spec",
    "spec_helpers",

    # Symlinks used by js-test-tool
    "xmodule_js",
    "common_static",
)

################################# DJANGO-REQUIRE ###############################


# The baseUrl to pass to the r.js optimizer, relative to STATIC_ROOT.
REQUIRE_BASE_URL = "./"

# The name of a build profile to use for your project, relative to REQUIRE_BASE_URL.
# A sensible value would be 'app.build.js'. Leave blank to use the built-in default build profile.
# Set to False to disable running the default profile (e.g. if only using it to build Standalone
# Modules)
REQUIRE_BUILD_PROFILE = "cms/js/build.js"

# The name of the require.js script used by your project, relative to REQUIRE_BASE_URL.
REQUIRE_JS = "js/vendor/requiresjs/require.js"

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = False

########################## DJANGO WEBPACK LOADER ##############################

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(STATIC_ROOT, 'webpack-stats.json')
    },
    'WORKERS': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(STATIC_ROOT, 'webpack-worker-stats.json')
    }
}
WEBPACK_CONFIG_PATH = 'webpack.prod.config.js'

################################# CELERY ######################################

# Auto discover tasks fails to detect contentstore tasks
CELERY_IMPORTS = ('cms.djangoapps.contentstore.tasks')

# Message configuration

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_MESSAGE_COMPRESSION = 'gzip'

# Results configuration

CELERY_IGNORE_RESULT = False
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

# Events configuration

CELERY_TRACK_STARTED = True

CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True

# Exchange configuration

CELERY_DEFAULT_EXCHANGE = 'edx.core'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'

# Queues configuration

HIGH_PRIORITY_QUEUE = 'edx.core.high'
DEFAULT_PRIORITY_QUEUE = 'edx.core.default'

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_CREATE_MISSING_QUEUES = True

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = [
    'edx.cms.core.default',
    'edx.cms.core.high',
]

CELERY_BROKER_TRANSPORT = 'amqp'
CELERY_BROKER_HOSTNAME = 'localhost'
CELERY_BROKER_USER = 'celery'
CELERY_BROKER_PASSWORD = 'celery'

############################## Video ##########################################

YOUTUBE = {
    # YouTube JavaScript API
    'API': 'https://www.youtube.com/iframe_api',

    'TEST_TIMEOUT': 1500,

    # URL to get YouTube metadata
    'METADATA_URL': 'https://www.googleapis.com/youtube/v3/videos',

    # Current youtube api for requesting transcripts.
    # For example: http://video.google.com/timedtext?lang=en&v=j_jEn79vS3g.
    'TEXT_API': {
        'url': 'video.google.com/timedtext',
        'params': {
            'lang': 'en',
            'v': 'set_youtube_id_of_11_symbols_here',
        },
    },

    'IMAGE_API': 'http://img.youtube.com/vi/{youtube_id}/0.jpg',  # /maxresdefault.jpg for 1920*1080
}

YOUTUBE_API_KEY = 'PUT_YOUR_API_KEY_HERE'

############################# VIDEO UPLOAD PIPELINE #############################

VIDEO_UPLOAD_PIPELINE = {
    'BUCKET': '',
    'ROOT_PATH': '',
    'CONCURRENT_UPLOAD_LIMIT': 4,
}

############################ APPS #####################################

# The order of INSTALLED_APPS is important, when adding new apps here
# remember to check that you are not creating new
# RemovedInDjango19Warnings in the test logs.
INSTALLED_APPS = [
    # Standard apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'method_override',

    # Common Initialization
    'openedx.core.djangoapps.common_initialization.apps.CommonInitializationConfig',

    # Common views
    'openedx.core.djangoapps.common_views',

    # API access administration
    'openedx.core.djangoapps.api_admin',

    # History tables
    'simple_history',

    # Database-backed configuration
    'config_models',
    'openedx.core.djangoapps.config_model_utils',
    'waffle',

    # Monitor the status of services
    'openedx.core.djangoapps.service_status',

    # Video module configs (This will be moved to Video once it becomes an XBlock)
    'openedx.core.djangoapps.video_config',

    # edX Video Pipeline integration
    'openedx.core.djangoapps.video_pipeline',

    # For CMS
    'contentstore.apps.ContentstoreConfig',

    'openedx.core.djangoapps.contentserver',
    'course_creators',
    'student.apps.StudentConfig',  # misleading name due to sharing with lms
    'openedx.core.djangoapps.course_groups',  # not used in cms (yet), but tests run
    'xblock_config.apps.XBlockConfig',

    # Maintenance tools
    'maintenance',
    'openedx.core.djangoapps.util.apps.UtilConfig',

    # Tracking
    'track',
    'eventtracking.django.apps.EventTrackingConfig',

    # For asset pipelining
    'edxmako.apps.EdxMakoConfig',
    'pipeline',
    'static_replace',
    'require',
    'webpack_loader',

    # Site configuration for theming and behavioral modification
    'openedx.core.djangoapps.site_configuration',

    # Ability to detect and special-case crawler behavior
    'openedx.core.djangoapps.crawlers',

    # Discussion
    'openedx.core.djangoapps.django_comment_common',

    # for course creator table
    'django.contrib.admin',

    # for managing course modes
    'course_modes.apps.CourseModesConfig',

    # Verified Track Content Cohorting (Beta feature that will hopefully be removed)
    'openedx.core.djangoapps.verified_track_content',

    # Dark-launching languages
    'openedx.core.djangoapps.dark_lang',

    #
    # User preferences
    'wiki',
    'django_notify',
    'course_wiki',  # Our customizations
    'mptt',
    'sekizai',
    'openedx.core.djangoapps.user_api',
    'django_openid_auth',

    # Country embargo support
    'openedx.core.djangoapps.embargo',

    # Course action state
    'course_action_state',

    # Additional problem types
    'edx_jsme',    # Molecular Structure

    'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig',
    'openedx.core.djangoapps.content.block_structure.apps.BlockStructureConfig',

    # edx-milestones service
    'milestones',

    # Self-paced course configuration
    'openedx.core.djangoapps.self_paced',

    # Coursegraph
    'openedx.core.djangoapps.coursegraph.apps.CoursegraphConfig',

    # Credit courses
    'openedx.core.djangoapps.credit.apps.CreditConfig',

    'xblock_django',

    # Catalog integration
    'openedx.core.djangoapps.catalog',

    # django-oauth2-provider (deprecated)
    'provider',
    'provider.oauth2',
    'edx_oauth2_provider',

    # django-oauth-toolkit
    'oauth2_provider',

    # These are apps that aren't strictly needed by Studio, but are imported by
    # other apps that are.  Django 1.8 wants to have imported models supported
    # by installed apps.
    'openedx.core.djangoapps.oauth_dispatch.apps.OAuthDispatchAppConfig',
    'oauth_provider',
    'courseware',
    'survey.apps.SurveyConfig',
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
    'completion',

    # System Wide Roles
    'openedx.core.djangoapps.system_wide_roles',

    # Microsite configuration application
    'microsite_configuration',

    # Static i18n support
    'statici18n',

    # Tagging
    'cms.lib.xblock.tagging',

    # Enables default site and redirects
    'django_sites_extensions',

    # additional release utilities to ease automation
    'release_util',

    # rule-based authorization
    'rules.apps.AutodiscoverRulesConfig',
    'bridgekeeper',

    # management of user-triggered async tasks (course import/export, etc.)
    'user_tasks',

    # CMS specific user task handling
    'cms_user_tasks.apps.CmsUserTasksConfig',

    # Unusual migrations
    'database_fixups',

    # Customized celery tasks, including persisting failed tasks so they can
    # be retried
    'celery_utils',

    # Waffle related utilities
    'openedx.core.djangoapps.waffle_utils',

    # DRF filters
    'django_filters',
    'cms.djangoapps.api',

    # Entitlements, used in openedx tests
    'entitlements',

    # Asset management for mako templates
    'pipeline_mako',

    # API Documentation
    'drf_yasg',

    'openedx.features.course_duration_limits',
    'openedx.features.content_type_gating',
    'openedx.features.discounts',
    'experiments',

]


################# EDX MARKETING SITE ##################################

EDXMKTG_LOGGED_IN_COOKIE_NAME = 'edxloggedin'
EDXMKTG_USER_INFO_COOKIE_NAME = 'edx-user-info'
EDXMKTG_USER_INFO_COOKIE_VERSION = 1

MKTG_URLS = {}
MKTG_URL_LINK_MAP = {

}

SUPPORT_SITE_LINK = ''
ID_VERIFICATION_SUPPORT_LINK = ''
PASSWORD_RESET_SUPPORT_LINK = ''
ACTIVATION_EMAIL_SUPPORT_LINK = ''

############################## EVENT TRACKING #################################

TRACK_MAX_EVENT = 50000

TRACKING_BACKENDS = {
    'logger': {
        'ENGINE': 'track.backends.logger.LoggerBackend',
        'OPTIONS': {
            'name': 'tracking'
        }
    }
}

# We're already logging events, and we don't want to capture user
# names/passwords.  Heartbeat events are likely not interesting.
TRACKING_IGNORE_URL_PATTERNS = [r'^/event', r'^/login', r'^/heartbeat']

EVENT_TRACKING_ENABLED = True
EVENT_TRACKING_BACKENDS = {
    'tracking_logs': {
        'ENGINE': 'eventtracking.backends.routing.RoutingBackend',
        'OPTIONS': {
            'backends': {
                'logger': {
                    'ENGINE': 'eventtracking.backends.logger.LoggerBackend',
                    'OPTIONS': {
                        'name': 'tracking',
                        'max_event_size': TRACK_MAX_EVENT,
                    }
                }
            },
            'processors': [
                {'ENGINE': 'track.shim.LegacyFieldMappingProcessor'},
                {'ENGINE': 'track.shim.PrefixedEventProcessor'}
            ]
        }
    },
    'segmentio': {
        'ENGINE': 'eventtracking.backends.routing.RoutingBackend',
        'OPTIONS': {
            'backends': {
                'segment': {'ENGINE': 'eventtracking.backends.segment.SegmentBackend'}
            },
            'processors': [
                {
                    'ENGINE': 'eventtracking.processors.whitelist.NameWhitelistProcessor',
                    'OPTIONS': {
                        'whitelist': []
                    }
                },
                {
                    'ENGINE': 'track.shim.GoogleAnalyticsProcessor'
                }
            ]
        }
    }
}
EVENT_TRACKING_PROCESSORS = []

EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST = []

#### PASSWORD POLICY SETTINGS #####
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "util.password_policy_validators.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 2
        }
    },
    {
        "NAME": "util.password_policy_validators.MaximumLengthValidator",
        "OPTIONS": {
            "max_length": 75
        }
    },
]

PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG = {
    'ENFORCE_COMPLIANCE_ON_LOGIN': False
}

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = 6
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = 30 * 60


### Apps only installed in some instances
# The order of INSTALLED_APPS matters, so this tuple is the app name and the item in INSTALLED_APPS
# that this app should be inserted *before*. A None here means it should be appended to the list.
OPTIONAL_APPS = (
    ('problem_builder', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('edx_sga', None),

    # edx-ora2
    ('submissions', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('openassessment', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('openassessment.assessment', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('openassessment.fileupload', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('openassessment.workflow', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),
    ('openassessment.xblock', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),

    # edxval
    ('edxval', 'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig'),

    # Organizations App (http://github.com/edx/edx-organizations)
    ('organizations', None),

    # Enterprise App (http://github.com/edx/edx-enterprise)
    ('enterprise', None),
    ('consent', None),
    ('integrated_channels.integrated_channel', None),
    ('integrated_channels.degreed', None),
    ('integrated_channels.sap_success_factors', None),
    ('integrated_channels.xapi', None),
    ('integrated_channels.cornerstone', None),
)


for app_name, insert_before in OPTIONAL_APPS:
    # First attempt to only find the module rather than actually importing it,
    # to avoid circular references - only try to import if it can't be found
    # by find_module, which doesn't work with import hooks
    try:
        imp.find_module(app_name)
    except ImportError:
        try:
            __import__(app_name)
        except ImportError:
            continue

    try:
        INSTALLED_APPS.insert(INSTALLED_APPS.index(insert_before), app_name)
    except (IndexError, ValueError):
        INSTALLED_APPS.append(app_name)


### External auth usage -- prefixes for ENROLLMENT_DOMAIN
SHIBBOLETH_DOMAIN_PREFIX = 'shib:'
OPENID_DOMAIN_PREFIX = 'openid:'

# Set request limits for maximum size of a request body and maximum number of GET/POST parameters. (>=Django 1.10)
# Limits are currently disabled - but can be used for finer-grained denial-of-service protection.
DATA_UPLOAD_MAX_MEMORY_SIZE = None
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

### Size of chunks into which asset uploads will be divided
UPLOAD_CHUNK_SIZE_IN_MB = 10

### Max size of asset uploads to GridFS
MAX_ASSET_UPLOAD_FILE_SIZE_IN_MB = 10

# FAQ url to direct users to if they upload
# a file that exceeds the above size
MAX_ASSET_UPLOAD_FILE_SIZE_URL = ""

### Default value for entrance exam minimum score
ENTRANCE_EXAM_MIN_SCORE_PCT = 50

### Default language for a new course
DEFAULT_COURSE_LANGUAGE = "en"

# Specify XBlocks that should be treated as advanced problems. Each entry is a
# dict:
#       'component': the entry-point name of the XBlock.
#       'boilerplate_name': an optional YAML template to be used.  Specify as
#               None to omit.
#
ADVANCED_PROBLEM_TYPES = [
    {
        'component': 'openassessment',
        'boilerplate_name': None,
    },
    {
        'component': 'drag-and-drop-v2',
        'boilerplate_name': None
    },
    {
        'component': 'staffgradedxblock',
        'boilerplate_name': None
    }
]

############### Settings for Retirement #####################
RETIRED_USERNAME_PREFIX = 'retired__user_'
RETIRED_EMAIL_PREFIX = 'retired__user_'
RETIRED_EMAIL_DOMAIN = 'retired.invalid'
RETIRED_USERNAME_FMT = lambda settings: settings.RETIRED_USERNAME_PREFIX + '{}'
RETIRED_EMAIL_FMT = lambda settings: settings.RETIRED_EMAIL_PREFIX + '{}@' + settings.RETIRED_EMAIL_DOMAIN
derived('RETIRED_USERNAME_FMT', 'RETIRED_EMAIL_FMT')
RETIRED_USER_SALTS = ['abc', '123']
RETIREMENT_SERVICE_WORKER_USERNAME = 'RETIREMENT_SERVICE_USER'

# These states are the default, but are designed to be overridden in configuration.
RETIREMENT_STATES = [
    'PENDING',

    'LOCKING_ACCOUNT',
    'LOCKING_COMPLETE',

    # Use these states only when ENABLE_DISCUSSION_SERVICE is True.
    'RETIRING_FORUMS',
    'FORUMS_COMPLETE',

    # TODO - Change these states to be the LMS-only email opt-out - PLAT-2189
    'RETIRING_EMAIL_LISTS',
    'EMAIL_LISTS_COMPLETE',

    'RETIRING_ENROLLMENTS',
    'ENROLLMENTS_COMPLETE',

    # Use these states only when ENABLE_STUDENT_NOTES is True.
    'RETIRING_NOTES',
    'NOTES_COMPLETE',

    'RETIRING_LMS',
    'LMS_COMPLETE',

    'ERRORED',
    'ABORTED',
    'COMPLETE',
]

USERNAME_REPLACEMENT_WORKER = "REPLACE WITH VALID USERNAME"

# Files and Uploads type filter values

FILES_AND_UPLOAD_TYPE_FILTERS = {
    "Images": ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/tiff', 'image/tif', 'image/x-icon',
               'image/svg+xml', 'image/bmp', 'image/x-ms-bmp', ],
    "Documents": [
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
        'application/vnd.openxmlformats-officedocument.presentationml.template',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
        'application/msword',
        'application/vnd.ms-excel',
        'application/vnd.ms-powerpoint',
        'application/csv',
        'application/vnd.ms-excel.sheet.macroEnabled.12',
        'text/x-tex',
        'application/x-pdf',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'file/pdf',
        'image/pdf',
        'text/csv',
        'text/pdf',
        'text/x-sh',
        '\"application/pdf\"',
    ],
    "Audio": ['audio/mpeg', 'audio/mp3', 'audio/x-wav', 'audio/ogg', 'audio/wav', 'audio/aac', 'audio/x-m4a',
              'audio/mp4', 'audio/x-ms-wma', ],
    "Code": ['application/json', 'text/html', 'text/javascript', 'application/javascript', 'text/css', 'text/x-python',
             'application/x-java-jnlp-file', 'application/xml', 'application/postscript', 'application/x-javascript',
             'application/java-vm', 'text/x-c++src', 'text/xml', 'text/x-scss', 'application/x-python-code',
             'application/java-archive', 'text/x-python-script', 'application/x-ruby', 'application/mathematica',
             'text/coffeescript', 'text/x-matlab', 'application/sql', 'text/php', ]
}

# Default to no Search Engine
SEARCH_ENGINE = None
ELASTIC_FIELD_MAPPINGS = {
    "start_date": {
        "type": "date"
    }
}

XBLOCK_SETTINGS = {}
XBLOCK_FS_STORAGE_BUCKET = None
XBLOCK_FS_STORAGE_PREFIX = None

STUDIO_FRONTEND_CONTAINER_URL = None

################################ Settings for Credit Course Requirements ################################
# Initial delay used for retrying tasks.
# Additional retries use longer delays.
# Value is in seconds.
CREDIT_TASK_DEFAULT_RETRY_DELAY = 30

# Maximum number of retries per task for errors that are not related
# to throttling.
CREDIT_TASK_MAX_RETRIES = 5

# Maximum age in seconds of timestamps we will accept
# when a credit provider notifies us that a student has been approved
# or denied for credit.
CREDIT_PROVIDER_TIMESTAMP_EXPIRATION = 15 * 60

CREDIT_PROVIDER_SECRET_KEYS = {}

# dir containing all themes
COMPREHENSIVE_THEME_DIRS = []

# Theme directory locale paths
COMPREHENSIVE_THEME_LOCALE_PATHS = []

# Theme to use when no site or site theme is defined,
# set to None if you want to use openedx theme
DEFAULT_SITE_THEME = None

ENABLE_COMPREHENSIVE_THEMING = False

################################ Settings for Microsites ################################

### Select an implementation for the microsite backend
# for MICROSITE_BACKEND possible choices are
# 1. microsite_configuration.backends.filebased.FilebasedMicrositeBackend
# 2. microsite_configuration.backends.database.DatabaseMicrositeBackend
MICROSITE_BACKEND = 'microsite_configuration.backends.filebased.FilebasedMicrositeBackend'
# for MICROSITE_TEMPLATE_BACKEND possible choices are
# 1. microsite_configuration.backends.filebased.FilebasedMicrositeTemplateBackend
# 2. microsite_configuration.backends.database.DatabaseMicrositeTemplateBackend
MICROSITE_TEMPLATE_BACKEND = 'microsite_configuration.backends.filebased.FilebasedMicrositeTemplateBackend'
# TTL for microsite database template cache
MICROSITE_DATABASE_TEMPLATE_CACHE_TTL = 5 * 60


############################ Global Database Configuration #####################

DATABASE_ROUTERS = [
    'openedx.core.lib.django_courseware_routers.StudentModuleHistoryExtendedRouter',
]

############################ Cache Configuration ###############################

CACHES = {
    'course_structure_cache': {
        'KEY_PREFIX': 'course_structure',
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': '7200',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'celery': {
        'KEY_PREFIX': 'celery',
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': '7200',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'mongo_metadata_inheritance': {
        'KEY_PREFIX': 'mongo_metadata_inheritance',
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': 300,
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'staticfiles': {
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'staticfiles_general',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'default': {
        'VERSION': '1',
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'default',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'configuration': {
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'configuration',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'general': {
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'general',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
}

############################ OAUTH2 Provider ###################################

# OpenID Connect issuer ID. Normally the URL of the authentication endpoint.
OAUTH_OIDC_ISSUER = 'http://127.0.0.1:8000/oauth2'

# 5 minute expiration time for JWT id tokens issued for external API requests.
OAUTH_ID_TOKEN_EXPIRATION = 5 * 60

# Partner support link for CMS footer
PARTNER_SUPPORT_EMAIL = ''

# Affiliate cookie tracking
AFFILIATE_COOKIE_NAME = 'affiliate_id'

############## Settings for Studio Context Sensitive Help ##############

HELP_TOKENS_INI_FILE = REPO_ROOT / "cms" / "envs" / "help_tokens.ini"
HELP_TOKENS_LANGUAGE_CODE = lambda settings: settings.LANGUAGE_CODE
HELP_TOKENS_VERSION = lambda settings: doc_version()
HELP_TOKENS_BOOKS = {
    'learner': 'https://edx.readthedocs.io/projects/open-edx-learner-guide',
    'course_author': 'https://edx.readthedocs.io/projects/open-edx-building-and-running-a-course',
}
derived('HELP_TOKENS_LANGUAGE_CODE', 'HELP_TOKENS_VERSION')

# Used with Email sending
RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS = 5
RETRY_ACTIVATION_EMAIL_TIMEOUT = 0.5

############## DJANGO-USER-TASKS ##############

# How long until database records about the outcome of a task and its artifacts get deleted?
USER_TASKS_MAX_AGE = timedelta(days=7)

############## Settings for the Enterprise App ######################

ENTERPRISE_ENROLLMENT_API_URL = LMS_ROOT_URL + LMS_ENROLLMENT_API_PATH
ENTERPRISE_SERVICE_WORKER_USERNAME = 'enterprise_worker'
ENTERPRISE_API_CACHE_TIMEOUT = 3600  # Value is in seconds
# The default value of this needs to be a 16 character string
ENTERPRISE_REPORTING_SECRET = '0000000000000000'
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = {}

BASE_COOKIE_DOMAIN = 'localhost'
############## Settings for the Discovery App ######################

COURSE_CATALOG_API_URL = 'http://localhost:8008/api/v1'

# which access.py permission name to check in order to determine if a course is visible in
# the course catalog. We default this to the legacy permission 'see_exists'.
COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_exists'

# which access.py permission name to check in order to determine if a course about page is
# visible. We default this to the legacy permission 'see_exists'.
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_exists'

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = "both"
DEFAULT_MOBILE_AVAILABLE = False

################# Mobile URLS ##########################

# These are URLs to the app store for mobile.
MOBILE_STORE_URLS = {}

############################# Persistent Grades ####################################

# Queue to use for updating persistent grades
RECALCULATE_GRADES_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

# Rate limit for regrading tasks that a grading policy change can kick off
POLICY_CHANGE_TASK_RATE_LIMIT = '300/h'

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

########## Settings for video transcript migration tasks ############
VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

########## Settings youtube thumbnails scraper tasks ############
SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

###################### VIDEO IMAGE STORAGE ######################

VIDEO_IMAGE_DEFAULT_FILENAME = 'images/video-images/default_video_image.png'
VIDEO_IMAGE_SUPPORTED_FILE_FORMATS = {
    '.bmp': 'image/bmp',
    '.bmp2': 'image/x-ms-bmp',   # PIL gives x-ms-bmp format
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png'
}
VIDEO_IMAGE_MAX_FILE_SIZE_MB = '2 MB'
VIDEO_IMAGE_MIN_FILE_SIZE_KB = '2 KB'
VIDEO_IMAGE_MAX_WIDTH = 1280
VIDEO_IMAGE_MAX_HEIGHT = 720
VIDEO_IMAGE_MIN_WIDTH = 640
VIDEO_IMAGE_MIN_HEIGHT = 360
VIDEO_IMAGE_ASPECT_RATIO = 16 / 9.0
VIDEO_IMAGE_ASPECT_RATIO_TEXT = '16:9'
VIDEO_IMAGE_ASPECT_RATIO_ERROR_MARGIN = 0.1

###################### ZENDESK ######################
ZENDESK_URL = ''
ZENDESK_USER = None
ZENDESK_API_KEY = None
ZENDESK_CUSTOM_FIELDS = {}
ZENDESK_OAUTH_ACCESS_TOKEN = ''

############## Settings for Completion API #########################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = 0.95

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = []

############## Installed Django Apps #########################

from openedx.core.djangoapps.plugins import plugin_apps, plugin_settings, constants as plugin_constants
INSTALLED_APPS.extend(plugin_apps.get_apps(plugin_constants.ProjectType.CMS))
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.CMS, plugin_constants.SettingsType.COMMON)

# Course exports streamed in blocks of this size. 8192 or 8kb is the default
# setting for the FileWrapper class used to iterate over the export file data.
# See: https://docs.python.org/2/library/wsgiref.html#wsgiref.util.FileWrapper
COURSE_EXPORT_DOWNLOAD_CHUNK_SIZE = 8192

# E-Commerce API Configuration
ECOMMERCE_PUBLIC_URL_ROOT = 'http://localhost:8002'
ECOMMERCE_API_URL = 'http://localhost:8002/api/v2'
ECOMMERCE_API_SIGNING_KEY = 'SET-ME-PLEASE'

CREDENTIALS_INTERNAL_SERVICE_URL = 'http://localhost:8005'
CREDENTIALS_PUBLIC_SERVICE_URL = None

JOURNALS_URL_ROOT = 'https://journals-localhost:18000'
JOURNALS_API_URL = 'https://journals-localhost:18000/api/v1/'

ANALYTICS_DASHBOARD_URL = 'http://localhost:18110/courses'
ANALYTICS_DASHBOARD_NAME = 'Your Platform Name Here Insights'

COMMENTS_SERVICE_URL = 'http://localhost:18080'
COMMENTS_SERVICE_KEY = 'password'

CAS_SERVER_URL = ""
CAS_EXTRA_LOGIN_PARAMS = ""
CAS_ATTRIBUTE_CALLBACK = ""

FINANCIAL_REPORTS = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': None,
    'ROOT_PATH': 'sandbox',
}

CORS_ORIGIN_WHITELIST = []
CORS_ORIGIN_ALLOW_ALL = False

LOGIN_REDIRECT_WHITELIST = []

############### Settings for video pipeline ##################
VIDEO_UPLOAD_PIPELINE = {
    'BUCKET': '',
    'ROOT_PATH': '',
}

DEPRECATED_ADVANCED_COMPONENT_TYPES = []

########################## VIDEO IMAGE STORAGE ############################

VIDEO_IMAGE_SETTINGS = dict(
    VIDEO_IMAGE_MAX_BYTES=2 * 1024 * 1024,    # 2 MB
    VIDEO_IMAGE_MIN_BYTES=2 * 1024,       # 2 KB
    # Backend storage
    # STORAGE_CLASS='storages.backends.s3boto.S3BotoStorage',
    # STORAGE_KWARGS=dict(bucket='video-image-bucket'),
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-images/',
)

VIDEO_IMAGE_MAX_AGE = 31536000

########################## VIDEO TRANSCRIPTS STORAGE ############################
VIDEO_TRANSCRIPTS_SETTINGS = dict(
    VIDEO_TRANSCRIPTS_MAX_BYTES=3 * 1024 * 1024,    # 3 MB
    # Backend storage
    # STORAGE_CLASS='storages.backends.s3boto.S3BotoStorage',
    # STORAGE_KWARGS=dict(bucket='video-transcripts-bucket'),
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-transcripts/',
)

VIDEO_TRANSCRIPTS_MAX_AGE = 31536000

##### shoppingcart Payment #####
PAYMENT_SUPPORT_EMAIL = 'billing@example.com'

################################ Bulk Email ###################################
# Parameters for breaking down course enrollment into subtasks.
BULK_EMAIL_EMAILS_PER_TASK = 500

# Suffix used to construct 'from' email address for bulk emails.
# A course-specific identifier is prepended.
BULK_EMAIL_DEFAULT_FROM_EMAIL = 'no-reply@example.com'

# Flag to indicate if individual email addresses should be logged as they are sent
# a bulk email message.
BULK_EMAIL_LOG_SENT_EMAILS = False

################################ Settings for Microsites ################################
MICROSITE_ROOT_DIR = '/edx/app/edxapp/edx-microsite'
MICROSITE_CONFIGURATION = {}

############### Settings for django file storage ##################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

###################### Grade Downloads ######################
# These keys are used for all of our asynchronous downloadable files, including
# the ones that contain information other than grades.
GRADES_DOWNLOAD = {
    'STORAGE_CLASS': 'django.core.files.storage.FileSystemStorage',
    'STORAGE_KWARGS': {
        'location': '/tmp/edx-s3/grades',
    },
    'STORAGE_TYPE': None,
    'BUCKET': None,
    'ROOT_PATH': None,
}

############### Settings swift #####################################
SWIFT_USERNAME = None
SWIFT_KEY = None
SWIFT_TENANT_ID = None
SWIFT_TENANT_NAME = None
SWIFT_AUTH_URL = None
SWIFT_AUTH_VERSION = None
SWIFT_REGION_NAME = None
SWIFT_USE_TEMP_URLS = None
SWIFT_TEMP_URL_KEY = None
SWIFT_TEMP_URL_DURATION = 1800  # seconds

############### The SAML private/public key values ################
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = ""
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = ""
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT = {}
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT = {}

############### Settings for facebook ##############################
FACEBOOK_APP_ID = 'FACEBOOK_APP_ID'
FACEBOOK_APP_SECRET = 'FACEBOOK_APP_SECRET'
FACEBOOK_API_VERSION = 'v2.1'

### Proctoring configuration (redirct URLs and keys shared between systems) ####
PROCTORING_BACKENDS = {
    'DEFAULT': 'null',
    # The null key needs to be quoted because
    # null is a language independent type in YAML
    'null': {}
}
