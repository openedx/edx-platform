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

# pylint: disable=unused-import, useless-suppression, wrong-import-order, wrong-import-position

import importlib.util
import os
import sys

from corsheaders.defaults import default_headers as corsheaders_default_headers
from datetime import timedelta
import lms.envs.common
# Although this module itself may not use these imported variables, other dependent modules may.
from lms.envs.common import (
    USE_TZ, ALL_LANGUAGES, ASSET_IGNORE_REGEX,
    PARENTAL_CONSENT_AGE_LIMIT, REGISTRATION_EMAIL_PATTERNS_ALLOWED,
    # The following PROFILE_IMAGE_* settings are included as they are
    # indirectly accessed through the email opt-in API, which is
    # technically accessible through the CMS via legacy URLs.
    PROFILE_IMAGE_BACKEND, PROFILE_IMAGE_DEFAULT_FILENAME, PROFILE_IMAGE_DEFAULT_FILE_EXTENSION,
    PROFILE_IMAGE_HASH_SEED, PROFILE_IMAGE_MIN_BYTES, PROFILE_IMAGE_MAX_BYTES, PROFILE_IMAGE_SIZES_MAP,
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
    HEARTBEAT_CELERY_ROUTING_KEY,

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

    # Enterprise service settings
    ENTERPRISE_CATALOG_INTERNAL_ROOT_URL,

    IDA_LOGOUT_URI_LIST,

    # Subscription Plans
    PLAN_FEATURES,

    # Methods to derive settings
    _make_mako_template_dirs,
    _make_locale_paths,
)
from path import Path as path
from django.urls import reverse_lazy

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

# pylint: enable=useless-suppression

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


# .. setting_name: STUDIO_NAME
# .. setting_default: Your Platform Studio
# .. setting_description: The name that will appear on the landing page of Studio, as well as in various emails and
#   templates.
STUDIO_NAME = _("Your Platform Studio")
STUDIO_SHORT_NAME = _("Studio")
FEATURES = {
    'GITHUB_PUSH': False,

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the ones in lms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,

    # When True, all courses will be active, regardless of start date
    # DO NOT SET TO True IN THIS FILE
    # Doing so will cause all courses to be released on production
    'DISABLE_START_DATES': False,

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

    # Toggle to enable coordination with the Publisher tool (keep in sync with lms/envs/common.py)
    'ENABLE_PUBLISHER': False,

    # Show a new field in "Advanced settings" that can store custom data about a
    # course and that can be read from themes
    'ENABLE_OTHER_COURSE_SETTINGS': False,

    # Write new CSM history to the extended table.
    # This will eventually default to True and may be
    # removed since all installs should have the separate
    # extended history table. This is needed in the LMS and CMS
    # for migration consistency.
    'ENABLE_CSMH_EXTENDED': True,

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

    # Enable content libraries (modulestore) search functionality
    'ENABLE_LIBRARY_INDEX': False,

    # Enable content libraries (blockstore) indexing
    'ENABLE_CONTENT_LIBRARY_INDEX': False,

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

    'ENABLE_PASSWORD_RESET_FAILURE_EMAIL': False,

    # Whether archived courses (courses with end dates in the past) should be
    # shown in Studio in a separate list.
    'ENABLE_SEPARATE_ARCHIVED_COURSES': True,

    # For acceptance and load testing
    'AUTOMATIC_AUTH_FOR_TESTING': False,

    # Prevent auto auth from creating superusers or modifying existing users
    'RESTRICT_AUTOMATIC_AUTH': True,

    'ENABLE_INSTRUCTOR_ANALYTICS': False,
    'PREVIEW_LMS_BASE': "preview.localhost:18000",
    'ENABLE_GRADE_DOWNLOADS': True,
    'ENABLE_MKTG_SITE': False,
    'ENABLE_DISCUSSION_HOME_PANEL': True,
    'ENABLE_CORS_HEADERS': False,
    'ENABLE_CROSS_DOMAIN_CSRF_COOKIE': False,
    'ENABLE_COUNTRY_ACCESS': False,
    'ENABLE_CREDIT_API': False,
    'ENABLE_OAUTH2_PROVIDER': False,
    'ENABLE_SYSADMIN_DASHBOARD': False,
    'ENABLE_MOBILE_REST_API': False,
    'CUSTOM_COURSES_EDX': False,
    'ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES': True,
    'SHOW_FOOTER_LANGUAGE_SELECTOR': False,
    'ENABLE_ENROLLMENT_RESET': False,
    'DISABLE_MOBILE_COURSE_AVAILABLE': False,

    # .. toggle_name: ENABLE_CHANGE_USER_PASSWORD_ADMIN
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: Set to True to enable changing a user password through django admin. This is disabled by
    #   default because enabling allows a method to bypass password policy.
    # .. toggle_use_cases: open_edx
    # .. toggle_creation_date: 2020-02-21
    # .. toggle_target_removal_date: None
    # .. toggle_warnings: None
    # .. toggle_tickets: 'https://github.com/edx/edx-platform/pull/21616'
    'ENABLE_CHANGE_USER_PASSWORD_ADMIN': False,

    ### ORA Feature Flags ###
    # .. toggle_name: ENABLE_ORA_ALL_FILE_URLS
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: A "work-around" feature toggle meant to help in cases where some file uploads are not
    #   discoverable. If enabled, will iterate through all possible file key suffixes up to the max for displaying file
    #   metadata in staff assessments.
    # .. toggle_use_cases: temporary
    # .. toggle_creation_date: 2020-03-03
    # .. toggle_target_removal_date: None
    # .. toggle_tickets: https://openedx.atlassian.net/browse/EDUCATOR-4951
    # .. toggle_warnings: This temporary feature toggle does not have a target removal date.
    'ENABLE_ORA_ALL_FILE_URLS': False,

    # .. toggle_name: ENABLE_ORA_USER_STATE_UPLOAD_DATA
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: A "work-around" feature toggle meant to help in cases where some file uploads are not
    #   discoverable. If enabled, will pull file metadata from StudentModule.state for display in staff assessments.
    # .. toggle_use_cases: temporary
    # .. toggle_creation_date: 2020-03-03
    # .. toggle_target_removal_date: None
    # .. toggle_tickets: https://openedx.atlassian.net/browse/EDUCATOR-4951
    # .. toggle_warnings: This temporary feature toggle does not have a target removal date.
    'ENABLE_ORA_USER_STATE_UPLOAD_DATA': False,

    # .. toggle_name: DEPRECATE_OLD_COURSE_KEYS_IN_STUDIO
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: True
    # .. toggle_description: Warn about removing support for deprecated course keys.
    #      To enable, set to True.
    #      To disable, set to False.
    #      To enable with a custom support deadline, set to an ISO-8601 date string:
    #        eg: '2020-09-01'
    # .. toggle_use_cases: temporary
    # .. toggle_creation_date: 2020-06-12
    # .. toggle_target_removal_date: 2020-12-01
    # .. toggle_warnings: This can be removed once support is removed for deprecated
    #   course keys.
    # .. toggle_tickets: https://openedx.atlassian.net/browse/DEPR-58
    'DEPRECATE_OLD_COURSE_KEYS_IN_STUDIO': True,

    # .. toggle_name: ENABLE_LIBRARY_AUTHORING_MICROFRONTEND
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: Set to True to enable the Library Authoring MFE
    # .. toggle_use_cases: temporary
    # .. toggle_creation_date: 2020-06-20
    # .. toggle_target_removal_date: 2020-12-31
    # .. toggle_tickets: https://openedx.atlassian.net/wiki/spaces/COMM/pages/1545011241/BD-14+Blockstore+Powered+Content+Libraries+Taxonomies
    # .. toggle_warnings: Also set settings.LIBRARY_AUTHORING_MICROFRONTEND_URL and see
    #   REDIRECT_TO_LIBRARY_AUTHORING_MICROFRONTEND for rollout.
    'ENABLE_LIBRARY_AUTHORING_MICROFRONTEND': False,
}

