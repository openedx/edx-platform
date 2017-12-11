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
    USE_TZ, TECH_SUPPORT_EMAIL, PLATFORM_NAME, PLATFORM_DESCRIPTION, BUGS_EMAIL, DOC_STORE_CONFIG, DATA_DIR,
    ALL_LANGUAGES, WIKI_ENABLED, update_module_store_settings, ASSET_IGNORE_REGEX,
    PARENTAL_CONSENT_AGE_LIMIT, REGISTRATION_EMAIL_PATTERNS_ALLOWED,
    # The following PROFILE_IMAGE_* settings are included as they are
    # indirectly accessed through the email opt-in API, which is
    # technically accessible through the CMS via legacy URLs.
    PROFILE_IMAGE_BACKEND, PROFILE_IMAGE_DEFAULT_FILENAME, PROFILE_IMAGE_DEFAULT_FILE_EXTENSION,
    PROFILE_IMAGE_SECRET_KEY, PROFILE_IMAGE_MIN_BYTES, PROFILE_IMAGE_MAX_BYTES, PROFILE_IMAGE_SIZES_MAP,
    # The following setting is included as it is used to check whether to
    # display credit eligibility table on the CMS or not.
    ENABLE_CREDIT_ELIGIBILITY, YOUTUBE_API_KEY,
    COURSE_MODE_DEFAULTS, DEFAULT_COURSE_ABOUT_IMAGE_URL,

    # User-uploaded content
    MEDIA_ROOT,
    MEDIA_URL,

    # Lazy Gettext
    _,

    # Django REST framework configuration
    REST_FRAMEWORK,

    STATICI18N_OUTPUT_DIR,

    # Theme to use when no site or site theme is defined,
    DEFAULT_SITE_THEME,

    # Default site to use if no site exists matching request headers
    SITE_ID,

    # Enable or disable theming
    ENABLE_COMPREHENSIVE_THEMING,
    COMPREHENSIVE_THEME_LOCALE_PATHS,
    COMPREHENSIVE_THEME_DIRS,

    # constants for redirects app
    REDIRECT_CACHE_TIMEOUT,
    REDIRECT_CACHE_KEY_PREFIX,

    JWT_AUTH,

    USERNAME_REGEX_PARTIAL,
    USERNAME_PATTERN,

    # django-debug-toolbar
    DEBUG_TOOLBAR_PATCH_SETTINGS,
    BLOCK_STRUCTURES_SETTINGS,

    # File upload defaults
    FILE_UPLOAD_STORAGE_BUCKET_NAME,
    FILE_UPLOAD_STORAGE_PREFIX,

    COURSE_ENROLLMENT_MODES,

    HELP_TOKENS_BOOKS,

    SUPPORT_SITE_LINK,
    PASSWORD_RESET_SUPPORT_LINK,
    ACTIVATION_EMAIL_SUPPORT_LINK,

    DEFAULT_MOBILE_AVAILABLE,

    CONTACT_EMAIL,

    DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH,
    # Video Image settings
    VIDEO_IMAGE_SETTINGS,
    VIDEO_TRANSCRIPTS_SETTINGS,

    # Methods to derive settings
    _make_mako_template_dirs,
    _make_locale_paths,
)
from path import Path as path
from warnings import simplefilter

from lms.djangoapps.lms_xblock.mixin import LmsBlockMixin
from cms.lib.xblock.authoring_mixin import AuthoringMixin
import dealer.git
from xmodule.modulestore.edit_info import EditInfoMixin
from openedx.core.djangoapps.theming.helpers_dirs import (
    get_themes_unchecked,
    get_theme_base_dirs_from_settings
)
from openedx.core.lib.license import LicenseMixin
from openedx.core.lib.derived import derived, derived_collection_entry
from openedx.core.release import doc_version

############################ FEATURE CONFIGURATION #############################


# Dummy secret key for dev/test
SECRET_KEY = 'dev key'

