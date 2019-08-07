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
"""

# We intentionally define lots of variables that aren't used
# pylint: disable=unused-import

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name, wrong-import-position

from __future__ import absolute_import

import imp
import sys
import os

from corsheaders.defaults import default_headers as corsheaders_default_headers
from path import Path as path
from django.utils.translation import ugettext_lazy as _
from enterprise.constants import (
    ENTERPRISE_ADMIN_ROLE,
    ENTERPRISE_CATALOG_ADMIN_ROLE,
    ENTERPRISE_DASHBOARD_ADMIN_ROLE,
    ENTERPRISE_ENROLLMENT_API_ADMIN_ROLE,
    ENTERPRISE_OPERATOR_ROLE
)

from openedx.core.constants import COURSE_KEY_REGEX, COURSE_KEY_PATTERN, COURSE_ID_PATTERN
from openedx.core.djangoapps.theming.helpers_dirs import (
    get_themes_unchecked,
    get_theme_base_dirs_from_settings
)
from openedx.core.lib.derived import derived, derived_collection_entry
from openedx.core.release import doc_version
from xmodule.modulestore.modulestore_settings import update_module_store_settings
from xmodule.modulestore.edit_info import EditInfoMixin
from lms.djangoapps.lms_xblock.mixin import LmsBlockMixin

################################### FEATURES ###################################
# The display name of the platform to be used in templates/emails/etc.
PLATFORM_NAME = _('Your Platform Name Here')
PLATFORM_DESCRIPTION = _('Your Platform Description Here')
CC_MERCHANT_NAME = PLATFORM_NAME

PLATFORM_FACEBOOK_ACCOUNT = "http://www.facebook.com/YourPlatformFacebookAccount"
PLATFORM_TWITTER_ACCOUNT = "@YourPlatformTwitterAccount"


ENABLE_JASMINE = False

LMS_ROOT_URL = 'https://localhost:18000'
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL
LMS_ENROLLMENT_API_PATH = "/api/enrollment/v1/"

# Default choices for role dropdown in the membership tab of the instructor dashboard
# This setting is used when a site does not define its own choices via site configuration
MANUAL_ENROLLMENT_ROLE_CHOICES = ['Learner', 'Support', 'Partner']

# List of logout URIs for each IDA that the learner should be logged out of when they logout of the LMS. Only applies to
# IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = []

# Features
FEATURES = {
    'DISPLAY_DEBUG_INFO_TO_STAFF': True,
    'DISPLAY_HISTOGRAMS_TO_STAFF': False,  # For large courses this slows down courseware access for staff.

    'REROUTE_ACTIVATION_EMAIL': False,  # nonempty string = address for all activation emails

    ## DO NOT SET TO True IN THIS FILE
    ## Doing so will cause all courses to be released on production
    'DISABLE_START_DATES': False,  # When True, all courses will be active, regardless of start date

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the corresponding ones in cms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,

    # .. toggle_name: ENABLE_STUDENT_NOTES
    # .. toggle_type: feature_flag
    # .. toggle_default: True
    # .. toggle_description: Enables the Student Notes API and UI.
    # .. toggle_category: ????
    # .. toggle_use_cases: open_edx
    # .. toggle_creation_date: 2014-11-13
    # .. toggle_expiration_date: None
    # .. toggle_warnings: None
    # .. toggle_tickets: TNL-659
    # .. toggle_status: supported
    'ENABLE_STUDENT_NOTES': True,

    # discussion home panel, which includes a subscription on/off setting for discussion digest emails.
    # this should remain off in production until digest notifications are online.
    'ENABLE_DISCUSSION_HOME_PANEL': False,

    # Set this to True if you want the discussion digest emails enabled automatically for new users.
    # This will be set on all new account registrations.
    # It is not recommended to enable this feature if ENABLE_DISCUSSION_HOME_PANEL is not enabled, since
    # subscribers who receive digests in that case will only be able to unsubscribe via links embedded
    # in their emails, and they will have no way to resubscribe.
    'ENABLE_DISCUSSION_EMAIL_DIGEST': False,

    'ENABLE_DJANGO_ADMIN_SITE': True,  # set true to enable django's admin site, even on prod (e.g. for course ops)
    'ENABLE_SQL_TRACKING_LOGS': False,
    'ENABLE_LMS_MIGRATION': False,

    'ENABLE_MASQUERADE': True,  # allow course staff to change to student view of courseware

    # .. toggle_name: ENABLE_SYSADMIN_DASHBOARD
    # .. toggle_type: feature_flag
    # .. toggle_default: False
    # .. toggle_description: enables dashboard at /syadmin/ for django staff, for seeing overview of system status, for deleting and loading courses, for seeing log of git imports of courseware.
    # .. toggle_category: admin
    # .. toggle_use_cases: open_edx
    # .. toggle_creation_date: 2013-12-12
    # .. toggle_expiration_date: None
    # .. toggle_warnings: some views are not performant when there are more than 100 courses
    # .. toggle_tickets: None
    # .. toggle_status: unsupported
    'ENABLE_SYSADMIN_DASHBOARD': False,  # sysadmin dashboard, to see what courses are loaded, to delete & load courses

    'DISABLE_LOGIN_BUTTON': False,  # used in systems where login is automatic, eg MIT SSL

    # Toggles OAuth2 authentication provider
    'ENABLE_OAUTH2_PROVIDER': False,

    # Allows to enable an API endpoint to serve XBlock view, used for example by external applications.
    # See jquey-xblock: https://github.com/edx-solutions/jquery-xblock
    'ENABLE_XBLOCK_VIEW_ENDPOINT': False,

    # Allows to configure the LMS to provide CORS headers to serve requests from other domains
    'ENABLE_CORS_HEADERS': False,

    # Can be turned off if course lists need to be hidden. Effects views and templates.
    'COURSES_ARE_BROWSABLE': True,

    # Set to hide the courses list on the Learner Dashboard if they are not enrolled in any courses yet.
    'HIDE_DASHBOARD_COURSES_UNTIL_ACTIVATED': False,

    # enable analytics server.
    # WARNING: THIS SHOULD ALWAYS BE SET TO FALSE UNDER NORMAL
    # LMS OPERATION. See analytics.py for details about what
    # this does.
    'RUN_AS_ANALYTICS_SERVER_ENABLED': False,

    # Give a UI to show a student's submission history in a problem by the
    # Staff Debug tool.
    'ENABLE_STUDENT_HISTORY_VIEW': True,

    # Provide a UI to allow users to submit feedback from the LMS (left-hand help modal)
    'ENABLE_FEEDBACK_SUBMISSION': False,

    # Turn on a page that lets staff enter Python code to be run in the
    # sandbox, for testing whether it's enabled properly.
    'ENABLE_DEBUG_RUN_PYTHON': False,

    # Enable URL that shows information about the status of variuous services
    'ENABLE_SERVICE_STATUS': False,

    # Don't autoplay videos for students
    'AUTOPLAY_VIDEOS': False,

    # Move the student to next page when a video finishes. Set to True to show
    # an auto-advance button in videos. If False, videos never auto-advance.
    'ENABLE_AUTOADVANCE_VIDEOS': False,

    # Enable instructor dash to submit background tasks
    'ENABLE_INSTRUCTOR_BACKGROUND_TASKS': True,

    # Enable instructor to assign individual due dates
    # Note: In order for this feature to work, you must also add
    # 'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider' to
    # the setting FIELD_OVERRIDE_PROVIDERS, in addition to setting this flag to
    # True.
    'INDIVIDUAL_DUE_DATES': False,

    # Enable Custom Courses for EdX
    'CUSTOM_COURSES_EDX': False,

    # Toggle to enable certificates of courses on dashboard
    'ENABLE_VERIFIED_CERTIFICATES': False,

    # .. toggle_name: DISABLE_HONOR_CERTIFICATES
    # .. toggle_type: feature_flag
    # .. toggle_default: False
    # .. toggle_description: Set to True to disable honor certificates. Typically used when your installation only allows verified certificates, like courses.edx.org.
    # .. toggle_category: certificates
    # .. toggle_use_cases: open_edx
    # .. toggle_creation_date: 2019-05-14
    # .. toggle_expiration_date: None
    # .. toggle_tickets: https://openedx.atlassian.net/browse/PROD-269
    # .. toggle_status: supported
    'DISABLE_HONOR_CERTIFICATES': False,  # Toggle to disable honor certificates

    # for acceptance and load testing
    'AUTOMATIC_AUTH_FOR_TESTING': False,

    # Prevent auto auth from creating superusers or modifying existing users
    'RESTRICT_AUTOMATIC_AUTH': True,

    # Toggle the availability of the shopping cart page
    'ENABLE_SHOPPING_CART': False,

    # Toggle storing detailed billing information
    'STORE_BILLING_INFO': False,

    # Enable flow for payments for course registration (DIFFERENT from verified student flow)
    'ENABLE_PAID_COURSE_REGISTRATION': False,

    # Enable the display of cosmetic course price display (set in course advanced settings)
    'ENABLE_COSMETIC_DISPLAY_PRICE': False,

    # Automatically approve student identity verification attempts
    'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': False,

    # Maximum number of rows to include in the csv file for downloading problem responses.
    'MAX_PROBLEM_RESPONSES_COUNT': 5000,

    'ENABLED_PAYMENT_REPORTS': [
        "refund_report",
        "itemized_purchase_report",
        "university_revenue_share",
        "certificate_status"
    ],

    # Turn off account locking if failed login attempts exceeds a limit
    'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': True,

    # Hide any Personally Identifiable Information from application logs
    'SQUELCH_PII_IN_LOGS': True,

    # Toggles the embargo functionality, which blocks users from
    # the site or courses based on their location.
    'EMBARGO': False,

    # Whether the Wiki subsystem should be accessible via the direct /wiki/ paths. Setting this to True means
    # that people can submit content and modify the Wiki in any arbitrary manner. We're leaving this as True in the
    # defaults, so that we maintain current behavior
    'ALLOW_WIKI_ROOT_ACCESS': True,

    # Turn on/off Microsites feature
    'USE_MICROSITES': False,

    # Turn on third-party auth. Disabled for now because full implementations are not yet available. Remember to run
    # migrations if you enable this; we don't create tables by default.
    'ENABLE_THIRD_PARTY_AUTH': False,

    # Toggle to enable alternate urls for marketing links
    'ENABLE_MKTG_SITE': False,

    # Prevent concurrent logins per user
    'PREVENT_CONCURRENT_LOGINS': True,

    # When a logged in user goes to the homepage ('/') should the user be
    # redirected to the dashboard - this is default Open edX behavior. Set to
    # False to not redirect the user
    'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': True,

    # When a user goes to the homepage ('/') the user sees the
    # courses listed in the announcement dates order - this is default Open edX behavior.
    # Set to True to change the course sorting behavior by their start dates, latest first.
    'ENABLE_COURSE_SORTING_BY_START_DATE': True,

    # Expose Mobile REST API. Note that if you use this, you must also set
    # ENABLE_OAUTH2_PROVIDER to True
    'ENABLE_MOBILE_REST_API': False,

    # Enable the combined login/registration form
    'ENABLE_COMBINED_LOGIN_REGISTRATION': False,
    'ENABLE_COMBINED_LOGIN_REGISTRATION_FOOTER': False,

    # Enable organizational email opt-in
    'ENABLE_MKTG_EMAIL_OPT_IN': False,

    # Show the mobile app links in the footer
    'ENABLE_FOOTER_MOBILE_APP_LINKS': False,

    # Let students save and manage their annotations
    'ENABLE_EDXNOTES': False,

    # Milestones application flag
    'MILESTONES_APP': False,

    # Organizations application flag
    'ORGANIZATIONS_APP': False,

    # Prerequisite courses feature flag
    'ENABLE_PREREQUISITE_COURSES': False,

    # For easily adding modes to courses during acceptance testing
    'MODE_CREATION_FOR_TESTING': False,

    # For caching programs in contexts where the LMS can only
    # be reached over HTTP.
    'EXPOSE_CACHE_PROGRAMS_ENDPOINT': False,

    # Courseware search feature
    'ENABLE_COURSEWARE_SEARCH': False,

    # Dashboard search feature
    'ENABLE_DASHBOARD_SEARCH': False,

    # log all information from cybersource callbacks
    'LOG_POSTPAY_CALLBACKS': True,

    # Toggle platform-wide course licensing
    'LICENSING': False,

    # Certificates Web/HTML Views
    'CERTIFICATES_HTML_VIEW': False,

    # Course discovery feature
    'ENABLE_COURSE_DISCOVERY': False,

    # Setting for overriding default filtering facets for Course discovery
    # COURSE_DISCOVERY_FILTERS = ["org", "language", "modes"]

    # Software secure fake page feature flag
    'ENABLE_SOFTWARE_SECURE_FAKE': False,

    # Teams feature
    'ENABLE_TEAMS': True,

    # Show video bumper in LMS
    'ENABLE_VIDEO_BUMPER': False,

    # How many seconds to show the bumper again, default is 7 days:
    'SHOW_BUMPER_PERIODICITY': 7 * 24 * 3600,

    # Special Exams, aka Timed and Proctored Exams
    'ENABLE_SPECIAL_EXAMS': False,

    # Enable OpenBadge support. See the BADGR_* settings later in this file.
    'ENABLE_OPENBADGES': False,

    # Enable LTI Provider feature.
    'ENABLE_LTI_PROVIDER': False,

    # Show the language selector in the header
    'SHOW_HEADER_LANGUAGE_SELECTOR': False,

    # At edX it's safe to assume that English transcripts are always available
    # This is not the case for all installations.
    # The default value in {lms,cms}/envs/common.py and xmodule/tests/test_video.py should be consistent.
    'FALLBACK_TO_ENGLISH_TRANSCRIPTS': True,

    # Show the language selector in the footer
    'SHOW_FOOTER_LANGUAGE_SELECTOR': False,

    # Write new CSM history to the extended table.
    # This will eventually default to True and may be
    # removed since all installs should have the separate
    # extended history table.
    'ENABLE_CSMH_EXTENDED': False,

    # Read from both the CSMH and CSMHE history tables.
    # This is the default, but can be disabled if all history
    # lives in the Extended table, saving the frontend from
    # making multiple queries.
    'ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES': True,

    # Set this to False to facilitate cleaning up invalid xml from your modulestore.
    'ENABLE_XBLOCK_XML_VALIDATION': True,

    # Allow public account creation
    'ALLOW_PUBLIC_ACCOUNT_CREATION': True,

    # Enable footer banner for cookie consent.
    # See https://cookieconsent.insites.com/ for more.
    'ENABLE_COOKIE_CONSENT': False,

    # Whether or not the dynamic EnrollmentTrackUserPartition should be registered.
    'ENABLE_ENROLLMENT_TRACK_USER_PARTITION': True,

    # Enable one click program purchase
    # See LEARNER-493
    'ENABLE_ONE_CLICK_PROGRAM_PURCHASE': False,

    # Allow users to change their email address.
    'ALLOW_EMAIL_ADDRESS_CHANGE': True,

    # Whether the bulk enrollment view is enabled.
    'ENABLE_BULK_ENROLLMENT_VIEW': False,

    # Whether course goals is enabled.
    'ENABLE_COURSE_GOALS': True,

    # Set to enable Enterprise integration
    'ENABLE_ENTERPRISE_INTEGRATION': False,

    # Whether HTML XBlocks/XModules return HTML content with the Course Blocks API student_view_data
    'ENABLE_HTML_XBLOCK_STUDENT_VIEW_DATA': False,

    # Whether to send an email for failed password reset attempts or not. This is mainly useful for notifying users
    # that they don't have an account associated with email addresses they believe they've registered with.
    'ENABLE_PASSWORD_RESET_FAILURE_EMAIL': False,

    # Sets the default browser support. For more information go to http://browser-update.org/customize.html
    'UNSUPPORTED_BROWSER_ALERT_VERSIONS': "{i:10,f:-3,o:-3,s:-3,c:-3}",

    # Set this to true to make API docs available at /api-docs/.
    'ENABLE_API_DOCS': False,

    # Whether to display the account deletion section the account settings page
    'ENABLE_ACCOUNT_DELETION': True,
}

# Settings for the course reviews tool template and identification key, set either to None to disable course reviews
COURSE_REVIEWS_TOOL_PROVIDER_FRAGMENT_NAME = 'coursetalk-reviews-fragment.html'
COURSE_REVIEWS_TOOL_PROVIDER_PLATFORM_KEY = 'edx'

# CDN links to CourseTalk scripts to load read and write widgets
COURSE_TALK_READ_ONLY_SOURCE = '//d3q6qq2zt8nhwv.cloudfront.net/s/js/widgets/coursetalk-read-reviews.js'
COURSE_TALK_WRITE_ONLY_SOURCE = '//d3q6qq2zt8nhwv.cloudfront.net/s/js/widgets/coursetalk-write-reviews.js'

# Ignore static asset files on import which match this pattern
ASSET_IGNORE_REGEX = r"(^\._.*$)|(^\.DS_Store$)|(^.*~$)"

# Used for A/B testing
DEFAULT_GROUPS = []

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

# Used with XQueue
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds
XQUEUE_INTERFACE = {
    'url': 'http://localhost:18040',
    'basic_auth': ['edx', 'edx'],
    'django_auth': {
        'username': 'lms',
        'password': 'password'
    }
}

# Used with Email sending
RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS = 5
RETRY_ACTIVATION_EMAIL_TIMEOUT = 0.5
PASSWORD_RESET_EMAIL_RATE_LIMIT = {
    'no_of_emails': 1,
    'per_seconds': 60
}
# Deadline message configurations
COURSE_MESSAGE_ALERT_DURATION_IN_DAYS = 14

############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /edx-platform/lms pylint: disable=no-value-for-parameter
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
OPENEDX_ROOT = REPO_ROOT / "openedx"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /edx-platform is in
COURSES_ROOT = ENV_ROOT / "data"
NODE_MODULES_ROOT = REPO_ROOT / "node_modules"

DATA_DIR = COURSES_ROOT

# TODO: Remove the rest of the sys.path modification here and in cms/envs/common.py
sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'djangoapps')

# For Node.js

system_node_path = os.environ.get("NODE_PATH", NODE_MODULES_ROOT)

node_paths = [
    COMMON_ROOT / "static/js/vendor",
    system_node_path,
]
NODE_PATH = ':'.join(node_paths)

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoLite2-Country.mmdb"
# Where to look for a status message
STATUS_MESSAGE_PATH = ENV_ROOT / "status_message.json"

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

############################ OpenID Provider  ##################################
OPENID_PROVIDER_TRUSTED_ROOTS = ['cs50.net', '*.cs50.net']

############################ OAUTH2 Provider ###################################

# OpenID Connect issuer ID. Normally the URL of the authentication endpoint.

OAUTH_OIDC_ISSUER = 'http://127.0.0.1:8000/oauth2'

# OpenID Connect claim handlers

OAUTH_OIDC_ID_TOKEN_HANDLERS = (
    'edx_oauth2_provider.oidc.handlers.BasicIDTokenHandler',
    'edx_oauth2_provider.oidc.handlers.ProfileHandler',
    'edx_oauth2_provider.oidc.handlers.EmailHandler',
    'oauth2_handler.IDTokenHandler'
)

OAUTH_OIDC_USERINFO_HANDLERS = (
    'edx_oauth2_provider.oidc.handlers.BasicUserInfoHandler',
    'edx_oauth2_provider.oidc.handlers.ProfileHandler',
    'edx_oauth2_provider.oidc.handlers.EmailHandler',
    'oauth2_handler.UserInfoHandler'
)

OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS = 365
OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS = 30

################################## DJANGO OAUTH TOOLKIT #######################################

# Scope description strings are presented to the user
# on the application authorization page. See
# lms/templates/oauth2_provider/authorize.html for details.
# Non-default scopes should be added directly to OAUTH2_PROVIDER['SCOPES'] below.
OAUTH2_DEFAULT_SCOPES = {
    'read': _('Read access'),
    'write': _('Write access'),
    'email': _('Know your email address'),
    'profile': _('Know your name and username'),
}

OAUTH2_PROVIDER = {
    'OAUTH2_VALIDATOR_CLASS': 'openedx.core.djangoapps.oauth_dispatch.dot_overrides.validators.EdxOAuth2Validator',
    # 3 months and then we expire refresh tokens using edx_clear_expired_tokens (length is mobile app driven)
    'REFRESH_TOKEN_EXPIRE_SECONDS': 7776000,
    'SCOPES_BACKEND_CLASS': 'openedx.core.djangoapps.oauth_dispatch.scopes.ApplicationModelScopes',
    'SCOPES': dict(OAUTH2_DEFAULT_SCOPES, **{
        'user_id': _('Retrieve your user identifier'),
        'grades:read': _('Retrieve your grades for your enrolled courses'),
        'certificates:read': _('Retrieve your course certificates'),
    }),
    'DEFAULT_SCOPES': OAUTH2_DEFAULT_SCOPES,
    'REQUEST_APPROVAL_PROMPT': 'auto_even_if_expired',
    'ERROR_RESPONSE_WITH_SCOPES': True,
}
# This is required for the migrations in oauth_dispatch.models
# otherwise it fails saying this attribute is not present in Settings
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

# Automatically clean up edx-django-oauth2-provider tokens on use
OAUTH_DELETE_EXPIRED = True
OAUTH_ID_TOKEN_EXPIRATION = 60 * 60
OAUTH_ENFORCE_SECURE = True
OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS = 365
OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS = 30

################################## THIRD_PARTY_AUTH CONFIGURATION #############################
TPA_PROVIDER_BURST_THROTTLE = '10/min'
TPA_PROVIDER_SUSTAINED_THROTTLE = '50/hr'

################################## TEMPLATE CONFIGURATION #####################################
# Mako templating
import tempfile  # pylint: disable=wrong-import-order
MAKO_MODULE_DIR = os.path.join(tempfile.gettempdir(), 'mako_lms')
MAKO_TEMPLATE_DIRS_BASE = [
    PROJECT_ROOT / 'templates',
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
    OPENEDX_ROOT / 'core' / 'djangoapps' / 'cors_csrf' / 'templates',
    OPENEDX_ROOT / 'core' / 'djangoapps' / 'dark_lang' / 'templates',
    OPENEDX_ROOT / 'core' / 'lib' / 'license' / 'templates',
    OPENEDX_ROOT / 'features' / 'course_experience' / 'templates',
]


def _make_mako_template_dirs(settings):
    """
    Derives the final Mako template directories list from other settings.
    """
    if settings.ENABLE_COMPREHENSIVE_THEMING:
        themes_dirs = get_theme_base_dirs_from_settings(settings.COMPREHENSIVE_THEME_DIRS)
        for theme in get_themes_unchecked(themes_dirs, settings.PROJECT_ROOT):
            if theme.themes_base_dir not in settings.MAKO_TEMPLATE_DIRS_BASE:
                settings.MAKO_TEMPLATE_DIRS_BASE.insert(0, theme.themes_base_dir)
    if settings.FEATURES.get('USE_MICROSITES', False) and getattr(settings, "MICROSITE_CONFIGURATION", False):
        settings.MAKO_TEMPLATE_DIRS_BASE.insert(0, settings.MICROSITE_ROOT_DIR)
    return settings.MAKO_TEMPLATE_DIRS_BASE


CONTEXT_PROCESSORS = [
    'django.template.context_processors.request',
    'django.template.context_processors.static',
    'django.template.context_processors.i18n',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.template.context_processors.csrf',

    # Added for django-wiki
    'django.template.context_processors.media',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'sekizai.context_processors.sekizai',

    # Hack to get required link URLs to password reset templates
    'edxmako.shortcuts.marketing_link_context_processor',

    # Shoppingcart processor (detects if request.user has a cart)
    'shoppingcart.context_processor.user_has_cart_context_processor',

    # Timezone processor (sends language and time_zone preference)
    'courseware.context_processor.user_timezone_locale_prefs',

    # Allows the open edX footer to be leveraged in Django Templates.
    'edxmako.shortcuts.footer_context_processor',

    # Online contextual help
    'help_tokens.context_processor',
    'openedx.core.djangoapps.site_configuration.context_processors.configuration_context',

    # Mobile App processor (Detects if request is from the mobile app)
    'mobile_api.context_processor.is_from_mobile_app'
]

# Django templating
TEMPLATES = [
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Don't look for template source files inside installed applications.
        'APP_DIRS': False,
        # Instead, look for template source files in these dirs.
        'DIRS': [
            PROJECT_ROOT / "templates",
            COMMON_ROOT / 'templates',
            COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
            COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
            COMMON_ROOT / 'static',  # required to statically include common Underscore templates
        ],
        # Options specific to this backend.
        'OPTIONS': {
            'loaders': [
                # We have to use mako-aware template loaders to be able to include
                # mako templates inside django templates (such as main_django.html).
                'openedx.core.djangoapps.theming.template_loaders.ThemeTemplateLoader',
                'edxmako.makoloader.MakoFilesystemLoader',
                'edxmako.makoloader.MakoAppDirectoriesLoader',
            ],
            'context_processors': CONTEXT_PROCESSORS,
            # Change 'debug' in your environment settings files - not here.
            'debug': False
        }
    },
    {
        'NAME': 'mako',
        'BACKEND': 'edxmako.backend.Mako',
        # Don't look for template source files inside installed applications.
        'APP_DIRS': False,
        # Instead, look for template source files in these dirs.
        'DIRS': _make_mako_template_dirs,
        # Options specific to this backend.
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
            # Change 'debug' in your environment settings files - not here.
            'debug': False,
        }
    },
]
derived_collection_entry('TEMPLATES', 1, 'DIRS')
DEFAULT_TEMPLATE_ENGINE = TEMPLATES[0]
DEFAULT_TEMPLATE_ENGINE_DIRS = DEFAULT_TEMPLATE_ENGINE['DIRS'][:]


def _add_microsite_dirs_to_default_template_engine(settings):
    """
    Derives the final DEFAULT_TEMPLATE_ENGINE['DIRS'] setting from other settings.
    """
    if settings.FEATURES.get('USE_MICROSITES', False) and getattr(settings, "MICROSITE_CONFIGURATION", False):
        DEFAULT_TEMPLATE_ENGINE_DIRS.append(settings.MICROSITE_ROOT_DIR)
    return DEFAULT_TEMPLATE_ENGINE_DIRS


DEFAULT_TEMPLATE_ENGINE['DIRS'] = _add_microsite_dirs_to_default_template_engine
derived_collection_entry('DEFAULT_TEMPLATE_ENGINE', 'DIRS')

###############################################################################################

AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'openedx.core.djangoapps.oauth_dispatch.dot_overrides.backends.EdxRateLimitedAllowAllUsersModelBackend',
    'bridgekeeper.backends.RulePermissionBackend',
]

STUDENT_FILEUPLOAD_MAX_SIZE = 4 * 1000 * 1000  # 4 MB
MAX_FILEUPLOADS_PER_INPUT = 20

# Set request limits for maximum size of a request body and maximum number of GET/POST parameters. (>=Django 1.10)
# Limits are currently disabled - but can be used for finer-grained denial-of-service protection.
DATA_UPLOAD_MAX_MEMORY_SIZE = None
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Configuration option for when we want to grab server error pages
STATIC_GRAB = False
DEV_CONTENT = True

# License for serving content in China
ICP_LICENSE = None
ICP_LICENSE_INFO = {}

ELASTIC_SEARCH_CONFIG = [
    {
        'use_ssl': False,
        'host': 'localhost',
        'port': 9200
    }
]

VIDEO_CDN_URL = {
    'EXAMPLE_COUNTRY_CODE': "http://example.com/edx/video?s3_url="
}

STATIC_ROOT_BASE = '/edx/var/edxapp/staticfiles'

LOGGING_ENV = 'sandbox'

EDX_ROOT_URL = ''

LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/login'
LOGIN_URL = EDX_ROOT_URL + '/login'

PARTNER_SUPPORT_EMAIL = ''

CERT_QUEUE = 'certificates'

ALTERNATE_WORKER_QUEUES = 'cms'

LOCAL_LOGLEVEL = "INFO"

LOG_DIR = '/edx/var/log/edx'

DATA_DIR = '/edx/app/edxapp'

MAINTENANCE_BANNER_TEXT = 'Sample banner message'

GIT_REPO_DIR = '/edx/var/edxapp/course_repos'

DJFS = {
    'type': 'osfs',
    'directory_root': '/edx/app/edxapp/django-pyfs/static/django-pyfs',
    'url_root': '/static/django-pyfs',
}

### Dark code. Should be enabled in local settings for devel.

ENABLE_MULTICOURSE = False  # set to False to disable multicourse display (see lib.util.views.edXhome)

WIKI_ENABLED = True

###

COURSE_MODE_DEFAULTS = {
    'bulk_sku': None,
    'currency': 'usd',
    'description': None,
    'expiration_datetime': None,
    'min_price': 0,
    'name': _('Audit'),
    'sku': None,
    'slug': 'audit',
    'suggested_prices': '',
}

# IP addresses that are allowed to reload the course, etc.
# TODO (vshnayder): Will probably need to change as we get real access control in.
LMS_MIGRATION_ALLOWED_IPS = []

USAGE_KEY_PATTERN = r'(?P<usage_key_string>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'
ASSET_KEY_PATTERN = r'(?P<asset_key_string>(?:/?c4x(:/)?/[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'
USAGE_ID_PATTERN = r'(?P<usage_id>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'


# The space is required for space-dependent languages like Arabic and Farsi.
# However, backward compatibility with Ficus older releases is still maintained (space is still not valid)
# in the AccountCreationForm and the user_api through the ENABLE_UNICODE_USERNAME feature flag.
USERNAME_REGEX_PARTIAL = r'[\w .@_+-]+'
USERNAME_PATTERN = r'(?P<username>{regex})'.format(regex=USERNAME_REGEX_PARTIAL)


############################## HEARTBEAT ######################################

# Checks run in normal mode by the heartbeat djangoapp
HEARTBEAT_CHECKS = [
    'openedx.core.djangoapps.heartbeat.default_checks.check_modulestore',
    'openedx.core.djangoapps.heartbeat.default_checks.check_database',
]

# Other checks to run by default in "extended"/heavy mode
HEARTBEAT_EXTENDED_CHECKS = (
    'openedx.core.djangoapps.heartbeat.default_checks.check_celery',
)

HEARTBEAT_CELERY_TIMEOUT = 5

############################## EVENT TRACKING #################################
LMS_SEGMENT_KEY = None

# FIXME: Should we be doing this truncation?
TRACK_MAX_EVENT = 50000

DEBUG_TRACK_LOG = False

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
TRACKING_IGNORE_URL_PATTERNS = [r'^/event', r'^/login', r'^/heartbeat', r'^/segmentio/event', r'^/performance']

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

# Backwards compatibility with ENABLE_SQL_TRACKING_LOGS feature flag.
# In the future, adding the backend to TRACKING_BACKENDS should be enough.
if FEATURES.get('ENABLE_SQL_TRACKING_LOGS'):
    TRACKING_BACKENDS.update({
        'sql': {
            'ENGINE': 'track.backends.django.DjangoBackend'
        }
    })
    EVENT_TRACKING_BACKENDS.update({
        'sql': {
            'ENGINE': 'track.backends.django.DjangoBackend'
        }
    })

TRACKING_SEGMENTIO_WEBHOOK_SECRET = None
TRACKING_SEGMENTIO_ALLOWED_TYPES = ['track']
TRACKING_SEGMENTIO_DISALLOWED_SUBSTRING_NAMES = []
TRACKING_SEGMENTIO_SOURCE_MAP = {
    'analytics-android': 'mobile',
    'analytics-ios': 'mobile',
}

######################## GOOGLE ANALYTICS ###########################
GOOGLE_ANALYTICS_ACCOUNT = None
GOOGLE_SITE_VERIFICATION_ID = ''
GOOGLE_ANALYTICS_LINKEDIN = 'GOOGLE_ANALYTICS_LINKEDIN_DUMMY'

######################## BRANCH.IO ###########################
BRANCH_IO_KEY = ''

######################## OPTIMIZELY ###########################
OPTIMIZELY_PROJECT_ID = None

######################## subdomain specific settings ###########################
COURSE_LISTINGS = {}

############# XBlock Configuration ##########

# Import after sys.path fixup
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore import prefer_xmodules
from xmodule.x_module import XModuleMixin

# These are the Mixins that should be added to every XBlock.
# This should be moved into an XBlock Runtime/Application object
# once the responsibility of XBlock creation is moved out of modulestore - cpennington
XBLOCK_MIXINS = (LmsBlockMixin, InheritanceMixin, XModuleMixin, EditInfoMixin)

# Allow any XBlock in the LMS
XBLOCK_SELECT_FUNCTION = prefer_xmodules

# Paths to wrapper methods which should be applied to every XBlock's FieldData.
XBLOCK_FIELD_DATA_WRAPPERS = ()

XBLOCK_FS_STORAGE_BUCKET = None
XBLOCK_FS_STORAGE_PREFIX = None
XBLOCK_SETTINGS = {}

############# ModuleStore Configuration ##########

MODULESTORE_BRANCH = 'published-only'

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

############################### DJANGO BUILT-INS ###############################
# Change DEBUG in your environment settings files, not here
DEBUG = False
USE_TZ = True
SESSION_COOKIE_SECURE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_COOKIE_DOMAIN = ""
SESSION_COOKIE_NAME = 'sessionid'

# CMS base
CMS_BASE = 'localhost:18010'

# LMS base
LMS_BASE = 'localhost:18000'

# Studio name
STUDIO_NAME = 'Studio'
STUDIO_SHORT_NAME = 'Studio'

# Site info
SITE_NAME = "localhost"
HTTPS = 'on'
ROOT_URLCONF = 'lms.urls'
# NOTE: Please set ALLOWED_HOSTS to some sane value, as we do not allow the default '*'

# Platform Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'registration@example.com'
DEFAULT_FEEDBACK_EMAIL = 'feedback@example.com'
SERVER_EMAIL = 'devops@example.com'
TECH_SUPPORT_EMAIL = 'technical@example.com'
CONTACT_EMAIL = 'info@example.com'
BUGS_EMAIL = 'bugs@example.com'
UNIVERSITY_EMAIL = 'university@example.com'
PRESS_EMAIL = 'press@example.com'
FINANCE_EMAIL = ''

# Platform mailing address
CONTACT_MAILING_ADDRESS = 'SET-ME-PLEASE'

# Account activation email sender address
ACTIVATION_EMAIL_FROM_ADDRESS = ''

ADMINS = ()
MANAGERS = ADMINS

# Static content
STATIC_URL = '/static/'
STATIC_ROOT = ENV_ROOT / "staticfiles"
STATIC_URL_BASE = '/static/'

STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
    NODE_MODULES_ROOT / "@edx",
]

FAVICON_PATH = 'images/favicon.ico'
DEFAULT_COURSE_ABOUT_IMAGE_URL = 'images/pencils.jpg'

CAS_SERVER_URL = ""
CAS_EXTRA_LOGIN_PARAMS = ""
CAS_ATTRIBUTE_CALLBACK = ""

# User-uploaded content
MEDIA_ROOT = '/edx/var/edxapp/media/'
MEDIA_URL = '/media/'

# Locale/Internationalization
CELERY_TIMEZONE = 'UTC'
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html
# these languages display right to left
LANGUAGES_BIDI = ("he", "ar", "fa", "ur", "fa-ir", "rtl")

LANGUAGE_COOKIE = "openedx-language-preference"

# Sourced from http://www.localeplanet.com/icu/ and wikipedia
LANGUAGES = [
    ('en', u'English'),
    ('rtl', u'Right-to-Left Test Language'),
    ('eo', u'Dummy Language (Esperanto)'),  # Dummy languaged used for testing
    ('fake2', u'Fake translations'),        # Another dummy language for testing (not pushed to prod)

    ('am', u'አማርኛ'),  # Amharic
    ('ar', u'العربية'),  # Arabic
    ('az', u'azərbaycanca'),  # Azerbaijani
    ('bg-bg', u'български (България)'),  # Bulgarian (Bulgaria)
    ('bn-bd', u'বাংলা (বাংলাদেশ)'),  # Bengali (Bangladesh)
    ('bn-in', u'বাংলা (ভারত)'),  # Bengali (India)
    ('bs', u'bosanski'),  # Bosnian
    ('ca', u'Català'),  # Catalan
    ('ca@valencia', u'Català (València)'),  # Catalan (Valencia)
    ('cs', u'Čeština'),  # Czech
    ('cy', u'Cymraeg'),  # Welsh
    ('da', u'dansk'),  # Danish
    ('de-de', u'Deutsch (Deutschland)'),  # German (Germany)
    ('el', u'Ελληνικά'),  # Greek
    ('en-uk', u'English (United Kingdom)'),  # English (United Kingdom)
    ('en@lolcat', u'LOLCAT English'),  # LOLCAT English
    ('en@pirate', u'Pirate English'),  # Pirate English
    ('es-419', u'Español (Latinoamérica)'),  # Spanish (Latin America)
    ('es-ar', u'Español (Argentina)'),  # Spanish (Argentina)
    ('es-ec', u'Español (Ecuador)'),  # Spanish (Ecuador)
    ('es-es', u'Español (España)'),  # Spanish (Spain)
    ('es-mx', u'Español (México)'),  # Spanish (Mexico)
    ('es-pe', u'Español (Perú)'),  # Spanish (Peru)
    ('et-ee', u'Eesti (Eesti)'),  # Estonian (Estonia)
    ('eu-es', u'euskara (Espainia)'),  # Basque (Spain)
    ('fa', u'فارسی'),  # Persian
    ('fa-ir', u'فارسی (ایران)'),  # Persian (Iran)
    ('fi-fi', u'Suomi (Suomi)'),  # Finnish (Finland)
    ('fil', u'Filipino'),  # Filipino
    ('fr', u'Français'),  # French
    ('gl', u'Galego'),  # Galician
    ('gu', u'ગુજરાતી'),  # Gujarati
    ('he', u'עברית'),  # Hebrew
    ('hi', u'हिन्दी'),  # Hindi
    ('hr', u'hrvatski'),  # Croatian
    ('hu', u'magyar'),  # Hungarian
    ('hy-am', u'Հայերեն (Հայաստան)'),  # Armenian (Armenia)
    ('id', u'Bahasa Indonesia'),  # Indonesian
    ('it-it', u'Italiano (Italia)'),  # Italian (Italy)
    ('ja-jp', u'日本語 (日本)'),  # Japanese (Japan)
    ('kk-kz', u'қазақ тілі (Қазақстан)'),  # Kazakh (Kazakhstan)
    ('km-kh', u'ភាសាខ្មែរ (កម្ពុជា)'),  # Khmer (Cambodia)
    ('kn', u'ಕನ್ನಡ'),  # Kannada
    ('ko-kr', u'한국어 (대한민국)'),  # Korean (Korea)
    ('lt-lt', u'Lietuvių (Lietuva)'),  # Lithuanian (Lithuania)
    ('ml', u'മലയാളം'),  # Malayalam
    ('mn', u'Монгол хэл'),  # Mongolian
    ('mr', u'मराठी'),  # Marathi
    ('ms', u'Bahasa Melayu'),  # Malay
    ('nb', u'Norsk bokmål'),  # Norwegian Bokmål
    ('ne', u'नेपाली'),  # Nepali
    ('nl-nl', u'Nederlands (Nederland)'),  # Dutch (Netherlands)
    ('or', u'ଓଡ଼ିଆ'),  # Oriya
    ('pl', u'Polski'),  # Polish
    ('pt-br', u'Português (Brasil)'),  # Portuguese (Brazil)
    ('pt-pt', u'Português (Portugal)'),  # Portuguese (Portugal)
    ('ro', u'română'),  # Romanian
    ('ru', u'Русский'),  # Russian
    ('si', u'සිංහල'),  # Sinhala
    ('sk', u'Slovenčina'),  # Slovak
    ('sl', u'Slovenščina'),  # Slovenian
    ('sq', u'shqip'),  # Albanian
    ('sr', u'Српски'),  # Serbian
    ('sv', u'svenska'),  # Swedish
    ('sw', u'Kiswahili'),  # Swahili
    ('ta', u'தமிழ்'),  # Tamil
    ('te', u'తెలుగు'),  # Telugu
    ('th', u'ไทย'),  # Thai
    ('tr-tr', u'Türkçe (Türkiye)'),  # Turkish (Turkey)
    ('uk', u'Українська'),  # Ukranian
    ('ur', u'اردو'),  # Urdu
    ('vi', u'Tiếng Việt'),  # Vietnamese
    ('uz', u'Ўзбек'),  # Uzbek
    ('zh-cn', u'中文 (简体)'),  # Chinese (China)
    ('zh-hk', u'中文 (香港)'),  # Chinese (Hong Kong)
    ('zh-tw', u'中文 (台灣)'),  # Chinese (Taiwan)
]

LANGUAGE_DICT = dict(LANGUAGES)

# Languages supported for custom course certificate templates
CERTIFICATE_TEMPLATE_LANGUAGES = {
    'en': 'English',
    'es': 'Español',
}

USE_I18N = True
USE_L10N = True

STATICI18N_ROOT = PROJECT_ROOT / "static"
STATICI18N_OUTPUT_DIR = "js/i18n"


# Localization strings (e.g. django.po) are under these directories
def _make_locale_paths(settings):  # pylint: disable=missing-docstring
    locale_paths = [settings.REPO_ROOT + '/conf/locale']  # edx-platform/conf/locale/
    if settings.ENABLE_COMPREHENSIVE_THEMING:
        # Add locale paths to settings for comprehensive theming.
        for locale_path in settings.COMPREHENSIVE_THEME_LOCALE_PATHS:
            locale_paths += (path(locale_path), )
    return locale_paths
LOCALE_PATHS = _make_locale_paths
derived('LOCALE_PATHS')

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Guidelines for translators
TRANSLATORS_GUIDE = 'https://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/internationalization/i18n_translators_guide.html'  # pylint: disable=line-too-long

#################################### AWS #######################################
# S3BotoStorage insists on a timeout for uploaded assets. We should make it
# permanent instead, but rather than trying to figure out exactly where that
# setting is, I'm just bumping the expiration time to something absurd (100
# years). This is only used if DEFAULT_FILE_STORAGE is overriden to use S3
# in the global settings.py
AWS_QUERYSTRING_EXPIRE = 10 * 365 * 24 * 60 * 60  # 10 years
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'

################################# SIMPLEWIKI ###################################
SIMPLE_WIKI_REQUIRE_LOGIN_EDIT = True
SIMPLE_WIKI_REQUIRE_LOGIN_VIEW = False

################################# WIKI ###################################
from course_wiki import settings as course_wiki_settings

WIKI_ACCOUNT_HANDLING = False
WIKI_EDITOR = 'course_wiki.editors.CodeMirror'
WIKI_SHOW_MAX_CHILDREN = 0  # We don't use the little menu that shows children of an article in the breadcrumb
WIKI_ANONYMOUS = False  # Don't allow anonymous access until the styling is figured out

WIKI_CAN_DELETE = course_wiki_settings.CAN_DELETE
WIKI_CAN_MODERATE = course_wiki_settings.CAN_MODERATE
WIKI_CAN_CHANGE_PERMISSIONS = course_wiki_settings.CAN_CHANGE_PERMISSIONS
WIKI_CAN_ASSIGN = course_wiki_settings.CAN_ASSIGN

WIKI_USE_BOOTSTRAP_SELECT_WIDGET = False
WIKI_LINK_LIVE_LOOKUPS = False
WIKI_LINK_DEFAULT_LEVEL = 2

##### Feedback submission mechanism #####
FEEDBACK_SUBMISSION_EMAIL = None

##### Zendesk #####
ZENDESK_URL = ''
ZENDESK_USER = ''
ZENDESK_API_KEY = ''
ZENDESK_CUSTOM_FIELDS = {}
ZENDESK_OAUTH_ACCESS_TOKEN = ''

##### EMBARGO #####
EMBARGO_SITE_REDIRECT_URL = None

##### shoppingcart Payment #####
PAYMENT_SUPPORT_EMAIL = 'billing@example.com'

##### Using cybersource by default #####

CC_PROCESSOR_NAME = 'CyberSource2'
CC_PROCESSOR = {
    'CyberSource2': {
        "PURCHASE_ENDPOINT": '',
        "SECRET_KEY": '',
        "ACCESS_KEY": '',
        "PROFILE_ID": '',
    }
}

# Setting for PAID_COURSE_REGISTRATION, DOES NOT AFFECT VERIFIED STUDENTS
PAID_COURSE_REGISTRATION_CURRENCY = ['usd', '$']

# Members of this group are allowed to generate payment reports
PAYMENT_REPORT_GENERATOR_GROUP = 'shoppingcart_report_access'

################################# EdxNotes config  #########################

# Configure the LMS to use our stub EdxNotes implementation
EDXNOTES_PUBLIC_API = 'http://localhost:8120/api/v1'
EDXNOTES_INTERNAL_API = 'http://localhost:8120/api/v1'

EDXNOTES_CONNECT_TIMEOUT = 0.5  # time in seconds
EDXNOTES_READ_TIMEOUT = 1.5  # time in seconds

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = 13

######################### Branded Footer ###################################
# Constants for the footer used on the site and shared with other sites
# (such as marketing and the blog) via the branding API.

# URL for OpenEdX displayed in the footer
FOOTER_OPENEDX_URL = "http://open.edx.org"

# URL for the OpenEdX logo image
# We use logo images served from files.edx.org so we can (roughly) track
# how many OpenEdX installations are running.
# Site operators can choose from these logo options:
# * https://files.edx.org/openedx-logos/edx-openedx-logo-tag.png
# * https://files.edx.org/openedx-logos/edx-openedx-logo-tag-light.png"
# * https://files.edx.org/openedx-logos/edx-openedx-logo-tag-dark.png
FOOTER_OPENEDX_LOGO_IMAGE = "https://files.edx.org/openedx-logos/edx-openedx-logo-tag.png"

# This is just a placeholder image.
# Site operators can customize this with their organization's image.
FOOTER_ORGANIZATION_IMAGE = "images/logo.png"

# These are referred to both by the Django asset pipeline
# AND by the branding footer API, which needs to decide which
# version of the CSS to serve.
FOOTER_CSS = {
    "openedx": {
        "ltr": "style-lms-footer",
        "rtl": "style-lms-footer-rtl",
    },
    "edx": {
        "ltr": "style-lms-footer-edx",
        "rtl": "style-lms-footer-edx-rtl",
    },
}

# Cache expiration for the version of the footer served
# by the branding API.
FOOTER_CACHE_TIMEOUT = 30 * 60

# Max age cache control header for the footer (controls browser caching).
FOOTER_BROWSER_CACHE_MAX_AGE = 5 * 60

# Credit api notification cache timeout
CREDIT_NOTIFICATION_CACHE_TIMEOUT = 5 * 60 * 60

################################# Middleware ###################################

MIDDLEWARE_CLASSES = [
    'openedx.core.lib.x_forwarded_for.middleware.XForwardedForMiddleware',

    'crum.CurrentRequestUserMiddleware',

    # A newer and safer request cache.
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'edx_django_utils.monitoring.middleware.MonitoringCustomMetricsMiddleware',

    # Cookie monitoring
    'openedx.core.lib.request_utils.CookieMetricsMiddleware',

    'mobile_api.middleware.AppVersionUpgrade',
    'openedx.core.djangoapps.header_control.middleware.HeaderControlMiddleware',
    'microsite_configuration.middleware.MicrositeMiddleware',
    'lms.djangoapps.discussion.django_comment_client.middleware.AjaxExceptionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',

    # Allows us to define redirects via Django admin
    'django_sites_extensions.middleware.RedirectMiddleware',

    # Instead of SessionMiddleware, we use a more secure version
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware',

    # Instead of AuthenticationMiddleware, we use a cached backed version
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'openedx.core.djangoapps.cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'student.middleware.UserStandingMiddleware',
    'openedx.core.djangoapps.contentserver.middleware.StaticContentServer',

    # Adds user tags to tracking events
    # Must go before TrackMiddleware, to get the context set up
    'openedx.core.djangoapps.user_api.middleware.UserTagsEventContextMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',

    # CORS and CSRF
    'corsheaders.middleware.CorsMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CorsCSRFMiddleware',
    'openedx.core.djangoapps.cors_csrf.middleware.CsrfCrossDomainCookieMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'splash.middleware.SplashMiddleware',

    'openedx.core.djangoapps.geoinfo.middleware.CountryMiddleware',
    'openedx.core.djangoapps.embargo.middleware.EmbargoMiddleware',

    # Allows us to set user preferences
    'openedx.core.djangoapps.lang_pref.middleware.LanguagePreferenceMiddleware',

    # Allows us to dark-launch particular languages.
    # Must be after LangPrefMiddleware, so ?preview-lang query params can override
    # user's language preference. ?clear-lang resets to user's language preference.
    'openedx.core.djangoapps.dark_lang.middleware.DarkLangMiddleware',

    # Detects user-requested locale from 'accept-language' header in http request.
    # Must be after DarkLangMiddleware.
    'django.middleware.locale.LocaleMiddleware',

    'lms.djangoapps.discussion.django_comment_client.utils.ViewNameMiddleware',
    'codejail.django_integration.ConfigureCodeJailMiddleware',

    # catches any uncaught RateLimitExceptions and returns a 403 instead of a 500
    'ratelimitbackend.middleware.RateLimitMiddleware',

    # for expiring inactive sessions
    'openedx.core.djangoapps.session_inactivity_timeout.middleware.SessionInactivityTimeout',

    # use Django built in clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # to redirected unenrolled students to the course info page
    'courseware.middleware.CacheCourseIdMiddleware',
    'courseware.middleware.RedirectMiddleware',

    'course_wiki.middleware.WikiAccessMiddleware',

    'openedx.core.djangoapps.theming.middleware.CurrentSiteThemeMiddleware',

    'waffle.middleware.WaffleMiddleware',

    # Inserts Enterprise content.
    'openedx.features.enterprise_support.middleware.EnterpriseMiddleware',

    # Enables force_django_cache_miss functionality for TieredCache.
    'edx_django_utils.cache.middleware.TieredCacheMiddleware',

    # Outputs monitoring metrics for a request.
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',

    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',

    # Handles automatically storing user ids in django-simple-history tables when possible.
    'simple_history.middleware.HistoryRequestMiddleware',

    # This must be last
    'openedx.core.djangoapps.site_configuration.middleware.SessionCookieDomainOverrideMiddleware',
]

# Clickjacking protection can be disbaled by setting this to 'ALLOW'
X_FRAME_OPTIONS = 'DENY'

# Platform for Privacy Preferences header
P3P_HEADER = 'CP="Open EdX does not have a P3P policy."'

############################### PIPELINE #######################################

PIPELINE = {
    'PIPELINE_ENABLED': True,
    'CSS_COMPRESSOR': None,
    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    # Don't wrap JavaScript as there is code that depends upon updating the global namespace
    'DISABLE_WRAPPER': True,
    # Specify the UglifyJS binary to use
    'UGLIFYJS_BINARY': 'node_modules/.bin/uglifyjs',
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

courseware_js = [
    'js/ajax-error.js',
    'js/courseware.js',
    'js/histogram.js',
    'js/navigation.js',
    'js/modules/tab.js',
]


# Before a student accesses courseware, we do not
# need many of the JS dependencies.  This includes
# only the dependencies used everywhere in the LMS
# (including the dashboard/account/profile pages)
# Currently, this partially duplicates the "main vendor"
# JavaScript file, so only one of the two should be included
# on a page at any time.
# In the future, we will likely refactor this to use
# RequireJS and an optimizer.
base_vendor_js = [
    'common/js/vendor/jquery.js',
    'common/js/vendor/jquery-migrate.js',
    'js/vendor/jquery.cookie.js',
    'js/vendor/url.min.js',
    'common/js/vendor/underscore.js',
    'common/js/vendor/underscore.string.js',
    'common/js/vendor/picturefill.js',

    # Make some edX UI Toolkit utilities available in the global "edx" namespace
    'edx-ui-toolkit/js/utils/global-loader.js',
    'edx-ui-toolkit/js/utils/string-utils.js',
    'edx-ui-toolkit/js/utils/html-utils.js',

    # Finally load RequireJS and dependent vendor libraries
    'common/js/vendor/require.js',
    'js/RequireJS-namespace-undefine.js',
    'js/vendor/URI.min.js',
    'common/js/vendor/backbone.js'
]

main_vendor_js = base_vendor_js + [
    'js/vendor/json2.js',
    'js/vendor/jquery-ui.min.js',
    'js/vendor/jquery.qtip.min.js',
    'js/vendor/jquery.ba-bbq.min.js',
]

# Common files used by both RequireJS code and non-RequireJS code
base_application_js = [
    'js/src/utility.js',
    'js/src/logger.js',
    'js/user_dropdown_v1.js',  # Custom dropdown keyboard handling for legacy pages
    'js/dialog_tab_controls.js',
    'js/src/string_utils.js',
    'js/form.ext.js',
    'js/src/ie_shim.js',
    'js/src/accessibility_tools.js',
    'js/toggle_login_modal.js',
    'js/src/lang_edx.js',
]

dashboard_js = (
    sorted(rooted_glob(PROJECT_ROOT / 'static', 'js/dashboard/**/*.js'))
)
discussion_js = (
    rooted_glob(PROJECT_ROOT / 'static', 'js/customwmd.js') +
    rooted_glob(PROJECT_ROOT / 'static', 'js/mathjax_accessible.js') +
    rooted_glob(PROJECT_ROOT / 'static', 'js/mathjax_delay_renderer.js') +
    sorted(rooted_glob(COMMON_ROOT / 'static', 'common/js/discussion/**/*.js'))
)

discussion_vendor_js = [
    'js/Markdown.Converter.js',
    'js/Markdown.Sanitizer.js',
    'js/Markdown.Editor.js',
    'js/vendor/jquery.timeago.js',
    'js/src/jquery.timeago.locale.js',
    'js/vendor/jquery.truncate.js',
    'js/jquery.ajaxfileupload.js',
    'js/split.js'
]

notes_js = ['js/notes.js']
instructor_dash_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'js/instructor_dashboard/**/*.js'))

verify_student_js = [
    'js/sticky_filter.js',
    'js/query-params.js',
    'js/verify_student/models/verification_model.js',
    'js/verify_student/views/error_view.js',
    'js/verify_student/views/image_input_view.js',
    'js/verify_student/views/webcam_photo_view.js',
    'js/verify_student/views/step_view.js',
    'js/verify_student/views/intro_step_view.js',
    'js/verify_student/views/make_payment_step_view.js',
    'js/verify_student/views/payment_confirmation_step_view.js',
    'js/verify_student/views/face_photo_step_view.js',
    'js/verify_student/views/id_photo_step_view.js',
    'js/verify_student/views/review_photos_step_view.js',
    'js/verify_student/views/enrollment_confirmation_step_view.js',
    'js/verify_student/views/pay_and_verify_view.js',
    'js/verify_student/pay_and_verify.js',
]

reverify_js = [
    'js/verify_student/views/error_view.js',
    'js/verify_student/views/image_input_view.js',
    'js/verify_student/views/webcam_photo_view.js',
    'js/verify_student/views/step_view.js',
    'js/verify_student/views/face_photo_step_view.js',
    'js/verify_student/views/id_photo_step_view.js',
    'js/verify_student/views/review_photos_step_view.js',
    'js/verify_student/views/reverify_success_step_view.js',
    'js/verify_student/models/verification_model.js',
    'js/verify_student/views/reverify_view.js',
    'js/verify_student/reverify.js',
]

incourse_reverify_js = [
    'js/verify_student/views/error_view.js',
    'js/verify_student/views/image_input_view.js',
    'js/verify_student/views/webcam_photo_view.js',
    'js/verify_student/models/verification_model.js',
    'js/verify_student/views/incourse_reverify_view.js',
    'js/verify_student/incourse_reverify.js',
]

ccx_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'js/ccx/**/*.js'))

certificates_web_view_js = [
    'common/js/vendor/jquery.js',
    'common/js/vendor/jquery-migrate.js',
    'js/vendor/jquery.cookie.js',
    'js/src/logger.js',
    'js/utils/facebook.js',
]

credit_web_view_js = [
    'common/js/vendor/jquery.js',
    'common/js/vendor/jquery-migrate.js',
    'js/vendor/jquery.cookie.js',
    'js/src/logger.js',
]

PIPELINE['STYLESHEETS'] = {
    'style-vendor': {
        'source_filenames': [
            'css/vendor/font-awesome.css',
            'css/vendor/jquery.qtip.min.css',
        ],
        'output_filename': 'css/lms-style-vendor.css',
    },
    'style-vendor-tinymce-content': {
        'source_filenames': [
            'js/vendor/tinymce/js/tinymce/skins/studio-tmce4/content.min.css'
        ],
        'output_filename': 'css/lms-style-vendor-tinymce-content.css',
    },
    'style-vendor-tinymce-skin': {
        'source_filenames': [
            'js/vendor/tinymce/js/tinymce/skins/studio-tmce4/skin.min.css'
        ],
        'output_filename': 'css/lms-style-vendor-tinymce-skin.css',
    },
    'style-main-v1': {
        'source_filenames': [
            'css/lms-main-v1.css',
        ],
        'output_filename': 'css/lms-main-v1.css',
    },
    'style-main-v1-rtl': {
        'source_filenames': [
            'css/lms-main-v1-rtl.css',
        ],
        'output_filename': 'css/lms-main-v1-rtl.css',
    },
    'style-main-v2': {
        'source_filenames': [
            'css/lms-main-v2.css',
        ],
        'output_filename': 'css/lms-main-v2.css',
    },
    'style-main-v2-rtl': {
        'source_filenames': [
            'css/lms-main-v2-rtl.css',
        ],
        'output_filename': 'css/lms-main-v2-rtl.css',
    },
    'style-course-vendor': {
        'source_filenames': [
            'js/vendor/CodeMirror/codemirror.css',
            'css/vendor/jquery.treeview.css',
            'css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css',
        ],
        'output_filename': 'css/lms-style-course-vendor.css',
    },
    'style-course': {
        'source_filenames': [
            'css/lms-course.css',
        ],
        'output_filename': 'css/lms-course.css',
    },
    'style-course-rtl': {
        'source_filenames': [
            'css/lms-course-rtl.css',
        ],
        'output_filename': 'css/lms-course-rtl.css',
    },
    'style-student-notes': {
        'source_filenames': [
            'css/vendor/edxnotes/annotator.min.css',
        ],
        'output_filename': 'css/lms-style-student-notes.css',
    },
    'style-discussion-main': {
        'source_filenames': [
            'css/discussion/lms-discussion-main.css',
        ],
        'output_filename': 'css/discussion/lms-discussion-main.css',
    },
    'style-discussion-main-rtl': {
        'source_filenames': [
            'css/discussion/lms-discussion-main-rtl.css',
        ],
        'output_filename': 'css/discussion/lms-discussion-main-rtl.css',
    },
    'style-inline-discussion': {
        'source_filenames': [
            'css/discussion/inline-discussion.css',
        ],
        'output_filename': 'css/discussion/inline-discussion.css',
    },
    'style-inline-discussion-rtl': {
        'source_filenames': [
            'css/discussion/inline-discussion-rtl.css',
        ],
        'output_filename': 'css/discussion/inline-discussion-rtl.css',
    },
    FOOTER_CSS['openedx']['ltr']: {
        'source_filenames': [
            'css/lms-footer.css',
        ],
        'output_filename': 'css/lms-footer.css',
    },
    FOOTER_CSS['openedx']['rtl']: {
        'source_filenames': [
            'css/lms-footer-rtl.css',
        ],
        'output_filename': 'css/lms-footer-rtl.css'
    },
    FOOTER_CSS['edx']['ltr']: {
        'source_filenames': [
            'css/lms-footer-edx.css',
        ],
        'output_filename': 'css/lms-footer-edx.css'
    },
    FOOTER_CSS['edx']['rtl']: {
        'source_filenames': [
            'css/lms-footer-edx-rtl.css',
        ],
        'output_filename': 'css/lms-footer-edx-rtl.css'
    },
    'style-certificates': {
        'source_filenames': [
            'certificates/css/main-ltr.css',
            'css/vendor/font-awesome.css',
        ],
        'output_filename': 'css/certificates-style.css'
    },
    'style-certificates-rtl': {
        'source_filenames': [
            'certificates/css/main-rtl.css',
            'css/vendor/font-awesome.css',
        ],
        'output_filename': 'css/certificates-style-rtl.css'
    },
    'style-learner-dashboard': {
        'source_filenames': [
            'css/lms-learner-dashboard.css',
        ],
        'output_filename': 'css/lms-learner-dashboard.css',
    },
    'style-learner-dashboard-rtl': {
        'source_filenames': [
            'css/lms-learner-dashboard-rtl.css',
        ],
        'output_filename': 'css/lms-learner-dashboard-rtl.css',
    },
    'style-mobile': {
        'source_filenames': [
            'css/lms-mobile.css',
        ],
        'output_filename': 'css/lms-mobile.css',
    },
    'style-mobile-rtl': {
        'source_filenames': [
            'css/lms-mobile-rtl.css',
        ],
        'output_filename': 'css/lms-mobile-rtl.css',
    },
}

common_js = [
    'js/src/ajax_prefix.js',
    'js/src/jquery.immediateDescendents.js',
    'js/src/xproblem.js',
]
xblock_runtime_js = [
    'common/js/xblock/core.js',
    'common/js/xblock/runtime.v1.js',
    'lms/js/xblock/lms.runtime.v1.js',
]
lms_application_js = [
    'js/calculator.js',
    'js/feedback_form.js',
    'js/main.js',
]

PIPELINE['JAVASCRIPT'] = {
    'base_application': {
        'source_filenames': base_application_js,
        'output_filename': 'js/lms-base-application.js',
    },
    'application': {
        'source_filenames': (
            common_js + xblock_runtime_js + base_application_js + lms_application_js +
            [
                'js/sticky_filter.js',
                'js/query-params.js',
                'common/js/vendor/moment-with-locales.js',
                'common/js/vendor/moment-timezone-with-data.js',
            ]
        ),
        'output_filename': 'js/lms-application.js',
    },
    'courseware': {
        'source_filenames': courseware_js,
        'output_filename': 'js/lms-courseware.js',
    },
    'base_vendor': {
        'source_filenames': base_vendor_js,
        'output_filename': 'js/lms-base-vendor.js',
    },
    'main_vendor': {
        'source_filenames': main_vendor_js,
        'output_filename': 'js/lms-main_vendor.js',
    },
    'module-descriptor-js': {
        'source_filenames': rooted_glob(COMMON_ROOT / 'static/', 'xmodule/descriptors/js/*.js'),
        'output_filename': 'js/lms-module-descriptors.js',
    },
    'module-js': {
        'source_filenames': rooted_glob(COMMON_ROOT / 'static', 'xmodule/modules/js/*.js'),
        'output_filename': 'js/lms-modules.js',
    },
    'discussion': {
        'source_filenames': discussion_js,
        'output_filename': 'js/discussion.js',
    },
    'discussion_vendor': {
        'source_filenames': discussion_vendor_js,
        'output_filename': 'js/discussion_vendor.js',
    },
    'notes': {
        'source_filenames': notes_js,
        'output_filename': 'js/notes.js',
    },
    'instructor_dash': {
        'source_filenames': instructor_dash_js,
        'output_filename': 'js/instructor_dash.js',
    },
    'dashboard': {
        'source_filenames': dashboard_js,
        'output_filename': 'js/dashboard.js'
    },
    'verify_student': {
        'source_filenames': verify_student_js,
        'output_filename': 'js/verify_student.js'
    },
    'reverify': {
        'source_filenames': reverify_js,
        'output_filename': 'js/reverify.js'
    },
    'incourse_reverify': {
        'source_filenames': incourse_reverify_js,
        'output_filename': 'js/incourse_reverify.js'
    },
    'ccx': {
        'source_filenames': ccx_js,
        'output_filename': 'js/ccx.js'
    },
    'footer_edx': {
        'source_filenames': ['js/footer-edx.js'],
        'output_filename': 'js/footer-edx.js'
    },
    'certificates_wv': {
        'source_filenames': certificates_web_view_js,
        'output_filename': 'js/certificates/web_view.js'
    },
    'credit_wv': {
        'source_filenames': credit_web_view_js,
        'output_filename': 'js/credit/web_view.js'
    }
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
)


################################# DJANGO-REQUIRE ###############################

# The baseUrl to pass to the r.js optimizer, relative to STATIC_ROOT.
REQUIRE_BASE_URL = "./"

# The name of a build profile to use for your project, relative to REQUIRE_BASE_URL.
# A sensible value would be 'app.build.js'. Leave blank to use the built-in default build profile.
# Set to False to disable running the default profile (e.g. if only using it to build Standalone
# Modules)
REQUIRE_BUILD_PROFILE = "lms/js/build.js"

# The name of the require.js script used by your project, relative to REQUIRE_BASE_URL.
REQUIRE_JS = "common/js/vendor/require.js"

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = False

# In production, the Django pipeline appends a file hash to JavaScript file names.
# This makes it difficult for RequireJS to load its requirements, since module names
# specified in JavaScript code do not include the hash.
# For this reason, we calculate the actual path including the hash on the server
# when rendering the page.  We then override the default paths provided to RequireJS
# so it can resolve the module name to the correct URL.
#
# If you want to load JavaScript dependencies using RequireJS
# but you don't want to include those dependencies in the JS bundle for the page,
# then you need to add the js urls in this list.
REQUIRE_JS_PATH_OVERRIDES = {
    'course_bookmarks/js/views/bookmark_button': 'course_bookmarks/js/views/bookmark_button.js',
    'js/views/message_banner': 'js/views/message_banner.js',
    'moment': 'common/js/vendor/moment-with-locales.js',
    'moment-timezone': 'common/js/vendor/moment-timezone-with-data.js',
    'js/courseware/course_info_events': 'js/courseware/course_info_events.js',
    'js/courseware/accordion_events': 'js/courseware/accordion_events.js',
    'js/dateutil_factory': 'js/dateutil_factory.js',
    'js/courseware/link_clicked_events': 'js/courseware/link_clicked_events.js',
    'js/courseware/toggle_element_visibility': 'js/courseware/toggle_element_visibility.js',
    'js/student_account/logistration_factory': 'js/student_account/logistration_factory.js',
    'js/courseware/courseware_factory': 'js/courseware/courseware_factory.js',
    'js/groups/views/cohorts_dashboard_factory': 'js/groups/views/cohorts_dashboard_factory.js',
    'js/groups/discussions_management/discussions_dashboard_factory': 'js/discussions_management/views/discussions_dashboard_factory.js',  # pylint: disable=line-too-long
    'draggabilly': 'js/vendor/draggabilly.js',
    'hls': 'common/js/vendor/hls.js'
}

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

########################## DJANGO DEBUG TOOLBAR ###############################

# We don't enable Django Debug Toolbar universally, but whenever we do, we want
# to avoid patching settings.  Patched settings can cause circular import
# problems: https://django-debug-toolbar.readthedocs.org/en/1.0/installation.html#explicit-setup

DEBUG_TOOLBAR_PATCH_SETTINGS = False

################################# CELERY ######################################

# Celery's task autodiscovery won't find tasks nested in a tasks package.
# Tasks are only registered when the module they are defined in is imported.
CELERY_IMPORTS = (
    'openedx.core.djangoapps.programs.tasks.v1.tasks',
)

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
HIGH_MEM_QUEUE = 'edx.core.high_mem'

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_CREATE_MISSING_QUEUES = True

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = [
    'edx.lms.core.default',
    'edx.lms.core.high',
    'edx.lms.core.high_mem'
]

# let logging work as configured:
CELERYD_HIJACK_ROOT_LOGGER = False

CELERY_BROKER_VHOST = ''
CELERY_BROKER_USE_SSL = False
CELERY_EVENT_QUEUE_TTL = None

CELERY_BROKER_TRANSPORT = 'amqp'
CELERY_BROKER_HOSTNAME = 'localhost'
CELERY_BROKER_USER = 'celery'
CELERY_BROKER_PASSWORD = 'celery'
CELERY_TIMEZONE = 'UTC'

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

################################ Bulk Email ###################################

# Suffix used to construct 'from' email address for bulk emails.
# A course-specific identifier is prepended.
BULK_EMAIL_DEFAULT_FROM_EMAIL = 'no-reply@example.com'

# Parameters for breaking down course enrollment into subtasks.
BULK_EMAIL_EMAILS_PER_TASK = 500

# Initial delay used for retrying tasks.  Additional retries use
# longer delays.  Value is in seconds.
BULK_EMAIL_DEFAULT_RETRY_DELAY = 30

# Maximum number of retries per task for errors that are not related
# to throttling.
BULK_EMAIL_MAX_RETRIES = 5

# Maximum number of retries per task for errors that are related to
# throttling.  If this is not set, then there is no cap on such retries.
BULK_EMAIL_INFINITE_RETRY_CAP = 1000

# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it.  At the moment, the name is the same.
BULK_EMAIL_ROUTING_KEY = HIGH_PRIORITY_QUEUE

# We also define a queue for smaller jobs so that large courses don't block
# smaller emails (see BULK_EMAIL_JOB_SIZE_THRESHOLD setting)
BULK_EMAIL_ROUTING_KEY_SMALL_JOBS = DEFAULT_PRIORITY_QUEUE

# For emails with fewer than these number of recipients, send them through
# a different queue to avoid large courses blocking emails that are meant to be
# sent to self and staff
BULK_EMAIL_JOB_SIZE_THRESHOLD = 100

# Flag to indicate if individual email addresses should be logged as they are sent
# a bulk email message.
BULK_EMAIL_LOG_SENT_EMAILS = False

# Delay in seconds to sleep between individual mail messages being sent,
# when a bulk email task is retried for rate-related reasons.  Choose this
# value depending on the number of workers that might be sending email in
# parallel, and what the SES rate is.
BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS = 0.02

############################# Email Opt In ####################################

# Minimum age for organization-wide email opt in
EMAIL_OPTIN_MINIMUM_AGE = PARENTAL_CONSENT_AGE_LIMIT

############################## Video ##########################################

YOUTUBE = {
    # YouTube JavaScript API
    'API': 'https://www.youtube.com/iframe_api',

    'TEST_TIMEOUT': 1500,

    # URL to get YouTube metadata
    'METADATA_URL': 'https://www.googleapis.com/youtube/v3/videos/',

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

################################### APPS ######################################

# The order of INSTALLED_APPS is important, when adding new apps here
# remember to check that you are not creating new
# RemovedInDjango19Warnings in the test logs.
INSTALLED_APPS = [
    # Standard ones that are always installed...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'djcelery',

    # Common Initialization
    'openedx.core.djangoapps.common_initialization.apps.CommonInitializationConfig',

    # LMS-specific Initialization
    'lms_initialization.apps.LMSInitializationConfig',

    # Common views
    'openedx.core.djangoapps.common_views',

    # History tables
    'simple_history',

    # Database-backed configuration
    'config_models',
    'openedx.core.djangoapps.config_model_utils',
    'waffle',

    # Monitor the status of services
    'openedx.core.djangoapps.service_status',

    # Display status message to students
    'status',

    # For asset pipelining
    'edxmako.apps.EdxMakoConfig',
    'pipeline',
    'static_replace',
    'webpack_loader',

    # For user interface plugins
    'web_fragments',
    'openedx.core.djangoapps.plugin_api',

    # For content serving
    'openedx.core.djangoapps.contentserver',

    # Site configuration for theming and behavioral modification
    'openedx.core.djangoapps.site_configuration',

    # Video module configs (This will be moved to Video once it becomes an XBlock)
    'openedx.core.djangoapps.video_config',

    # edX Video Pipeline integration
    'openedx.core.djangoapps.video_pipeline',

    # Our courseware
    'courseware',
    'student.apps.StudentConfig',

    'static_template_view',
    'staticbook',
    'track',
    'eventtracking.django.apps.EventTrackingConfig',
    'util',
    'lms.djangoapps.certificates.apps.CertificatesConfig',
    'dashboard',
    'lms.djangoapps.instructor_task',
    'openedx.core.djangoapps.course_groups',
    'bulk_email',
    'branding',

    # Student support tools
    'support',

    # django-oauth2-provider (deprecated)
    'provider',
    'provider.oauth2',
    'edx_oauth2_provider',

    # django-oauth-toolkit
    'oauth2_provider',
    'openedx.core.djangoapps.oauth_dispatch.apps.OAuthDispatchAppConfig',

    'third_party_auth',

    # We don't use this directly (since we use OAuth2), but we need to install it anyway.
    # When a user is deleted, Django queries all tables with a FK to the auth_user table,
    # and since django-rest-framework-oauth imports this, it will try to access tables
    # defined by oauth_provider.  If those tables don't exist, an error can occur.
    'oauth_provider',

    # System Wide Roles
    'openedx.core.djangoapps.system_wide_roles',

    'openedx.core.djangoapps.auth_exchange',

    # For the wiki
    'wiki',  # The new django-wiki from benjaoming
    'django_notify',
    'course_wiki',  # Our customizations
    'mptt',
    'sekizai',
    #'wiki.plugins.attachments',
    'wiki.plugins.links',
    # Notifications were enabled, but only 11 people used it in three years. It
    # got tangled up during the Django 1.8 migration, so we are disabling it.
    # See TNL-3783 for details.
    #'wiki.plugins.notifications',
    'course_wiki.plugins.markdownedx',

    # For testing
    'django.contrib.admin',  # only used in DEBUG mode
    'debug',
    'openedx.core.djangoapps.util.apps.UtilConfig',

    # Discussion forums
    'openedx.core.djangoapps.django_comment_common',

    # Notes
    'notes',
    'edxnotes',

    # Splash screen
    'splash',

    # User API
    'rest_framework',

    'openedx.core.djangoapps.user_api',

    # Shopping cart
    'shoppingcart',

    # Different Course Modes
    'course_modes.apps.CourseModesConfig',

    # Enrollment API
    'openedx.core.djangoapps.enrollments',

    # Entitlement API
    'entitlements.apps.EntitlementsConfig',

    # Bulk Enrollment API
    'bulk_enroll',

    # Student Identity Verification
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',

    # Dark-launching languages
    'openedx.core.djangoapps.dark_lang',

    # Microsite configuration
    'microsite_configuration.apps.MicrositeConfigurationConfig',

    # RSS Proxy
    'rss_proxy',

    # Country embargo support
    'openedx.core.djangoapps.embargo',

    # Course action state
    'course_action_state',

    # Additional problem types
    'edx_jsme',    # Molecular Structure

    # Country list
    'django_countries',

    # edX Mobile API
    'mobile_api',
    'social_django',

    # Surveys
    'survey.apps.SurveyConfig',

    'lms.djangoapps.lms_xblock.apps.LMSXBlockConfig',

    # Course data caching
    'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig',
    'openedx.core.djangoapps.content.block_structure.apps.BlockStructureConfig',
    'lms.djangoapps.course_blocks',


    # Coursegraph
    'openedx.core.djangoapps.coursegraph.apps.CoursegraphConfig',

    # Mailchimp Syncing
    'mailing',

    # CORS and cross-domain CSRF
    'corsheaders',
    'openedx.core.djangoapps.cors_csrf',

    'lms.djangoapps.commerce.apps.CommerceConfig',

    # Credit courses
    'openedx.core.djangoapps.credit.apps.CreditConfig',

    # Course teams
    'lms.djangoapps.teams',

    'xblock_django',

    # programs support
    'openedx.core.djangoapps.programs.apps.ProgramsConfig',

    # Catalog integration
    'openedx.core.djangoapps.catalog',

    # Self-paced course configuration
    'openedx.core.djangoapps.self_paced',

    'sorl.thumbnail',

    # edx-milestones service
    'milestones',

    # Gating of course content
    'gating.apps.GatingConfig',

    # Static i18n support
    'statici18n',

    # API access administration
    'openedx.core.djangoapps.api_admin',

    # Verified Track Content Cohorting (Beta feature that will hopefully be removed)
    'openedx.core.djangoapps.verified_track_content',

    # Learner's dashboard
    'learner_dashboard',

    # Needed whether or not enabled, due to migrations
    'badges.apps.BadgesConfig',

    # Enables default site and redirects
    'django_sites_extensions',

    # Email marketing integration
    'email_marketing.apps.EmailMarketingConfig',

    # additional release utilities to ease automation
    'release_util',

    # rule-based authorization
    'rules.apps.AutodiscoverRulesConfig',
    'bridgekeeper',

    # Customized celery tasks, including persisting failed tasks so they can
    # be retried
    'celery_utils',

    # Ability to detect and special-case crawler behavior
    'openedx.core.djangoapps.crawlers',

    # Unusual migrations
    'database_fixups',

    'openedx.core.djangoapps.waffle_utils',

    # Course Goals
    'lms.djangoapps.course_goals.apps.CourseGoalsConfig',

    # Features
    'openedx.features.course_bookmarks',
    'openedx.features.course_experience',
    'openedx.features.course_search',
    'openedx.features.enterprise_support.apps.EnterpriseSupportConfig',
    'openedx.features.learner_profile',
    'openedx.features.course_duration_limits',
    'openedx.features.content_type_gating',
    'openedx.features.discounts',

    'experiments',

    # DRF filters
    'django_filters',

    # API Documentation
    'drf_yasg',

    # edx-drf-extensions
    'csrf.apps.CsrfAppConfig',  # Enables frontend apps to retrieve CSRF tokens.
    'xss_utils'
]

######################### CSRF #########################################

# Forwards-compatibility with Django 1.7
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52
# It is highly recommended that you override this in any environment accessed by
# end users
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = []
CROSS_DOMAIN_CSRF_COOKIE_DOMAIN = ''
CROSS_DOMAIN_CSRF_COOKIE_NAME = ''

######################### Django Rest Framework ########################

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'edx_rest_framework_extensions.paginators.DefaultPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'PAGE_SIZE': 10,
    'URL_FORMAT_OVERRIDE': None,
    'DEFAULT_THROTTLE_RATES': {
        'user': '60/minute',
        'service_user': '120/minute',
        'registration_validation': '30/minute',
    },
}

SWAGGER_SETTINGS = {
    'DEFAULT_INFO': 'openedx.core.openapi.openapi_info',
}

######################### MARKETING SITE ###############################
EDXMKTG_LOGGED_IN_COOKIE_NAME = 'edxloggedin'
EDXMKTG_USER_INFO_COOKIE_NAME = 'edx-user-info'
EDXMKTG_USER_INFO_COOKIE_VERSION = 1

MKTG_URLS = {}
MKTG_URL_LINK_MAP = {
    'ABOUT': 'about',
    'CONTACT': 'contact',
    'FAQ': 'help',
    'COURSES': 'courses',
    'ROOT': 'root',
    'TOS': 'tos',
    'HONOR': 'honor',  # If your site does not have an honor code, simply delete this line.
    'PRIVACY': 'privacy',
    'PRESS': 'press',
    'BLOG': 'blog',
    'DONATE': 'donate',
    'SITEMAP.XML': 'sitemap_xml',

    # Verified Certificates
    'WHAT_IS_VERIFIED_CERT': 'verified-certificate',
}

STATIC_TEMPLATE_VIEW_DEFAULT_FILE_EXTENSION = 'html'

SUPPORT_SITE_LINK = ''
ID_VERIFICATION_SUPPORT_LINK = ''
PASSWORD_RESET_SUPPORT_LINK = ''
ACTIVATION_EMAIL_SUPPORT_LINK = ''

# Days before the expired date that we warn the user
ENTITLEMENT_EXPIRED_ALERT_PERIOD = 90

############################# SOCIAL MEDIA SHARING #############################
# Social Media Sharing on Student Dashboard
SOCIAL_SHARING_SETTINGS = {
    # Note: Ensure 'CUSTOM_COURSE_URLS' has a matching value in cms/envs/common.py
    'CUSTOM_COURSE_URLS': False,
    'DASHBOARD_FACEBOOK': False,
    'FACEBOOK_BRAND': None,
    'CERTIFICATE_FACEBOOK': False,
    'CERTIFICATE_FACEBOOK_TEXT': None,
    'CERTIFICATE_TWITTER': False,
    'CERTIFICATE_TWITTER_TEXT': None,
    'DASHBOARD_TWITTER': False,
    'DASHBOARD_TWITTER_TEXT': None,
    'TWITTER_BRAND': None
}

################# Social Media Footer Links #######################
# The names list controls the order of social media
# links in the footer.
SOCIAL_MEDIA_FOOTER_NAMES = [
    "facebook",
    "twitter",
    "youtube",
    "linkedin",
    "google_plus",
    "reddit",
]

# The footer URLs dictionary maps social footer names
# to URLs defined in configuration.
SOCIAL_MEDIA_FOOTER_URLS = {}

# The display dictionary defines the title
# and icon class for each social media link.
SOCIAL_MEDIA_FOOTER_DISPLAY = {
    "facebook": {
        # Translators: This is the website name of www.facebook.com.  Please
        # translate this the way that Facebook advertises in your language.
        "title": _("Facebook"),
        "icon": "fa-facebook-square",
        "action": _(u"Like {platform_name} on Facebook")
    },
    "twitter": {
        # Translators: This is the website name of www.twitter.com.  Please
        # translate this the way that Twitter advertises in your language.
        "title": _("Twitter"),
        "icon": "fa-twitter-square",
        "action": _(u"Follow {platform_name} on Twitter")
    },
    "linkedin": {
        # Translators: This is the website name of www.linkedin.com.  Please
        # translate this the way that LinkedIn advertises in your language.
        "title": _("LinkedIn"),
        "icon": "fa-linkedin-square",
        "action": _(u"Follow {platform_name} on LinkedIn")
    },
    "google_plus": {
        # Translators: This is the website name of plus.google.com.  Please
        # translate this the way that Google+ advertises in your language.
        "title": _("Google+"),
        "icon": "fa-google-plus-square",
        "action": _(u"Follow {platform_name} on Google+")
    },
    "tumblr": {
        # Translators: This is the website name of www.tumblr.com.  Please
        # translate this the way that Tumblr advertises in your language.
        "title": _("Tumblr"),
        "icon": "fa-tumblr"
    },
    "meetup": {
        # Translators: This is the website name of www.meetup.com.  Please
        # translate this the way that MeetUp advertises in your language.
        "title": _("Meetup"),
        "icon": "fa-calendar"
    },
    "reddit": {
        # Translators: This is the website name of www.reddit.com.  Please
        # translate this the way that Reddit advertises in your language.
        "title": _("Reddit"),
        "icon": "fa-reddit-square",
        "action": _(u"Subscribe to the {platform_name} subreddit"),
    },
    "vk": {
        # Translators: This is the website name of https://vk.com.  Please
        # translate this the way that VK advertises in your language.
        "title": _("VK"),
        "icon": "fa-vk"
    },
    "weibo": {
        # Translators: This is the website name of http://www.weibo.com.  Please
        # translate this the way that Weibo advertises in your language.
        "title": _("Weibo"),
        "icon": "fa-weibo"
    },
    "youtube": {
        # Translators: This is the website name of www.youtube.com.  Please
        # translate this the way that YouTube advertises in your language.
        "title": _("Youtube"),
        "icon": "fa-youtube-square",
        "action": _(u"Subscribe to the {platform_name} YouTube channel")
    }
}

################# Mobile URLS ##########################

# These are URLs to the app store for mobile.
MOBILE_STORE_URLS = {}

################# Student Verification #################
VERIFY_STUDENT = {
    "DAYS_GOOD_FOR": 365,  # How many days is a verficiation good for?
    # The variable represents the window within which a verification is considered to be "expiring soon."
    "EXPIRING_SOON_WINDOW": 28,
}

################# Student Verification Expiry Email #################
VERIFICATION_EXPIRY_EMAIL = {
    "RESEND_DAYS": 15,
    "DAYS_RANGE": 1,
    "DEFAULT_EMAILS": 2,
}

DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH = "verify_student_disable_account_activation_requirement"

### This enables the Metrics tab for the Instructor dashboard ###########
FEATURES['CLASS_DASHBOARD'] = False
if FEATURES.get('CLASS_DASHBOARD'):
    INSTALLED_APPS.append('class_dashboard')

################ Enable credit eligibility feature ####################
ENABLE_CREDIT_ELIGIBILITY = True
FEATURES['ENABLE_CREDIT_ELIGIBILITY'] = ENABLE_CREDIT_ELIGIBILITY

############# Cross-domain requests #################

if FEATURES.get('ENABLE_CORS_HEADERS'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = ()
    CORS_ORIGIN_ALLOW_ALL = False
    CORS_ALLOW_HEADERS = corsheaders_default_headers + (
        'use-jwt-cookie',
    )

CORS_ORIGIN_WHITELIST = []
CORS_ORIGIN_ALLOW_ALL = False
# Default cache expiration for the cross-domain proxy HTML page.
# This is a static page that can be iframed into an external page
# to simulate cross-domain requests.
XDOMAIN_PROXY_CACHE_TIMEOUT = 60 * 15

LOGIN_REDIRECT_WHITELIST = []

###################### Registration ##################################

# For each of the fields, give one of the following values:
# - 'required': to display the field, and make it mandatory
# - 'optional': to display the field, and make it non-mandatory
# - 'hidden': to not display the field

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

REGISTRATION_FIELD_ORDER = [
    "name",
    "first_name",
    "last_name",
    "username",
    "email",
    "confirm_email",
    "password",
    "city",
    "state",
    "country",
    "gender",
    "year_of_birth",
    "level_of_education",
    "company",
    "title",
    "mailing_address",
    "goals",
    "honor_code",
    "terms_of_service",
]

# Optional setting to restrict registration / account creation to only emails
# that match a regex in this list. Set to None to allow any email (default).
REGISTRATION_EMAIL_PATTERNS_ALLOWED = None

########################## CERTIFICATE NAME ########################
CERT_NAME_SHORT = "Certificate"
CERT_NAME_LONG = "Certificate of Achievement"

#################### OpenBadges Settings #######################

BADGING_BACKEND = 'badges.backends.badgr.BadgrBackend'

# Be sure to set up images for course modes using the BadgeImageConfiguration model in the certificates app.
BADGR_API_TOKEN = None
# Do not add the trailing slash here.
BADGR_BASE_URL = "http://localhost:8005"
BADGR_ISSUER_SLUG = "example-issuer"
# Number of seconds to wait on the badging server when contacting it before giving up.
BADGR_TIMEOUT = 10

###################### Grade Downloads ######################
# These keys are used for all of our asynchronous downloadable files, including
# the ones that contain information other than grades.
GRADES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

POLICY_CHANGE_GRADES_ROUTING_KEY = 'edx.lms.core.default'

RECALCULATE_GRADES_ROUTING_KEY = 'edx.lms.core.default'

GRADES_DOWNLOAD = {
    'STORAGE_CLASS': 'django.core.files.storage.FileSystemStorage',
    'STORAGE_KWARGS': {
        'location': '/tmp/edx-s3/grades',
    },
    'STORAGE_TYPE': None,
    'BUCKET': None,
    'ROOT_PATH': None,
}

FINANCIAL_REPORTS = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': None,
    'ROOT_PATH': 'sandbox',
}

#### Grading policy change-related settings #####
# Rate limit for regrading tasks that a grading policy change can kick off
POLICY_CHANGE_TASK_RATE_LIMIT = '300/h'

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

############################ ORA 2 ############################################

# By default, don't use a file prefix
ORA2_FILE_PREFIX = None

# Default File Upload Storage bucket and prefix. Used by the FileUpload Service.
FILE_UPLOAD_STORAGE_BUCKET_NAME = 'SET-ME-PLEASE (ex. bucket-name)'
FILE_UPLOAD_STORAGE_PREFIX = 'submissions_attachments'

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = 6
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = 30 * 60


##### LMS DEADLINE DISPLAY TIME_ZONE #######
TIME_ZONE_DISPLAYED_FOR_DEADLINES = 'UTC'


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

# Source:
# http://loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt according to http://en.wikipedia.org/wiki/ISO_639-1
# Note that this is used as the set of choices to the `code` field of the
# `LanguageProficiency` model.
ALL_LANGUAGES = [
    [u"aa", u"Afar"],
    [u"ab", u"Abkhazian"],
    [u"af", u"Afrikaans"],
    [u"ak", u"Akan"],
    [u"sq", u"Albanian"],
    [u"am", u"Amharic"],
    [u"ar", u"Arabic"],
    [u"an", u"Aragonese"],
    [u"hy", u"Armenian"],
    [u"as", u"Assamese"],
    [u"av", u"Avaric"],
    [u"ae", u"Avestan"],
    [u"ay", u"Aymara"],
    [u"az", u"Azerbaijani"],
    [u"ba", u"Bashkir"],
    [u"bm", u"Bambara"],
    [u"eu", u"Basque"],
    [u"be", u"Belarusian"],
    [u"bn", u"Bengali"],
    [u"bh", u"Bihari languages"],
    [u"bi", u"Bislama"],
    [u"bs", u"Bosnian"],
    [u"br", u"Breton"],
    [u"bg", u"Bulgarian"],
    [u"my", u"Burmese"],
    [u"ca", u"Catalan"],
    [u"ch", u"Chamorro"],
    [u"ce", u"Chechen"],
    [u"zh", u"Chinese"],
    [u"zh_HANS", u"Simplified Chinese"],
    [u"zh_HANT", u"Traditional Chinese"],
    [u"cu", u"Church Slavic"],
    [u"cv", u"Chuvash"],
    [u"kw", u"Cornish"],
    [u"co", u"Corsican"],
    [u"cr", u"Cree"],
    [u"cs", u"Czech"],
    [u"da", u"Danish"],
    [u"dv", u"Divehi"],
    [u"nl", u"Dutch"],
    [u"dz", u"Dzongkha"],
    [u"en", u"English"],
    [u"eo", u"Esperanto"],
    [u"et", u"Estonian"],
    [u"ee", u"Ewe"],
    [u"fo", u"Faroese"],
    [u"fj", u"Fijian"],
    [u"fi", u"Finnish"],
    [u"fr", u"French"],
    [u"fy", u"Western Frisian"],
    [u"ff", u"Fulah"],
    [u"ka", u"Georgian"],
    [u"de", u"German"],
    [u"gd", u"Gaelic"],
    [u"ga", u"Irish"],
    [u"gl", u"Galician"],
    [u"gv", u"Manx"],
    [u"el", u"Greek"],
    [u"gn", u"Guarani"],
    [u"gu", u"Gujarati"],
    [u"ht", u"Haitian"],
    [u"ha", u"Hausa"],
    [u"he", u"Hebrew"],
    [u"hz", u"Herero"],
    [u"hi", u"Hindi"],
    [u"ho", u"Hiri Motu"],
    [u"hr", u"Croatian"],
    [u"hu", u"Hungarian"],
    [u"ig", u"Igbo"],
    [u"is", u"Icelandic"],
    [u"io", u"Ido"],
    [u"ii", u"Sichuan Yi"],
    [u"iu", u"Inuktitut"],
    [u"ie", u"Interlingue"],
    [u"ia", u"Interlingua"],
    [u"id", u"Indonesian"],
    [u"ik", u"Inupiaq"],
    [u"it", u"Italian"],
    [u"jv", u"Javanese"],
    [u"ja", u"Japanese"],
    [u"kl", u"Kalaallisut"],
    [u"kn", u"Kannada"],
    [u"ks", u"Kashmiri"],
    [u"kr", u"Kanuri"],
    [u"kk", u"Kazakh"],
    [u"km", u"Central Khmer"],
    [u"ki", u"Kikuyu"],
    [u"rw", u"Kinyarwanda"],
    [u"ky", u"Kirghiz"],
    [u"kv", u"Komi"],
    [u"kg", u"Kongo"],
    [u"ko", u"Korean"],
    [u"kj", u"Kuanyama"],
    [u"ku", u"Kurdish"],
    [u"lo", u"Lao"],
    [u"la", u"Latin"],
    [u"lv", u"Latvian"],
    [u"li", u"Limburgan"],
    [u"ln", u"Lingala"],
    [u"lt", u"Lithuanian"],
    [u"lb", u"Luxembourgish"],
    [u"lu", u"Luba-Katanga"],
    [u"lg", u"Ganda"],
    [u"mk", u"Macedonian"],
    [u"mh", u"Marshallese"],
    [u"ml", u"Malayalam"],
    [u"mi", u"Maori"],
    [u"mr", u"Marathi"],
    [u"ms", u"Malay"],
    [u"mg", u"Malagasy"],
    [u"mt", u"Maltese"],
    [u"mn", u"Mongolian"],
    [u"na", u"Nauru"],
    [u"nv", u"Navajo"],
    [u"nr", u"Ndebele, South"],
    [u"nd", u"Ndebele, North"],
    [u"ng", u"Ndonga"],
    [u"ne", u"Nepali"],
    [u"nn", u"Norwegian Nynorsk"],
    [u"nb", u"Bokmål, Norwegian"],
    [u"no", u"Norwegian"],
    [u"ny", u"Chichewa"],
    [u"oc", u"Occitan"],
    [u"oj", u"Ojibwa"],
    [u"or", u"Oriya"],
    [u"om", u"Oromo"],
    [u"os", u"Ossetian"],
    [u"pa", u"Panjabi"],
    [u"fa", u"Persian"],
    [u"pi", u"Pali"],
    [u"pl", u"Polish"],
    [u"pt", u"Portuguese"],
    [u"ps", u"Pushto"],
    [u"qu", u"Quechua"],
    [u"rm", u"Romansh"],
    [u"ro", u"Romanian"],
    [u"rn", u"Rundi"],
    [u"ru", u"Russian"],
    [u"sg", u"Sango"],
    [u"sa", u"Sanskrit"],
    [u"si", u"Sinhala"],
    [u"sk", u"Slovak"],
    [u"sl", u"Slovenian"],
    [u"se", u"Northern Sami"],
    [u"sm", u"Samoan"],
    [u"sn", u"Shona"],
    [u"sd", u"Sindhi"],
    [u"so", u"Somali"],
    [u"st", u"Sotho, Southern"],
    [u"es", u"Spanish"],
    [u"sc", u"Sardinian"],
    [u"sr", u"Serbian"],
    [u"ss", u"Swati"],
    [u"su", u"Sundanese"],
    [u"sw", u"Swahili"],
    [u"sv", u"Swedish"],
    [u"ty", u"Tahitian"],
    [u"ta", u"Tamil"],
    [u"tt", u"Tatar"],
    [u"te", u"Telugu"],
    [u"tg", u"Tajik"],
    [u"tl", u"Tagalog"],
    [u"th", u"Thai"],
    [u"bo", u"Tibetan"],
    [u"ti", u"Tigrinya"],
    [u"to", u"Tonga (Tonga Islands)"],
    [u"tn", u"Tswana"],
    [u"ts", u"Tsonga"],
    [u"tk", u"Turkmen"],
    [u"tr", u"Turkish"],
    [u"tw", u"Twi"],
    [u"ug", u"Uighur"],
    [u"uk", u"Ukrainian"],
    [u"ur", u"Urdu"],
    [u"uz", u"Uzbek"],
    [u"ve", u"Venda"],
    [u"vi", u"Vietnamese"],
    [u"vo", u"Volapük"],
    [u"cy", u"Welsh"],
    [u"wa", u"Walloon"],
    [u"wo", u"Wolof"],
    [u"xh", u"Xhosa"],
    [u"yi", u"Yiddish"],
    [u"yo", u"Yoruba"],
    [u"za", u"Zhuang"],
    [u"zu", u"Zulu"]
]


### Apps only installed in some instances
# The order of INSTALLED_APPS matters, so this tuple is the app name and the item in INSTALLED_APPS
# that this app should be inserted *before*. A None here means it should be appended to the list.
OPTIONAL_APPS = [
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

    # Enterprise Apps (http://github.com/edx/edx-enterprise)
    ('enterprise', None),
    ('consent', None),
    ('integrated_channels.integrated_channel', None),
    ('integrated_channels.degreed', None),
    ('integrated_channels.sap_success_factors', None),
    ('integrated_channels.cornerstone', None),
    ('integrated_channels.xapi', None),

    # Required by the Enterprise App
    ('django_object_actions', None),  # https://github.com/crccheck/django-object-actions
]

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

### Analytics API
ANALYTICS_API_KEY = ""
ANALYTICS_API_URL = "http://localhost:18100"
ANALYTICS_DASHBOARD_URL = 'http://localhost:18110/courses'
ANALYTICS_DASHBOARD_NAME = 'Your Platform Name Here Insights'

# REGISTRATION CODES DISPLAY INFORMATION SUBTITUTIONS IN THE INVOICE ATTACHMENT
INVOICE_CORP_ADDRESS = "Please place your corporate address\nin this configuration"
INVOICE_PAYMENT_INSTRUCTIONS = "This is where you can\nput directions on how people\nbuying registration codes"

# Country code overrides
# Used by django-countries
COUNTRIES_OVERRIDE = {
    # Taiwan is specifically not translated to avoid it being translated as "Taiwan (Province of China)"
    "TW": "Taiwan",
    'XK': _('Kosovo'),
}

# which access.py permission name to check in order to determine if a course is visible in
# the course catalog. We default this to the legacy permission 'see_exists'.
COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_exists'

# which access.py permission name to check in order to determine if a course about page is
# visible. We default this to the legacy permission 'see_exists'.
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_exists'

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = "both"
DEFAULT_MOBILE_AVAILABLE = False

# Enrollment API Cache Timeout
ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT = 60

# These tabs are currently disabled
NOTES_DISABLED_TABS = ['course_structure', 'tags']

# Configuration used for generating PDF Receipts/Invoices
PDF_RECEIPT_TAX_ID = '00-0000000'
PDF_RECEIPT_FOOTER_TEXT = 'Enter your receipt footer text here.'
PDF_RECEIPT_DISCLAIMER_TEXT = 'ENTER YOUR RECEIPT DISCLAIMER TEXT HERE.'
PDF_RECEIPT_BILLING_ADDRESS = 'Enter your receipt terms and conditions here.'
PDF_RECEIPT_TERMS_AND_CONDITIONS = 'Enter your receipt terms and conditions here.'
PDF_RECEIPT_TAX_ID_LABEL = 'fake Tax ID'
PDF_RECEIPT_LOGO_PATH = PROJECT_ROOT + '/static/images/openedx-logo-tag.png'
# Height of the Logo in mm
PDF_RECEIPT_LOGO_HEIGHT_MM = 12
PDF_RECEIPT_COBRAND_LOGO_PATH = PROJECT_ROOT + '/static/images/logo.png'
# Height of the Co-brand Logo in mm
PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM = 12

# Use None for the default search engine
SEARCH_ENGINE = None
# Use LMS specific search initializer
SEARCH_INITIALIZER = "lms.lib.courseware_search.lms_search_initializer.LmsSearchInitializer"
# Use the LMS specific result processor
SEARCH_RESULT_PROCESSOR = "lms.lib.courseware_search.lms_result_processor.LmsSearchResultProcessor"
# Use the LMS specific filter generator
SEARCH_FILTER_GENERATOR = "lms.lib.courseware_search.lms_filter_generator.LmsSearchFilterGenerator"
# Override to skip enrollment start date filtering in course search
SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = False

# The configuration visibility of account fields.
ACCOUNT_VISIBILITY_CONFIGURATION = {
    # Default visibility level for accounts without a specified value
    # The value is one of: 'all_users', 'private'
    "default_visibility": "all_users",

    # The list of account fields that are always public
    "public_fields": [
        'account_privacy',
        'profile_image',
        'username',
    ],
}

# The list of all fields that are shared with other users using the bulk 'all_users' privacy setting
ACCOUNT_VISIBILITY_CONFIGURATION["bulk_shareable_fields"] = (
    ACCOUNT_VISIBILITY_CONFIGURATION["public_fields"] + [
        'bio',
        'course_certificates',
        'country',
        'date_joined',
        'language_proficiencies',
        "level_of_education",
        'social_links',
        'time_zone',

        # Not an actual field, but used to signal whether badges should be public.
        'accomplishments_shared',
    ]
)

# The list of all fields that can be shared selectively with other users using the 'custom' privacy setting
ACCOUNT_VISIBILITY_CONFIGURATION["custom_shareable_fields"] = (
    ACCOUNT_VISIBILITY_CONFIGURATION["bulk_shareable_fields"] + [
        "name",
    ]
)

# The list of account fields that are visible only to staff and users viewing their own profiles
ACCOUNT_VISIBILITY_CONFIGURATION["admin_fields"] = (
    ACCOUNT_VISIBILITY_CONFIGURATION["custom_shareable_fields"] + [
        "email",
        "extended_profile",
        "gender",
        "goals",
        "is_active",
        "mailing_address",
        "requires_parental_consent",
        "secondary_email",
        "year_of_birth",
    ]
)

# The current list of social platforms to be shown to the user.
#
# url_stub represents the host URL, it must end with a forward
# slash and represent the profile at https://www.[url_stub][username]
#
# The example will be used as a placeholder in the social link
# input field as well as in some messaging describing an example of a
# valid link.
SOCIAL_PLATFORMS = {
    'facebook': {
        'display_name': 'Facebook',
        'url_stub': 'facebook.com/',
        'example': 'https://www.facebook.com/username'
    },
    'twitter': {
        'display_name': 'Twitter',
        'url_stub': 'twitter.com/',
        'example': 'https://www.twitter.com/username'
    },
    'linkedin': {
        'display_name': 'LinkedIn',
        'url_stub': 'linkedin.com/in/',
        'example': 'www.linkedin.com/in/username'
    }
}

# E-Commerce API Configuration
ECOMMERCE_PUBLIC_URL_ROOT = 'http://localhost:8002'
ECOMMERCE_API_URL = 'http://localhost:8002/api/v2'
ECOMMERCE_API_TIMEOUT = 5
ECOMMERCE_SERVICE_WORKER_USERNAME = 'ecommerce_worker'
ECOMMERCE_API_SIGNING_KEY = 'SET-ME-PLEASE'

COURSE_CATALOG_API_URL = 'http://localhost:8008/api/v1'

CREDENTIALS_INTERNAL_SERVICE_URL = 'http://localhost:8005'
CREDENTIALS_PUBLIC_SERVICE_URL = None

JOURNALS_URL_ROOT = 'https://journals-localhost:18000'
JOURNALS_API_URL = 'https://journals-localhost:18000/api/v1/'

COMMENTS_SERVICE_URL = 'http://localhost:18080'
COMMENTS_SERVICE_KEY = 'password'

# Reverification checkpoint name pattern
CHECKPOINT_PATTERN = r'(?P<checkpoint_name>[^/]+)'

# For the fields override feature
# If using FEATURES['INDIVIDUAL_DUE_DATES'], you should add
# 'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider' to
# this setting.
FIELD_OVERRIDE_PROVIDERS = ()

# Modulestore-level field override providers. These field override providers don't
# require student context.
MODULESTORE_FIELD_OVERRIDE_PROVIDERS = ('openedx.features.content_type_gating.field_override.ContentTypeGatingFieldOverride',)  # pylint: disable=line-too-long

# PROFILE IMAGE CONFIG
# WARNING: Certain django storage backends do not support atomic
# file overwrites (including the default, OverwriteStorage) - instead
# there are separate calls to delete and then write a new file in the
# storage backend.  This introduces the risk of a race condition
# occurring when a user uploads a new profile image to replace an
# earlier one (the file will temporarily be deleted).
PROFILE_IMAGE_BACKEND = {
    'class': 'storages.backends.overwrite.OverwriteStorage',
    'options': {
        'location': os.path.join(MEDIA_ROOT, 'profile-images/'),
        'base_url': os.path.join(MEDIA_URL, 'profile-images/'),
    },
}
PROFILE_IMAGE_DEFAULT_FILENAME = 'images/profiles/default'
PROFILE_IMAGE_DEFAULT_FILE_EXTENSION = 'png'
# This secret key is used in generating unguessable URLs to users'
# profile images.  Once it has been set, changing it will make the
# platform unaware of current image URLs, resulting in reverting all
# users' profile images to the default placeholder image.
PROFILE_IMAGE_SECRET_KEY = 'placeholder secret key'
PROFILE_IMAGE_MAX_BYTES = 1024 * 1024
PROFILE_IMAGE_MIN_BYTES = 100
PROFILE_IMAGE_SIZES_MAP = {
    'full': 500,
    'large': 120,
    'medium': 50,
    'small': 30
}

# Sets the maximum number of courses listed on the homepage
# If set to None, all courses will be listed on the homepage
HOMEPAGE_COURSE_MAX = None

################################ Settings for Credit Courses ################################
# Initial delay used for retrying tasks.
# Additional retries use longer delays.
# Value is in seconds.
CREDIT_TASK_DEFAULT_RETRY_DELAY = 30

# Maximum number of retries per task for errors that are not related
# to throttling.
CREDIT_TASK_MAX_RETRIES = 5

# Dummy secret key for dev/test
SECRET_KEY = 'dev key'

# Secret keys shared with credit providers.
# Used to digitally sign credit requests (us --> provider)
# and validate responses (provider --> us).
# Each key in the dictionary is a credit provider ID, and
# the value is the 32-character key.
CREDIT_PROVIDER_SECRET_KEYS = {}

# Maximum age in seconds of timestamps we will accept
# when a credit provider notifies us that a student has been approved
# or denied for credit.
CREDIT_PROVIDER_TIMESTAMP_EXPIRATION = 15 * 60

# The Help link to the FAQ page about the credit
CREDIT_HELP_LINK_URL = "/"

# Default domain for the e-mail address associated with users who are created
# via the LTI Provider feature. Note that the generated e-mail addresses are
# not expected to be active; this setting simply allows administrators to
# route any messages intended for LTI users to a common domain.
LTI_USER_EMAIL_DOMAIN = 'lti.example.com'

# An aggregate score is one derived from multiple problems (such as the
# cumulative score for a vertical element containing many problems). Sending
# aggregate scores immediately introduces two issues: one is a race condition
# between the view method and the Celery task where the updated score may not
# yet be visible to the database if the view has not yet returned (and committed
# its transaction). The other is that the student is likely to receive a stream
# of notifications as the score is updated with every problem. Waiting a
# reasonable period of time allows the view transaction to end, and allows us to
# collapse multiple score updates into a single message.
# The time value is in seconds.
LTI_AGGREGATE_SCORE_PASSBACK_DELAY = 15 * 60

# Credit notifications settings
NOTIFICATION_EMAIL_CSS = "templates/credit_notifications/credit_notification.css"
NOTIFICATION_EMAIL_EDX_LOGO = "templates/credit_notifications/edx-logo-header.png"


################################ Settings for JWTs ################################

JWT_AUTH = {
    'JWT_VERIFY_EXPIRATION': True,

    'JWT_PAYLOAD_GET_USERNAME_HANDLER': lambda d: d.get('username'),
    'JWT_LEEWAY': 1,
    'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',

    'JWT_AUTH_COOKIE': 'edx-jwt-cookie',

    # Number of seconds before JWTs expire
    'JWT_EXPIRATION': 30,
    'JWT_IN_COOKIE_EXPIRATION': 60 * 60,

    'JWT_LOGIN_CLIENT_ID': 'login-service-client-id',
    'JWT_LOGIN_SERVICE_USERNAME': 'login_service_user',

    'JWT_SUPPORTED_VERSION': '1.2.0',

    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SECRET_KEY,

    'JWT_SIGNING_ALGORITHM': 'RS512',
    'JWT_PRIVATE_SIGNING_JWK': None,
    'JWT_PUBLIC_SIGNING_JWK_SET': None,

    'JWT_ISSUER': 'change-me',
    'JWT_AUDIENCE': 'change-me',
}

EDX_DRF_EXTENSIONS = {
    # Set this value to an empty dict in order to prevent automatically updating
    # user data from values in (possibly stale) JWTs.
    'JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING': {},
}

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

MICROSITE_ROOT_DIR = '/edx/app/edxapp/edx-microsite'
MICROSITE_CONFIGURATION = {}

################################ Settings for rss_proxy ################################

RSS_PROXY_CACHE_TIMEOUT = 3600  # The length of time we cache RSS retrieved from remote URLs in seconds

#### Custom Courses for EDX (CCX) configuration

# This is an arbitrary hard limit.
# The reason we introcuced this number is because we do not want the CCX
# to compete with the MOOC.
CCX_MAX_STUDENTS_ALLOWED = 200

# Financial assistance settings

# Maximum and minimum length of answers, in characters, for the
# financial assistance form
FINANCIAL_ASSISTANCE_MIN_LENGTH = 250
FINANCIAL_ASSISTANCE_MAX_LENGTH = 2500

#### Registration form extension. ####
# Only used if combined login/registration is enabled.
# This can be used to add fields to the registration page.
# It must be a path to a valid form, in dot-separated syntax.
# IE: custom_form_app.forms.RegistrationExtensionForm
# Note: If you want to use a model to store the results of the form, you will
# need to add the model's app to the ADDL_INSTALLED_APPS array in your
# lms.env.json file.

REGISTRATION_EXTENSION_FORM = None

# Identifier included in the User Agent from open edX mobile apps.
MOBILE_APP_USER_AGENT_REGEXES = [
    r'edX/org.edx.mobile',
]

# cache timeout in seconds for Mobile App Version Upgrade
APP_UPGRADE_CACHE_TIMEOUT = 3600

# Offset for courseware.StudentModuleHistoryExtended which is used to
# calculate the starting primary key for the underlying table.  This gap
# should be large enough that you do not generate more than N courseware.StudentModuleHistory
# records before you have deployed the app to write to coursewarehistoryextended.StudentModuleHistoryExtended
# if you want to avoid an overlap in ids while searching for history across the two tables.
STUDENTMODULEHISTORYEXTENDED_OFFSET = 10000

# Cutoff date for granting audit certificates

AUDIT_CERT_CUTOFF_DATE = None

################################ Settings for Credentials Service ################################

CREDENTIALS_SERVICE_USERNAME = 'credentials_service_user'
CREDENTIALS_GENERATION_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

# Queue to use for award program certificates
PROGRAM_CERTIFICATES_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

# Settings for Comprehensive Theming app

# See https://github.com/edx/edx-django-sites-extensions for more info
# Default site to use if site matching request headers does not exist
SITE_ID = 1

# dir containing all themes
COMPREHENSIVE_THEME_DIRS = []

# Theme directory locale paths
COMPREHENSIVE_THEME_LOCALE_PATHS = []

# Theme to use when no site or site theme is defined,
# set to None if you want to use openedx theme
DEFAULT_SITE_THEME = None

ENABLE_COMPREHENSIVE_THEMING = False

# API access management
API_ACCESS_MANAGER_EMAIL = 'api-access@example.com'
API_ACCESS_FROM_EMAIL = 'api-requests@example.com'
API_DOCUMENTATION_URL = 'https://course-catalog-api-guide.readthedocs.io/en/latest/'
AUTH_DOCUMENTATION_URL = 'https://course-catalog-api-guide.readthedocs.io/en/latest/authentication/index.html'

# Affiliate cookie tracking
AFFILIATE_COOKIE_NAME = 'dev_affiliate_id'

############## Settings for RedirectMiddleware ###############

# Setting this to None causes Redirect data to never expire
# The cache is cleared when Redirect models are saved/deleted
REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
REDIRECT_CACHE_KEY_PREFIX = 'redirects'

############## Settings for LMS Context Sensitive Help ##############

HELP_TOKENS_INI_FILE = REPO_ROOT / "lms" / "envs" / "help_tokens.ini"
HELP_TOKENS_LANGUAGE_CODE = lambda settings: settings.LANGUAGE_CODE
HELP_TOKENS_VERSION = lambda settings: doc_version()
HELP_TOKENS_BOOKS = {
    'learner': 'https://edx.readthedocs.io/projects/open-edx-learner-guide',
    'course_author': 'https://edx.readthedocs.io/projects/open-edx-building-and-running-a-course',
}
derived('HELP_TOKENS_LANGUAGE_CODE', 'HELP_TOKENS_VERSION')

############## OPEN EDX ENTERPRISE SERVICE CONFIGURATION ######################
# The Open edX Enterprise service is currently hosted via the LMS container/process.
# However, for all intents and purposes this service is treated as a standalone IDA.
# These configuration settings are specific to the Enterprise service and you should
# not find references to them within the edx-platform project.
#
# Only used if FEATURES['ENABLE_ENTERPRISE_INTEGRATION'] == True.

ENTERPRISE_ENROLLMENT_API_URL = LMS_INTERNAL_ROOT_URL + LMS_ENROLLMENT_API_PATH
ENTERPRISE_PUBLIC_ENROLLMENT_API_URL = LMS_ROOT_URL + LMS_ENROLLMENT_API_PATH
ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES = ['audit', 'honor']
ENTERPRISE_SUPPORT_URL = ''
# The default value of this needs to be a 16 character string
ENTERPRISE_REPORTING_SECRET = '0000000000000000'
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = {}
ENTERPRISE_CUSTOMER_SUCCESS_EMAIL = "customersuccess@edx.org"

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the EdxRestApiClient class
# These default settings are utilized by the LMS when interacting with the service,
# and are overridden by the configuration parameter accessors defined in production.py

ENTERPRISE_API_URL = 'https://localhost:18000/enterprise/api/v1'
ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
ENTERPRISE_SERVICE_WORKER_USERNAME = 'enterprise_worker'
ENTERPRISE_API_CACHE_TIMEOUT = 3600  # Value is in seconds
ENTERPRISE_CUSTOMER_LOGO_IMAGE_SIZE = 512   # Enterprise logo image size limit in KB's

############## ENTERPRISE SERVICE LMS CONFIGURATION ##################################
# The LMS has some features embedded that are related to the Enterprise service, but
# which are not provided by the Enterprise service. These settings provide base values
# for those features.

ENTERPRISE_PLATFORM_WELCOME_TEMPLATE = _(u'Welcome to {platform_name}.')
ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE = _(
    u'You have left the {start_bold}{enterprise_name}{end_bold} website and are now on the {platform_name} site. '
    u'{enterprise_name} has partnered with {platform_name} to offer you high-quality, always available learning '
    u'programs to help you advance your knowledge and career. '
    u'{line_break}Please note that {platform_name} has a different {privacy_policy_link_start}Privacy Policy'
    u'{privacy_policy_link_end} from {enterprise_name}.'
)
ENTERPRISE_TAGLINE = ''
ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS = {
    'age',
    'level_of_education',
    'gender',
    'goals',
    'year_of_birth',
    'mailing_address',
}
ENTERPRISE_READONLY_ACCOUNT_FIELDS = [
    'username',
    'name',
    'email',
    'country',
]
ENTERPRISE_CUSTOMER_COOKIE_NAME = 'enterprise_customer_uuid'
BASE_COOKIE_DOMAIN = 'localhost'
SYSTEM_TO_FEATURE_ROLE_MAPPING = {
    ENTERPRISE_ADMIN_ROLE: [ENTERPRISE_DASHBOARD_ADMIN_ROLE],
    ENTERPRISE_OPERATOR_ROLE: [
        ENTERPRISE_DASHBOARD_ADMIN_ROLE,
        ENTERPRISE_CATALOG_ADMIN_ROLE,
        ENTERPRISE_ENROLLMENT_API_ADMIN_ROLE
    ],
}

DATA_CONSENT_SHARE_CACHE_TIMEOUT = 8 * 60 * 60  # 8 hours

ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS = {}
ENTERPRISE_TAGLINE = ''

############## Settings for Course Enrollment Modes ######################
# The min_price key refers to the minimum price allowed for an instance
# of a particular type of course enrollment mode. This is not to be confused
# with the min_price field of the CourseMode model, which refers to the actual
# price of the CourseMode.
COURSE_ENROLLMENT_MODES = {
    "audit": {
        "id": 1,
        "slug": "audit",
        "display_name": _("Audit"),
        "min_price": 0,
    },
    "verified": {
        "id": 2,
        "slug": "verified",
        "display_name": _("Verified"),
        "min_price": 1,
    },
    "professional": {
        "id": 3,
        "slug": "professional",
        "display_name": _("Professional"),
        "min_price": 1,
    },
    "no-id-professional": {
        "id": 4,
        "slug": "no-id-professional",
        "display_name": _("No-Id-Professional"),
        "min_price": 0,
    },
    "credit": {
        "id": 5,
        "slug": "credit",
        "display_name": _("Credit"),
        "min_price": 0,
    },
    "honor": {
        "id": 6,
        "slug": "honor",
        "display_name": _("Honor"),
        "min_price": 0,
    },
    "masters": {
        "id": 7,
        "slug": "masters",
        "display_name": _("Master's"),
        "min_price": 0,
    },
}

CONTENT_TYPE_GATE_GROUP_IDS = {
    'limited_access': 1,
    'full_access': 2,
}

############## Settings for the Discovery App ######################

COURSES_API_CACHE_TIMEOUT = 3600  # Value is in seconds

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = DEFAULT_PRIORITY_QUEUE


# Initialize to 'unknown', but read from JSON in production.py
EDX_PLATFORM_REVISION = 'release'

############## Settings for Completion API #########################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = 0.95
COMPLETION_BY_VIEWING_DELAY_MS = 5000

############### Settings for Django Rate limit #####################
RATELIMIT_ENABLE = True
RATELIMIT_RATE = '120/m'

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

############## Settings for Microfrontends  #########################
# If running a Gradebook container locally,
# modify lms/envs/private.py to give it a non-null value
WRITABLE_GRADEBOOK_URL = None

PROFILE_MICROFRONTEND_URL = None
ORDER_HISTORY_MICROFRONTEND_URL = None
ACCOUNT_MICROFRONTEND_URL = None
PROGRAM_MANAGER_MICROFRONTEND_URL = None

############### Settings for the ace_common plugin #################
ACE_ENABLED_CHANNELS = ['django_email']
ACE_ENABLED_POLICIES = ['bulk_email_optout']
ACE_CHANNEL_SAILTHRU_DEBUG = True
ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = None
ACE_ROUTING_KEY = 'edx.lms.core.default'
ACE_CHANNEL_DEFAULT_EMAIL = 'django_email'
ACE_CHANNEL_TRANSACTIONAL_EMAIL = 'django_email'

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

############### Settings for facebook ##############################
FACEBOOK_APP_ID = 'FACEBOOK_APP_ID'
FACEBOOK_APP_SECRET = 'FACEBOOK_APP_SECRET'
FACEBOOK_API_VERSION = 'v2.1'

############### Settings for django-fernet-fields ##################
FERNET_KEYS = [
    'DUMMY KEY CHANGE BEFORE GOING TO PRODUCTION',
]

############### Settings for user-state-client ##################
# Maximum number of rows to fetch in XBlockUserStateClient calls. Adjust for performance
USER_STATE_BATCH_SIZE = 5000

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = []

############## Plugin Django Apps #########################

from openedx.core.djangoapps.plugins import plugin_apps, plugin_settings, constants as plugin_constants
INSTALLED_APPS.extend(plugin_apps.get_apps(plugin_constants.ProjectType.LMS))
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.LMS, plugin_constants.SettingsType.COMMON)

DEPRECATED_ADVANCED_COMPONENT_TYPES = []

############### Settings for video pipeline ##################
VIDEO_UPLOAD_PIPELINE = {
    'BUCKET': '',
    'ROOT_PATH': '',
}

############### Settings for django file storage ##################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

### Proctoring configuration (redirct URLs and keys shared between systems) ####
PROCTORING_BACKENDS = {
    'DEFAULT': 'null',
    # The null key needs to be quoted because
    # null is a language independent type in YAML
    'null': {}
}

############### The SAML private/public key values ################
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = ""
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = ""
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT = {}
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT = {}