ENABLE_JASMINE = False

# List of logout URIs for each IDA that the learner should be logged out of when they logout of the LMS. Only applies to
# IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = []

############################# MICROFRONTENDS ###################################
COURSE_AUTHORING_MICROFRONTEND_URL = None
LIBRARY_AUTHORING_MICROFRONTEND_URL = None

############################# SOCIAL MEDIA SHARING #############################
SOCIAL_SHARING_SETTINGS = {
    # Note: Ensure 'CUSTOM_COURSE_URLS' has a matching value in lms/envs/common.py
    'CUSTOM_COURSE_URLS': False,
    'DASHBOARD_FACEBOOK': False,
    'CERTIFICATE_FACEBOOK': False,
    'CERTIFICATE_TWITTER': False,
    'DASHBOARD_TWITTER': False
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

# TODO: This path modification exists as temporary support for deprecated import patterns.
# It will be removed in an upcoming Open edX release.
# See docs/decisions/0007-sys-path-modification-removal.rst
sys.path.append(REPO_ROOT / 'import_shims' / 'studio')

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoLite2-Country.mmdb"

DATA_DIR = COURSES_ROOT

DJFS = {
    'type': 'osfs',
    'directory_root': '/edx/var/edxapp/django-pyfs/static/django-pyfs',
    'url_root': '/static/django-pyfs',
}
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

    # edly context processors
    'openedx.features.edly.context_processor.dynamic_theming_context',
    'openedx.features.edly.context_processor.edly_app_context'
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
                'common.djangoapps.edxmako.makoloader.MakoFilesystemLoader',
                'common.djangoapps.edxmako.makoloader.MakoAppDirectoriesLoader',
            ),
            'context_processors': CONTEXT_PROCESSORS,
            # Change 'debug' in your environment settings files - not here.
            'debug': False
        }
    },
    {
        'NAME': 'mako',
        'BACKEND': 'common.djangoapps.edxmako.backend.Mako',
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
        'BACKEND': 'common.djangoapps.edxmako.backend.Mako',
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
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
AWS_SECURITY_TOKEN = None
AWS_QUERYSTRING_AUTH = False
AWS_STORAGE_BUCKET_NAME = 'SET-ME-PLEASE (ex. bucket-name)'
AWS_S3_CUSTOM_DOMAIN = 'SET-ME-PLEASE (ex. bucket-name.s3.amazonaws.com)'

##############################################################################

EDX_ROOT_URL = ''

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

LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/home/'
# TODO: Determine if LOGIN_URL could be set to the FRONTEND_LOGIN_URL value instead.
LOGIN_URL = reverse_lazy('login_redirect_to_lms')
FRONTEND_LOGIN_URL = lambda settings: settings.LMS_ROOT_URL + '/login'
derived('FRONTEND_LOGIN_URL')
FRONTEND_LOGOUT_URL = lambda settings: settings.LMS_ROOT_URL + '/logout'
derived('FRONTEND_LOGOUT_URL')
FRONTEND_REGISTER_URL = lambda settings: settings.LMS_ROOT_URL + '/register'
derived('FRONTEND_REGISTER_URL')

LMS_ENROLLMENT_API_PATH = "/api/enrollment/v1/"
ENTERPRISE_API_URL = LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS = {}

# Public domain name of Studio (should be resolvable from the end-user's browser)
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
CSRF_TRUSTED_ORIGINS = []

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

MIDDLEWARE = [
    'openedx.core.lib.x_forwarded_for.middleware.XForwardedForMiddleware',

    # Avoid issue with https://blog.heroku.com/chrome-changes-samesite-cookie
    # Override was found here https://github.com/django/django/pull/11894
    'django_cookies_samesite.middleware.CookiesSameSite',

    'crum.CurrentRequestUserMiddleware',

    # CORS and CSRF
    'corsheaders.middleware.CorsMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CorsCSRFMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CsrfCrossDomainCookieMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # A newer and safer request cache.
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'edx_django_utils.monitoring.MonitoringMemoryMiddleware',

    # Cookie monitoring
    'openedx.core.lib.request_utils.CookieMonitoringMiddleware',

    'openedx.core.djangoapps.header_control.middleware.HeaderControlMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',

    # CORS and CSRF
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CorsCSRFMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CsrfCrossDomainCookieMiddleware',

    # JWT auth
    'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',

    'openedx.features.edly.middleware.SettingsOverrideMiddleware',

    # Allows us to define redirects via Django admin
    'django_sites_extensions.middleware.RedirectMiddleware',

    # Instead of SessionMiddleware, we use a more secure version
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware',

    'method_override.middleware.MethodOverrideMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'openedx.core.djangoapps.cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'common.djangoapps.student.middleware.UserStandingMiddleware',
    'openedx.core.djangoapps.contentserver.middleware.StaticContentServer',

    'django.contrib.messages.middleware.MessageMiddleware',
    'common.djangoapps.track.middleware.TrackMiddleware',

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

    # Adds monitoring attributes to requests.
    'edx_rest_framework_extensions.middleware.RequestCustomAttributesMiddleware',

    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',

    'openedx.features.edly.middleware.EdlyOrganizationAccessMiddleware',
    # Handles automatically storing user ids in django-simple-history tables when possible.
    'simple_history.middleware.HistoryRequestMiddleware',

    # This must be last so that it runs first in the process_response chain
    'openedx.core.djangoapps.site_configuration.middleware.SessionCookieDomainOverrideMiddleware',
]

# Edly Configuration
ADMIN_CONFIGURATION_USERS_GROUP = 'Admin Configuration Users'
EDLY_PANEL_USERS_GROUP = 'Edly Panel Users'
EDLY_INSIGHTS_GROUP = 'Edly Insights Admin'
EDLY_PANEL_ADMIN_USERS_GROUP = 'Edly Panel Admin Users'
EDLY_PANEL_RESTRICTED_USERS_GROUP = 'Edly Panel Restricted Users'
EDLY_WP_ADMIN_USERS_GROUP = 'WordPress Edly Admin Users'
EDLY_WP_SUBSCRIBER_USERS_GROUP = 'WordPress Subscriber Users'
EDLY_API_USERS_GROUP = 'Edly API Users'
EDLY_PANEL_SUPER_ADMIN = 'Edly Panel Super Admin'


EDLY_USER_ROLES = {
    'panel_restricted': EDLY_PANEL_RESTRICTED_USERS_GROUP,
    'panel_user': EDLY_PANEL_USERS_GROUP,
    'insights_admin': EDLY_INSIGHTS_GROUP,
    'panel_admin': EDLY_PANEL_ADMIN_USERS_GROUP,
    'subscriber': EDLY_WP_SUBSCRIBER_USERS_GROUP,
    'edly_admin': EDLY_WP_ADMIN_USERS_GROUP,
    'super_admin': EDLY_PANEL_SUPER_ADMIN
}

ENABLE_EDLY_ORGANIZATIONS_SWITCH = 'enable_edly_organizations'
EDLY_USER_INFO_COOKIE_NAME = 'edly-user-info'
EDLY_COOKIE_SECRET_KEY = 'EDLY-COOKIE-SECRET-KEY'
EDLY_JWT_ALGORITHM = 'HS256'

ALLOWED_SITE_CONFIGURATIONS_OVERRIDE = [
    'BRANDING', 'COLORS', 'ALLOW_PUBLIC_ACCOUNT_CREATION', 'REGISTRATION_EXTRA_FIELDS',
    'EMAILS_CONFIG', 'DJANGO_SETTINGS_OVERRIDE', 'GTM_ID', 'GA_ID', 'MOBILE_ENABLED',
    'MOBILE_APP_CONFIG'
]

ALLOWED_DJANGO_SETTINGS_OVERRIDE = [
    'SITE_NAME', 'PLATFORM_NAME', 'STUDIO_NAME', 'LANGUAGE_CODE', 'LMS_BASE', 'LMS_ROOT_URL',
    'SESSION_COOKIE_DOMAIN', 'CSRF_TRUSTED_ORIGINS', 'CMS_BASE',
    'FRONTEND_LOGIN_URL', 'FRONTEND_LOGOUT_URL', 'LOGIN_REDIRECT_WHITELIST',
    'DEFAULT_FROM_EMAIL', 'BULK_EMAIL_DEFAULT_FROM_EMAIL',
    'FEATURES', 'MKTG_URLS', 'MARKETING_SITE_ROOT',
    'CORS_ORIGIN_WHITELIST', 'CURRENT_PLAN', 'LMS_SEGMENT_KEY', 'CMS_SEGMENT_KEY', 'BADGR_USERNAME', 'BADGR_PASSWORD',
    'BADGR_ISSUER_SLUG', 'BADGR_FLAG'
]

# CORS CONFIG
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_INSECURE = True
CORS_ORIGIN_WHITELIST = (
    'http://panel.dev.edly.com',
    'http://panel.backend.dev.edly.com',
)
EXTRA_MIDDLEWARE_CLASSES = []

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
ORA2_FILE_PREFIX = 'default_env-default_deployment/ora2'

# Default File Upload Storage bucket and prefix. Used by the FileUpload Service.
FILE_UPLOAD_STORAGE_BUCKET_NAME = 'SET-ME-PLEASE (ex. bucket-name)'
FILE_UPLOAD_STORAGE_PREFIX = 'submissions_attachments'

############################ Modulestore Configuration ################################

DOC_STORE_CONFIG = {
    'db': 'edxapp',
    'host': 'localhost',
    'replicaSet': '',
    'user': 'edxapp',
    'port': 27017,
    'collection': 'modulestore',
    'ssl': False,
    # https://api.mongodb.com/python/2.9.1/api/pymongo/mongo_client.html#module-pymongo.mongo_client
    # default is never timeout while the connection is open,
    #this means it needs to explicitly close raising pymongo.errors.NetworkTimeout
    'socketTimeoutMS': 6000,
    'connectTimeoutMS': 2000,  # default is 20000, I believe raises pymongo.errors.ConnectionFailure
    # Not setting waitQueueTimeoutMS and waitQueueMultiple since pymongo defaults to nobody being allowed to wait
    'auth_source': None,
    'read_preference': 'PRIMARY'
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
        'password': 'password',
        'port': 27017,
        'user': 'edxapp',
        'ssl': False,
        'auth_source': None
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
                        'render_template': 'common.djangoapps.edxmako.shortcuts.render_to_string',
                    }
                },
                {
                    'NAME': 'draft',
                    'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': DATA_DIR,
                        'render_template': 'common.djangoapps.edxmako.shortcuts.render_to_string',
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
        'NAME': 'edxapp',
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
        'USER': 'edxapp001'
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

    # Overrides to default configurable 'limits' (above).
    # Keys should be course run ids.
    # Values should be dictionaries that look like 'limits'.
    "limit_overrides": {},
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
SESSION_COOKIE_AGE = 2592000 # Default: 30 days, in seconds
SESSION_SERIALIZER = 'openedx.core.lib.session_serializers.PickleSerializer'
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
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
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

STATICI18N_FILENAME_FUNCTION = 'statici18n.utils.legacy_filename'
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

    #    This fix is useless in the Maple release.
    #    The upstream Open edX fix is https://github.com/edx/edx-platform/pull/25957
    #    For more details see: https://github.com/jazzband/django-pipeline/pull/715
    #
    'MIMETYPES': (
        (str('text/coffeescript'), str('.coffee')),
        (str('text/less'), str('.less')),
        (str('text/javascript'), str('.js')),
        (str('text/x-sass'), str('.sass')),
        (str('text/x-scss'), str('.scss')),
    )
}