STUDIO_NAME = _("Your Platform Studio")
STUDIO_SHORT_NAME = _("Studio")
FEATURES = {
    'GITHUB_PUSH': False,

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the ones in lms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,
    'ENABLE_STUDENT_NOTES': True,

    'AUTH_USE_CERTIFICATES': False,

    # email address for studio staff (eg to request course creation)
    'STUDIO_REQUEST_EMAIL': '',

    # Segment - must explicitly turn it on for production
    'CMS_SEGMENT_KEY': None,

    # Enable URL that shows information about the status of various services
    'ENABLE_SERVICE_STATUS': False,

    # Don't autoplay videos for course authors
    'AUTOPLAY_VIDEOS': False,

    # If set to True, new Studio users won't be able to author courses unless
    # an Open edX admin has added them to the course creator group.
    'ENABLE_CREATOR_GROUP': True,

    # whether to use password policy enforcement or not
    'ENFORCE_PASSWORD_POLICY': False,

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

    # Turn off Advanced Security by default
    'ADVANCED_SECURITY': False,

    # Turn off Video Upload Pipeline through Studio, by default
    'ENABLE_VIDEO_UPLOAD_PIPELINE': False,

    # let students save and manage their annotations
    # for consistency in user-experience, keep the value of this feature flag
    # in sync with the one in lms/envs/common.py
    'ENABLE_EDXNOTES': False,

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

    # Can the visibility of the discussion tab be configured on a per-course basis?
    'ALLOW_HIDING_DISCUSSION_TAB': False,

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

    # Whether archived courses (courses with end dates in the past) should be
    # shown in Studio in a separate list.
    'ENABLE_SEPARATE_ARCHIVED_COURSES': True,
}

ENABLE_JASMINE = False

############################# SOCIAL MEDIA SHARING #############################
SOCIAL_SHARING_SETTINGS = {
    # Note: Ensure 'CUSTOM_COURSE_URLS' has a matching value in lms/envs/common.py
    'CUSTOM_COURSE_URLS': False
}

############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /edx-platform/cms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
OPENEDX_ROOT = REPO_ROOT / "openedx"
CMS_ROOT = REPO_ROOT / "cms"
LMS_ROOT = REPO_ROOT / "lms"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /edx-platform is in

GITHUB_REPO_ROOT = ENV_ROOT / "data"

sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'djangoapps')

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoIP.dat"
GEOIPV6_PATH = REPO_ROOT / "common/static/data/geoip/GeoIPv6.dat"

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
    'dealer.contrib.django.staff.context_processor',  # access git revision
    'help_tokens.context_processor',
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

##############################################################################

EDX_ROOT_URL = ''

LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/signin'
LOGIN_URL = EDX_ROOT_URL + '/signin'

# use the ratelimit backend to prevent brute force attacks
AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'ratelimitbackend.backends.RateLimitModelBackend',
]

LMS_BASE = None
LMS_ROOT_URL = "http://localhost:8000"
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL
LMS_ENROLLMENT_API_PATH = "/api/enrollment/v1/"
ENTERPRISE_API_URL = LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'

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

#################### CAPA External Code Evaluation #############################
XQUEUE_INTERFACE = {
    'url': 'http://localhost:8888',
    'django_auth': {'username': 'local',
                    'password': 'local'},
    'basic_auth': None,
}

################################# Deprecation warnings #####################

# Ignore deprecation warnings (so we don't clutter Jenkins builds/production)
simplefilter('ignore')

################################# Middleware ###################################

MIDDLEWARE_CLASSES = [
    'crum.CurrentRequestUserMiddleware',
    'request_cache.middleware.RequestCache',

    'openedx.core.djangoapps.monitoring_utils.middleware.MonitoringMemoryMiddleware',

    'openedx.core.djangoapps.header_control.middleware.HeaderControlMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'birdcage.v1_11.csrf.CsrfViewMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',

    # Instead of SessionMiddleware, we use a more secure version
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware',

    'method_override.middleware.MethodOverrideMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'openedx.core.djangoapps.cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',
    # Enable SessionAuthenticationMiddleware in order to invalidate
    # user sessions after a password change.
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',

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

    # This must be last so that it runs first in the process_response chain
    'openedx.core.djangoapps.site_configuration.middleware.SessionCookieDomainOverrideMiddleware',
]

# Clickjacking protection can be enabled by setting this to 'DENY'
X_FRAME_OPTIONS = 'ALLOW'

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

############################ Modulestore Configuration ################################
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

#################### Python sandbox ############################################

CODE_JAIL = {
    # Path to a sandboxed Python executable.  None means don't bother.
    'python_bin': None,
    # User to run as in the sandbox.
    'user': 'sandbox',

    # Configurable limits.
    'limits': {
        # How many CPU seconds can jailed code use?
        'CPU': 1,
    },
}