STATICFILES_STORAGE = 'openedx.core.storage.ProductionStorage'
STATICFILES_STORAGE_KWARGS = {}

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


############################ SERVICE_VARIANT ##################################

# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', 'cms')

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""


################################# CELERY ######################################

# Celery beat configuration

CELERYBEAT_SCHEDULER = 'celery.beat:PersistentScheduler'

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

# Name the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = f'edx.{QUEUE_VARIANT}core'

HIGH_PRIORITY_QUEUE = f'edx.{QUEUE_VARIANT}core.high'
DEFAULT_PRIORITY_QUEUE = f'edx.{QUEUE_VARIANT}core.default'

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {}
}

# Queues configuration

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_CREATE_MISSING_QUEUES = True

CELERY_BROKER_TRANSPORT = 'amqp'
CELERY_BROKER_HOSTNAME = 'localhost'
CELERY_BROKER_USER = 'celery'
CELERY_BROKER_PASSWORD = 'celery'
CELERY_BROKER_VHOST = ''
CELERY_BROKER_USE_SSL = False
CELERY_EVENT_QUEUE_TTL = None

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

############################# SETTINGS FOR VIDEO UPLOAD PIPELINE #############################

VIDEO_UPLOAD_PIPELINE = {
    'VEM_S3_BUCKET': '',
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
    'django_celery_results',
    'method_override',

    # Common Initialization
    'openedx.core.djangoapps.common_initialization.apps.CommonInitializationConfig',

    # Common views
    'openedx.core.djangoapps.common_views',

    # API access administration
    'openedx.core.djangoapps.api_admin',

    # CORS and cross-domain CSRF
    'corsheaders',
    'openedx.core.djangoapps.cors_csrf',

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
    'cms.djangoapps.contentstore.apps.ContentstoreConfig',

    'openedx.core.djangoapps.contentserver',
    'cms.djangoapps.course_creators',
    'common.djangoapps.student.apps.StudentConfig',  # misleading name due to sharing with lms
    'openedx.core.djangoapps.course_groups',  # not used in cms (yet), but tests run
    'cms.djangoapps.xblock_config.apps.XBlockConfig',

    # New (Blockstore-based) XBlock runtime
    'openedx.core.djangoapps.xblock.apps.StudioXBlockAppConfig',

    # Maintenance tools
    'cms.djangoapps.maintenance',
    'openedx.core.djangoapps.util.apps.UtilConfig',

    # Tracking
    'common.djangoapps.track',
    'eventtracking.django.apps.EventTrackingConfig',

    # For asset pipelining
    'common.djangoapps.edxmako.apps.EdxMakoConfig',
    'pipeline',
    'common.djangoapps.static_replace',
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
    'common.djangoapps.course_modes.apps.CourseModesConfig',

    # Verified Track Content Cohorting (Beta feature that will hopefully be removed)
    'openedx.core.djangoapps.verified_track_content',

    # Dark-launching languages
    'openedx.core.djangoapps.dark_lang',

    #
    # User preferences
    'wiki',
    'django_notify',
    'lms.djangoapps.course_wiki',  # Our customizations
    'mptt',
    'sekizai',
    'openedx.core.djangoapps.user_api',

    # Country embargo support
    'openedx.core.djangoapps.embargo',

    # Course action state
    'common.djangoapps.course_action_state',

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

    'common.djangoapps.xblock_django',

    # Catalog integration
    'openedx.core.djangoapps.catalog',

    # Programs support
    'openedx.core.djangoapps.programs.apps.ProgramsConfig',

    # django-oauth-toolkit
    'oauth2_provider',

    # These are apps that aren't strictly needed by Studio, but are imported by
    # other apps that are.  Django 1.8 wants to have imported models supported
    # by installed apps.
    'openedx.core.djangoapps.oauth_dispatch.apps.OAuthDispatchAppConfig',
    'lms.djangoapps.courseware',
    'lms.djangoapps.coursewarehistoryextended',
    'lms.djangoapps.survey.apps.SurveyConfig',
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
    'completion',

    # System Wide Roles
    'openedx.core.djangoapps.system_wide_roles',

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
    'cms.djangoapps.cms_user_tasks.apps.CmsUserTasksConfig',

    # Unusual migrations
    'common.djangoapps.database_fixups',

    # Customized celery tasks, including persisting failed tasks so they can
    # be retried
    'celery_utils',

    # Waffle related utilities
    'openedx.core.djangoapps.waffle_utils',

    # DRF filters
    'django_filters',
    'cms.djangoapps.api',

    # edx-drf-extensions
    'csrf.apps.CsrfAppConfig',  # Enables frontend apps to retrieve CSRF tokens.

    # Entitlements, used in openedx tests
    'common.djangoapps.entitlements',

    # Asset management for mako templates
    'common.djangoapps.pipeline_mako',

    # API Documentation
    'drf_yasg',

    'openedx.features.course_duration_limits',
    'openedx.features.content_type_gating',
    'openedx.features.discounts',
    'lms.djangoapps.experiments',

    # Edly apps
    'openedx.features.edly',
    'edly_panel_app',
    'openedx.features.subscriptions',
    'openedx.core.djangoapps.external_user_ids',
    # so sample_task is available to celery workers
    'openedx.core.djangoapps.heartbeat',

    # signal handlers to capture course dates into edx-when
    'openedx.core.djangoapps.course_date_signals',

    # Management of per-user schedules
    'openedx.core.djangoapps.schedules',
    'rest_framework_jwt',

    # Learning Sequence Navigation
    'openedx.core.djangoapps.content.learning_sequences.apps.LearningSequencesConfig',

    'ratelimitbackend',
]