############################ DJANGO_BUILTINS ################################
# Change DEBUG in your environment settings files, not here
DEBUG = False
SESSION_COOKIE_SECURE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


# Site info
SITE_NAME = "localhost:8001"
HTTPS = 'on'
ROOT_URLCONF = 'cms.urls'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'registration@example.com'
DEFAULT_FEEDBACK_EMAIL = 'feedback@example.com'
SERVER_EMAIL = 'devops@example.com'
ADMINS = []
MANAGERS = ADMINS

EDX_PLATFORM_REVISION = os.environ.get('EDX_PLATFORM_REVISION')

if not EDX_PLATFORM_REVISION:
    try:
        # Get git revision of the current file
        EDX_PLATFORM_REVISION = dealer.git.Backend(path=REPO_ROOT).revision
    except TypeError:
        # Not a git repository
        EDX_PLATFORM_REVISION = 'unknown'

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
TIME_ZONE = 'America/New_York'  # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGES_BIDI = lms.envs.common.LANGUAGES_BIDI

LANGUAGE_COOKIE = lms.envs.common.LANGUAGE_COOKIE

LANGUAGES = lms.envs.common.LANGUAGES
LANGUAGE_DICT = dict(LANGUAGES)

USE_I18N = True
USE_L10N = True

STATICI18N_ROOT = PROJECT_ROOT / "static"

# Localization strings (e.g. django.po) are under these directories
LOCALE_PATHS = _make_locale_paths
derived('LOCALE_PATHS')

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

COURSE_IMPORT_EXPORT_STORAGE = 'django.core.files.storage.FileSystemStorage'

##### EMBARGO #####
EMBARGO_SITE_REDIRECT_URL = None

############################### PIPELINE #######################################

PIPELINE_ENABLED = True

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

# Don't use compression by default
PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.uglifyjs.UglifyJSCompressor'

# Don't wrap JavaScript as there is code that depends upon updating the global namespace
PIPELINE_DISABLE_WRAPPER = True

# Specify the UglifyJS binary to use
PIPELINE_UGLIFYJS_BINARY = 'node_modules/.bin/uglifyjs'

from openedx.core.lib.rooted_paths import rooted_glob

PIPELINE_CSS = {
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
PIPELINE_JS = {
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

PIPELINE_COMPILERS = (
    'pipeline.compilers.coffee.CoffeeScriptCompiler',
)

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None

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
    "coffee/*.coffee",
    "coffee/*/*.coffee",
    "coffee/*/*/*.coffee",
    "coffee/*/*/*/*.coffee",

    # Ignore tests
    "spec",
    "spec_helpers",

    # Symlinks used by js-test-tool
    "xmodule_js",
    "common_static",
)

PIPELINE_YUI_BINARY = 'yui-compressor'

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
    }
}
WEBPACK_CONFIG_PATH = 'webpack.prod.config.js'