################# EDX MARKETING SITE ##################################

EDXMKTG_LOGGED_IN_COOKIE_NAME = 'edxloggedin'
EDXMKTG_USER_INFO_COOKIE_NAME = 'edx-user-info'
EDXMKTG_USER_INFO_COOKIE_VERSION = 1

MKTG_URLS = {}
MKTG_URL_OVERRIDES = {}
MKTG_URL_LINK_MAP = {

}

SUPPORT_SITE_LINK = ''
ID_VERIFICATION_SUPPORT_LINK = ''
PASSWORD_RESET_SUPPORT_LINK = ''
ACTIVATION_EMAIL_SUPPORT_LINK = ''
LOGIN_ISSUE_SUPPORT_LINK = ''

############################## EVENT TRACKING #################################

CMS_SEGMENT_KEY = None
TRACK_MAX_EVENT = 50000

TRACKING_BACKENDS = {
    'logger': {
        'ENGINE': 'common.djangoapps.track.backends.logger.LoggerBackend',
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
                {'ENGINE': 'common.djangoapps.track.shim.LegacyFieldMappingProcessor'},
                {'ENGINE': 'common.djangoapps.track.shim.PrefixedEventProcessor'}
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
                    'ENGINE': 'common.djangoapps.track.shim.GoogleAnalyticsProcessor'
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
        "NAME": "common.djangoapps.util.password_policy_validators.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 2
        }
    },
    {
        "NAME": "common.djangoapps.util.password_policy_validators.MaximumLengthValidator",
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
    ('integrated_channels.blackboard', None),
    ('integrated_channels.canvas', None),
    ('integrated_channels.moodle', None),

    # Xblocks Apps
    ('kwl.kwl_djangoapp', None),
)