################################# CELERY ######################################

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
LOW_PRIORITY_QUEUE = 'edx.core.low'

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_CREATE_MISSING_QUEUES = True

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {}
}


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

    # History tables
    'simple_history',

    # Database-backed configuration
    'config_models',
    'waffle',

    # Monitor the status of services
    'openedx.core.djangoapps.service_status',

    # Bookmarks
    'openedx.core.djangoapps.bookmarks.apps.BookmarksConfig',

    # Video module configs (This will be moved to Video once it becomes an XBlock)
    'openedx.core.djangoapps.video_config',

    # edX Video Pipeline integration
    'openedx.core.djangoapps.video_pipeline',

    # For CMS
    'contentstore.apps.ContentstoreConfig',

    'openedx.core.djangoapps.contentserver',
    'course_creators',
    'openedx.core.djangoapps.external_auth',
    'student',  # misleading name due to sharing with lms
    'openedx.core.djangoapps.course_groups',  # not used in cms (yet), but tests run
    'xblock_config.apps.XBlockConfig',

    # Maintenance tools
    'maintenance',
    'openedx.core.djangoapps.util.apps.UtilConfig',

    # Tracking
    'track',
    'eventtracking.django.apps.EventTrackingConfig',

    # Monitoring
    'openedx.core.djangoapps.datadog.apps.DatadogConfig',

    # For asset pipelining
    'edxmako.apps.EdxMakoConfig',
    'pipeline',
    'static_replace',
    'require',
    'webpack_loader',

    # Theming
    'openedx.core.djangoapps.theming.apps.ThemingConfig',

    # Site configuration for theming and behavioral modification
    'openedx.core.djangoapps.site_configuration',

    # Ability to detect and special-case crawler behavior
    'openedx.core.djangoapps.crawlers',

    # comment common
    'django_comment_common',

    # for course creator table
    'django.contrib.admin',

    # for managing course modes
    'course_modes.apps.CourseModesConfig',

    # Verified Track Content Cohorting (Beta feature that will hopefully be removed)
    'openedx.core.djangoapps.verified_track_content',

    # Dark-launching languages
    'openedx.core.djangoapps.dark_lang',

    # User preferences
    'openedx.core.djangoapps.user_api',
    'django_openid_auth',

    # Country embargo support
    'openedx.core.djangoapps.embargo',

    # Signals
    'openedx.core.djangoapps.signals.apps.SignalConfig',

    # Course action state
    'course_action_state',

    # Additional problem types
    'edx_jsme',    # Molecular Structure

    'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig',
    'openedx.core.djangoapps.content.course_structures.apps.CourseStructuresConfig',
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

    # edX Proctoring
    'edx_proctoring',

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
    'oauth_provider',
    'courseware',
    'survey',
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
    'lms.djangoapps.completion.apps.CompletionAppConfig',

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

    # Dynamic schedules
    'openedx.core.djangoapps.ace_common.apps.AceCommonConfig',
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig',

    # DRF filters
    'django_filters',
    'cms.djangoapps.api',

    # Entitlements, used in openedx tests
    'entitlements',
]


################# EDX MARKETING SITE ##################################

EDXMKTG_LOGGED_IN_COOKIE_NAME = 'edxloggedin'
EDXMKTG_USER_INFO_COOKIE_NAME = 'edx-user-info'
EDXMKTG_USER_INFO_COOKIE_VERSION = 1

MKTG_URLS = {}
MKTG_URL_LINK_MAP = {

}

COURSES_WITH_UNSAFE_CODE = []

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

#### PASSWORD POLICY SETTINGS #####

PASSWORD_MIN_LENGTH = None
PASSWORD_MAX_LENGTH = None
PASSWORD_COMPLEXITY = {}
PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD = None
PASSWORD_DICTIONARY = []

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = 5
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = 15 * 60


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


### ADVANCED_SECURITY_CONFIG
# Empty by default
ADVANCED_SECURITY_CONFIG = {}

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
    }
]


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
        '\application/pdf\""',
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

XBLOCK_SETTINGS = {
    "VideoDescriptor": {
        "licensing_enabled": FEATURES.get("LICENSING", False)
    },
    'VideoModule': {
        'YOUTUBE_API_KEY': YOUTUBE_API_KEY
    }
}

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

############################### PROCTORING CONFIGURATION DEFAULTS ##############
PROCTORING_BACKEND_PROVIDER = {
    'class': 'edx_proctoring.backends.null.NullBackendProvider',
    'options': {},
}
PROCTORING_SETTINGS = {}

############################ Global Database Configuration #####################

DATABASE_ROUTERS = [
    'openedx.core.lib.django_courseware_routers.StudentModuleHistoryExtendedRouter',
]

############################ OAUTH2 Provider ###################################

# OpenID Connect issuer ID. Normally the URL of the authentication endpoint.
OAUTH_OIDC_ISSUER = 'https://www.example.com/oauth2'

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
derived('HELP_TOKENS_LANGUAGE_CODE', 'HELP_TOKENS_VERSION')

# This is required for the migrations in oauth_dispatch.models
# otherwise it fails saying this attribute is not present in Settings
# Although Studio does not exable OAuth2 Provider capability, the new approach
# to generating test databases will discover and try to create all tables
# and this setting needs to be present
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

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

############## Settings for the Discovery App ######################

COURSE_CATALOG_API_URL = None

############################# Persistent Grades ####################################

# Queue to use for updating persistent grades
RECALCULATE_GRADES_ROUTING_KEY = LOW_PRIORITY_QUEUE

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = LOW_PRIORITY_QUEUE

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = LOW_PRIORITY_QUEUE

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
ZENDESK_URL = None
ZENDESK_USER = None
ZENDESK_API_KEY = None
ZENDESK_OAUTH_ACCESS_TOKEN = None
ZENDESK_CUSTOM_FIELDS = {}