for app_name, insert_before in OPTIONAL_APPS:
    # First attempt to only find the module rather than actually importing it,
    # to avoid circular references - only try to import if it can't be found
    # by find_spec, which doesn't work with import hooks
    if importlib.util.find_spec(app_name) is None:
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
    },
    {
        'component': 'edlyrating',
        'boilerplate_name': None
    },
    {
        'component': 'lti_consumer',
        'boilerplate_name': None
    },
    {
        'component': 'kwl',
        'boilerplate_name': None
    },
    {
        'component': 'annotatable',
        'boilerplate_name': None
    },
    {
        'component': 'google-document',
        'boilerplate_name': None
    },
    {
        'component': 'library_content',
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
RETIREMENT_SERVICE_USER_EMAIL = "retirement_worker@example.com"
RETIREMENT_SERVICE_USER_NAME = "retirement_worker"

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

############################ Global Database Configuration #####################

DATABASE_ROUTERS = [
    'openedx.core.lib.django_courseware_routers.StudentModuleHistoryExtendedRouter',
]

############################ Cache Configuration ###############################

CACHES = {
    'blockstore': {
        'KEY_PREFIX': 'blockstore',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': '86400',  # This data should be long-lived for performance, BundleCache handles invalidation
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'course_structure_cache': {
        'KEY_PREFIX': 'course_structure',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': '7200',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'celery': {
        'KEY_PREFIX': 'celery',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': '7200',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'mongo_metadata_inheritance': {
        'KEY_PREFIX': 'mongo_metadata_inheritance',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'TIMEOUT': 300,
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'staticfiles': {
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'staticfiles_general',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'default': {
        'VERSION': '1',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'default',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'configuration': {
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'configuration',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
    'general': {
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': ['localhost:11211'],
        'KEY_PREFIX': 'general',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
}

############################ OAUTH2 Provider ###################################


# 5 minute expiration time for JWT id tokens issued for external API requests.
OAUTH_ID_TOKEN_EXPIRATION = 5 * 60

# Partner support link for CMS footer
PARTNER_SUPPORT_EMAIL = ''

# Affiliate cookie tracking
AFFILIATE_COOKIE_NAME = 'dev_affiliate_id'

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

# Software Secure request retry settings
# Time in seconds before a retry of the task should be 60 mints.
SOFTWARE_SECURE_REQUEST_RETRY_DELAY = 60 * 60
# Maximum of 6 retries before giving up.
SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS = 6

############## DJANGO-USER-TASKS ##############

# How long until database records about the outcome of a task and its artifacts get deleted?
USER_TASKS_MAX_AGE = timedelta(days=7)

############## Settings for the Enterprise App ######################

ENTERPRISE_ENROLLMENT_API_URL = LMS_ROOT_URL + LMS_ENROLLMENT_API_PATH
ENTERPRISE_SERVICE_WORKER_USERNAME = 'enterprise_worker'
ENTERPRISE_API_CACHE_TIMEOUT = 3600  # Value is in seconds
# The default value of this needs to be a 16 character string
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = {}

# The setting key maps to the channel code (e.g. 'SAP' for success factors), Channel code is defined as
# part of django model of each integrated channel in edx-enterprise.
# The absence of a key/value pair translates to NO LIMIT on the number of "chunks" transmitted per cycle.
INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT = {}

BASE_COOKIE_DOMAIN = 'localhost'

# This limits the type of roles that are submittable via the `student` app's manual enrollment
# audit API. While this isn't used in CMS, it is used via Enterprise which is installed in
# the CMS. Without this, we get errors.
MANUAL_ENROLLMENT_ROLE_CHOICES = ['Learner', 'Support', 'Partner']

############## Settings for the Discovery App ######################

COURSE_CATALOG_URL_ROOT = 'http://localhost:8008'
COURSE_CATALOG_API_URL = '{}/api/v1'.format(COURSE_CATALOG_URL_ROOT)

# which access.py permission name to check in order to determine if a course is visible in
# the course catalog. We default this to the legacy permission 'see_exists'.
COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_exists'

# which access.py permission name to check in order to determine if a course about page is
# visible. We default this to the legacy permission 'see_exists'.
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_exists'

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = "both"
DEFAULT_MOBILE_AVAILABLE = False


# How long to cache OpenAPI schemas and UI, in seconds.
OPENAPI_CACHE_TIMEOUT = 0

################# Mobile URLS ##########################

# These are URLs to the app store for mobile.
MOBILE_STORE_URLS = {}

############################# Persistent Grades ####################################

# Queue to use for updating persistent grades
RECALCULATE_GRADES_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = 'edx.lms.core.default'

SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = 'edx.lms.core.default'

# Rate limit for regrading tasks that a grading policy change can kick off
POLICY_CHANGE_TASK_RATE_LIMIT = '300/h'

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

########## Settings for video transcript migration tasks ############
VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

########## Settings youtube thumbnails scraper tasks ############
SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

########## Settings update search index task ############
UPDATE_SEARCH_INDEX_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE

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
ZENDESK_USER = ''
ZENDESK_API_KEY = ''
ZENDESK_CUSTOM_FIELDS = {}
ZENDESK_OAUTH_ACCESS_TOKEN = ''
# A mapping of string names to Zendesk Group IDs
# To get the IDs of your groups you can go to
# {zendesk_url}/api/v2/groups.json
ZENDESK_GROUP_ID_MAPPING = {}

############## Settings for Completion API #########################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = 0.95

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = []

############## Installed Django Apps #########################

from edx_django_utils.plugins import get_plugin_apps, add_plugins
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

INSTALLED_APPS.extend(get_plugin_apps(ProjectType.CMS))
add_plugins(__name__, ProjectType.CMS, SettingsType.COMMON)

# Course exports streamed in blocks of this size. 8192 or 8kb is the default
# setting for the FileWrapper class used to iterate over the export file data.
# See: https://docs.python.org/2/library/wsgiref.html#wsgiref.util.FileWrapper
COURSE_EXPORT_DOWNLOAD_CHUNK_SIZE = 8192

# E-Commerce API Configuration
ECOMMERCE_PUBLIC_URL_ROOT = 'http://localhost:8002'
ECOMMERCE_API_URL = 'http://localhost:8002/api/v2'
ECOMMERCE_API_SIGNING_KEY = 'SET-ME-PLEASE'

CREDENTIALS_INTERNAL_SERVICE_URL = 'http://localhost:8005'
CREDENTIALS_PUBLIC_SERVICE_URL = 'http://localhost:8005'

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

############# CORS headers for cross-domain requests #################
if FEATURES.get('ENABLE_CORS_HEADERS'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = ()
    CORS_ORIGIN_ALLOW_ALL = False
    CORS_ALLOW_INSECURE = False
    CORS_ALLOW_HEADERS = corsheaders_default_headers + (
        'use-jwt-cookie',
    )

LOGIN_REDIRECT_WHITELIST = []

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
SWIFT_USE_TEMP_URLS = False
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

############### Settings for django-fernet-fields ##################
FERNET_KEYS = [
    'DUMMY KEY CHANGE BEFORE GOING TO PRODUCTION',
]

### Proctoring configuration (redirct URLs and keys shared between systems) ####
PROCTORING_BACKENDS = {
    'DEFAULT': 'null',
    # The null key needs to be quoted because
    # null is a language independent type in YAML
    'null': {}
}

PROCTORING_SETTINGS = {}

################## BLOCKSTORE RELATED SETTINGS  #########################
BLOCKSTORE_PUBLIC_URL_ROOT = 'http://localhost:18250'
BLOCKSTORE_API_URL = 'http://localhost:18250/api/v1/'
# Which of django's caches to use for storing anonymous user state for XBlocks
# in the blockstore-based XBlock runtime
XBLOCK_RUNTIME_V2_EPHEMERAL_DATA_CACHE = 'default'

###################### LEARNER PORTAL ################################
LEARNER_PORTAL_URL_ROOT = 'https://learner-portal-localhost:18000'

######################### MICROSITE ###############################
MICROSITE_ROOT_DIR = '/edx/app/edxapp/edx-microsite'
MICROSITE_CONFIGURATION = {}

############################ JWT #################################
JWT_ISSUER = 'http://127.0.0.1:8000/oauth2'
DEFAULT_JWT_ISSUER = {
    'ISSUER': 'http://127.0.0.1:8000/oauth2',
    'AUDIENCE': 'SET-ME-PLEASE',
    'SECRET_KEY': 'SET-ME-PLEASE'
}
JWT_EXPIRATION = 30
JWT_PRIVATE_SIGNING_KEY = None


SYSLOG_SERVER = ''
FEEDBACK_SUBMISSION_EMAIL = ''
REGISTRATION_EXTRA_FIELDS = {
    'confirm_email': 'hidden',
    'level_of_education': 'optional',
    'gender': 'optional',
    'year_of_birth': 'optional',
    'mailing_address': 'optional',
    'goals': 'optional',
    'honor_code': 'required',
    'terms_of_service': 'hidden',
    'city': 'hidden',
    'country': 'hidden',
}
EDXAPP_PARSE_KEYS = {}

###################### DEPRECATED URLS ##########################

# .. toggle_name: DISABLE_DEPRECATED_SIGNIN_URL
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Toggle for removing the deprecated /signin url.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2019-12-02
# .. toggle_target_removal_date: 2020-06-01
# .. toggle_warnings: This url can be removed once it no longer has any real traffic.
# .. toggle_tickets: ARCH-1253
DISABLE_DEPRECATED_SIGNIN_URL = False

# .. toggle_name: DISABLE_DEPRECATED_SIGNUP_URL
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Toggle for removing the deprecated /signup url.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2019-12-02
# .. toggle_target_removal_date: 2020-06-01
# .. toggle_warnings: This url can be removed once it no longer has any real traffic.
# .. toggle_tickets: ARCH-1253
DISABLE_DEPRECATED_SIGNUP_URL = False

##### LOGISTRATION RATE LIMIT SETTINGS #####
LOGISTRATION_RATELIMIT_RATE = '100/5m'
LOGISTRATION_API_RATELIMIT = '20/m'

##### REGISTRATION RATE LIMIT SETTINGS #####
REGISTRATION_VALIDATION_RATELIMIT = '30/7d'

##### PASSWORD RESET RATE LIMIT SETTINGS #####
PASSWORD_RESET_IP_RATE = '1/m'
PASSWORD_RESET_EMAIL_RATE = '2/h'

######################## Setting for content libraries ########################
MAX_BLOCKS_PER_CONTENT_LIBRARY = 1000

################# Student Verification #################
VERIFY_STUDENT = {
    "DAYS_GOOD_FOR": 365,  # How many days is a verficiation good for?
    # The variable represents the window within which a verification is considered to be "expiring soon."
    "EXPIRING_SOON_WINDOW": 28,
}

######################## Organizations ########################

# .. toggle_name: ORGANIZATIONS_AUTOCREATE
# .. toggle_implementation: DjangoSetting
# .. toggle_default: True
# .. toggle_description: When enabled, creating a course run or content library with
#   an "org slug" that does not map to an Organization in the database will trigger the
#   creation of a new Organization, with its name and short_name set to said org slug.
#   When disabled, creation of such content with an unknown org slug will instead
#   result in a validation error.
#   If you want the Organization table to be an authoritative information source in
#   Studio, then disable this; however, if you want the table to just be a reflection of
#   the orgs referenced in Studio content, then leave it enabled.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-11-02
ORGANIZATIONS_AUTOCREATE = True

################# Settings for brand logos. #################
LOGO_URL = None
LOGO_URL_PNG = None
LOGO_TRADEMARK_URL = None
FAVICON_URL = None
DEFAULT_EMAIL_LOGO_URL = 'https://edx-cdn.org/v3/default/logo.png'

# HOTJAR ANALYTICS
HOTJAR_TRACKING_ID = None

# MIXPANEL ANALYTICS PROJECT TOKEN
MIXPANEL_PROJECT_TOKEN = 'replace-me'

# USETIFUL PRODUCT TOUR TOKEN
USETIFUL_TOKEN = 'USETIFUL_TOKEN'

# REDIRECT URL FOR EXPIRED SITES
EXPIRE_REDIRECT_URL = 'http://wordpress.edx.devstack.lms/pricing-and-plans/'

# OPEN AI API KEY
OPENAI_SECRET_KEY = 'set-secret-key'
