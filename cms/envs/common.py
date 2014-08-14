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

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0611, W0614

import imp
import os
import sys
import lms.envs.common
# Although this module itself may not use these imported variables, other dependent modules may.
from lms.envs.common import (
    USE_TZ, TECH_SUPPORT_EMAIL, PLATFORM_NAME, BUGS_EMAIL, DOC_STORE_CONFIG, ALL_LANGUAGES, WIKI_ENABLED, MODULESTORE,
    update_module_store_settings, ASSET_IGNORE_REGEX
)
from path import path
from warnings import simplefilter

from lms.lib.xblock.mixin import LmsBlockMixin
from dealer.git import git

############################ FEATURE CONFIGURATION #############################

FEATURES = {
    'USE_DJANGO_PIPELINE': True,

    'GITHUB_PUSH': False,

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the ones in lms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,
    'ENABLE_STUDENT_NOTES': True,

    'AUTH_USE_CERTIFICATES': False,

    # email address for studio staff (eg to request course creation)
    'STUDIO_REQUEST_EMAIL': '',

    # Segment.io - must explicitly turn it on for production
    'SEGMENT_IO': False,

    # Enable URL that shows information about the status of various services
    'ENABLE_SERVICE_STATUS': False,

    # Don't autoplay videos for course authors
    'AUTOPLAY_VIDEOS': False,

    # If set to True, new Studio users won't be able to author courses unless
    # edX has explicitly added them to the course creator group.
    'ENABLE_CREATOR_GROUP': False,

    # whether to use password policy enforcement or not
    'ENFORCE_PASSWORD_POLICY': False,

    # If set to True, Studio won't restrict the set of advanced components
    # to just those pre-approved by edX
    'ALLOW_ALL_ADVANCED_COMPONENTS': False,

    # Turn off account locking if failed login attempts exceeds a limit
    'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': False,

    # Allow editing of short description in course settings in cms
    'EDITABLE_SHORT_DESCRIPTION': True,

    # Hide any Personally Identifiable Information from application logs
    'SQUELCH_PII_IN_LOGS': False,

    # Toggles the embargo functionality, which enable embargoing for particular courses
    'EMBARGO': False,

    # Toggles the embargo site functionality, which enable embargoing for the whole site
    'SITE_EMBARGOED': False,

    # Turn on/off Microsites feature
    'USE_MICROSITES': False,

    # Allow creating courses with non-ascii characters in the course id
    'ALLOW_UNICODE_COURSE_ID': False,

    # Prevent concurrent logins per user
    'PREVENT_CONCURRENT_LOGINS': False,

    # Turn off Advanced Security by default
    'ADVANCED_SECURITY': False,

    # Toggles Group Configuration editing functionality
    'ENABLE_GROUP_CONFIGURATIONS': os.environ.get('FEATURE_GROUP_CONFIGURATIONS'),

    # Modulestore to use for new courses
    'DEFAULT_STORE_FOR_NEW_COURSE': 'mongo',
}
ENABLE_JASMINE = False


############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /edx-platform/cms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
LMS_ROOT = REPO_ROOT / "lms"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /edx-platform is in

GITHUB_REPO_ROOT = ENV_ROOT / "data"

sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'lib')

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoIP.dat"
GEOIPV6_PATH = REPO_ROOT / "common/static/data/geoip/GeoIPv6.dat"

############################# WEB CONFIGURATION #############################
# This is where we stick our compiled template files.
import tempfile
MAKO_MODULE_DIR = os.path.join(tempfile.gettempdir(), 'mako_cms')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['main'] = [
    PROJECT_ROOT / 'templates',
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_js' / 'templates',
]

for namespace, template_dirs in lms.envs.common.MAKO_TEMPLATES.iteritems():
    MAKO_TEMPLATES['lms.' + namespace] = template_dirs

TEMPLATE_DIRS = MAKO_TEMPLATES['main']

EDX_ROOT_URL = ''

LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/signin'
LOGIN_URL = EDX_ROOT_URL + '/signin'


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.core.context_processors.csrf',
    'dealer.contrib.django.staff.context_processor',  # access git revision
    'contentstore.context_processors.doc_url',
)

# use the ratelimit backend to prevent brute force attacks
AUTHENTICATION_BACKENDS = (
    'ratelimitbackend.backends.RateLimitModelBackend',
)

LMS_BASE = None

# These are standard regexes for pulling out info like course_ids, usage_ids, etc.
# They are used so that URLs with deprecated-format strings still work.
from lms.envs.common import (
    COURSE_KEY_PATTERN, COURSE_ID_PATTERN, USAGE_KEY_PATTERN, ASSET_KEY_PATTERN
)

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
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'staticfiles.finders.FileSystemFinder',
    'staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'request_cache.middleware.RequestCache',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'method_override.middleware.MethodOverrideMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',
    'student.middleware.UserStandingMiddleware',
    'contentserver.middleware.StaticContentServer',
    'crum.CurrentRequestUserMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',

    # Allows us to dark-launch particular languages
    'dark_lang.middleware.DarkLangMiddleware',

    'embargo.middleware.EmbargoMiddleware',

    # Detects user-requested locale from 'accept-language' header in http request
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.transaction.TransactionMiddleware',
    # needs to run after locale middleware (or anything that modifies the request context)
    'edxmako.middleware.MakoMiddleware',

    # catches any uncaught RateLimitExceptions and returns a 403 instead of a 500
    'ratelimitbackend.middleware.RateLimitMiddleware',

    # for expiring inactive sessions
    'session_inactivity_timeout.middleware.SessionInactivityTimeout',

    # use Django built in clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Clickjacking protection can be enabled by setting this to 'DENY'
X_FRAME_OPTIONS = 'ALLOW'

############# XBlock Configuration ##########

# Import after sys.path fixup
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore import prefer_xmodules
from xmodule.x_module import XModuleMixin

# This should be moved into an XBlock Runtime/Application object
# once the responsibility of XBlock creation is moved out of modulestore - cpennington
XBLOCK_MIXINS = (LmsBlockMixin, InheritanceMixin, XModuleMixin)

# Allow any XBlock in Studio
# You should also enable the ALLOW_ALL_ADVANCED_COMPONENTS feature flag, so that
# xblocks can be added via advanced settings
XBLOCK_SELECT_FUNCTION = prefer_xmodules

############################ Modulestore Configuration ################################
MODULESTORE_BRANCH = 'draft-preferred'

############################ DJANGO_BUILTINS ################################
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False

# Site info
SITE_ID = 1
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
ADMINS = ()
MANAGERS = ADMINS

# Static content
STATIC_URL = '/static/' + git.revision + "/"
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_ROOT = ENV_ROOT / "staticfiles" / git.revision

STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
    LMS_ROOT / "static",

    # This is how you would use the textbook images locally
    # ("book", ENV_ROOT / "book_images"),
]

# Locale/Internationalization
TIME_ZONE = 'America/New_York'  # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html

LANGUAGES = lms.envs.common.LANGUAGES
USE_I18N = True
USE_L10N = True

# Localization strings (e.g. django.po) are under this directory
LOCALE_PATHS = (REPO_ROOT + '/conf/locale',)  # edx-platform/conf/locale/

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

##### EMBARGO #####
EMBARGO_SITE_REDIRECT_URL = None

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

from rooted_paths import rooted_glob

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
    'style-app': {
        'source_filenames': [
            'sass/style-app.css',
        ],
        'output_filename': 'css/cms-style-app.css',
    },
    'style-app-extend1': {
        'source_filenames': [
            'sass/style-app-extend1.css',
        ],
        'output_filename': 'css/cms-style-app-extend1.css',
    },
    'style-xmodule': {
        'source_filenames': [
            'sass/style-xmodule.css',
        ],
        'output_filename': 'css/cms-style-xmodule.css',
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

# test_order: Determines the position of this chunk of javascript on
# the jasmine test page
PIPELINE_JS = {
    'module-js': {
        'source_filenames': (
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/descriptors/js/*.js') +
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/modules/js/*.js') +
            rooted_glob(COMMON_ROOT / 'static/', 'coffee/src/discussion/*.js')
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
    "*.pyc"
    # it would be nice if we could do, for example, "**/*.scss",
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

    # Symlinks used by js-test-tool
    "xmodule_js",
    "common_static",
)

PIPELINE_YUI_BINARY = 'yui-compressor'

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
    'API': 'www.youtube.com/iframe_api',

    # URL to test YouTube availability
    'TEST_URL': 'gdata.youtube.com/feeds/api/videos/',

    # Current youtube api for requesting transcripts.
    # For example: http://video.google.com/timedtext?lang=en&v=j_jEn79vS3g.
    'TEXT_API': {
        'url': 'video.google.com/timedtext',
        'params': {
            'lang': 'en',
            'v': 'set_youtube_id_of_11_symbols_here',
        },
    },
}

############################ APPS #####################################

INSTALLED_APPS = (
    # Standard apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'djcelery',
    'south',
    'method_override',

    # Database-backed configuration
    'config_models',

    # Monitor the status of services
    'service_status',

    # Testing
    'django_nose',

    # For CMS
    'contentstore',
    'course_creators',
    'student',  # misleading name due to sharing with lms
    'course_groups',  # not used in cms (yet), but tests run

    # Tracking
    'track',
    'eventtracking.django',

    # Monitoring
    'datadog',

    # For asset pipelining
    'edxmako',
    'pipeline',
    'staticfiles',
    'static_replace',

    # comment common
    'django_comment_common',

    # for course creator table
    'django.contrib.admin',

    # for managing course modes
    'course_modes',

    # Dark-launching languages
    'dark_lang',

    # Student identity reverification
    'reverification',

    # User preferences
    'user_api',
    'django_openid_auth',

    'embargo',

    # Monitoring signals
    'monitoring',

    # Course action state
    'course_action_state',

    # Additional problem types
    'edx_jsme',    # Molecular Structure
)


################# EDX MARKETING SITE ##################################

EDXMKTG_COOKIE_NAME = 'edxloggedin'
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
    'logger': {
        'ENGINE': 'eventtracking.backends.logger.LoggerBackend',
        'OPTIONS': {
            'name': 'tracking',
            'max_event_size': TRACK_MAX_EVENT,
        }
    }
}
EVENT_TRACKING_PROCESSORS = [
    {
        'ENGINE': 'track.shim.LegacyFieldMappingProcessor'
    }
]

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

OPTIONAL_APPS = (
    'edx_jsdraw',
    'mentoring',

    # edx-ora2
    'submissions',
    'openassessment',
    'openassessment.assessment',
    'openassessment.fileupload',
    'openassessment.workflow',
    'openassessment.xblock'
)


for app_name in OPTIONAL_APPS:
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
    INSTALLED_APPS += (app_name,)

### ADVANCED_SECURITY_CONFIG
# Empty by default
ADVANCED_SECURITY_CONFIG = {}

### External auth usage -- prefixes for ENROLLMENT_DOMAIN
SHIBBOLETH_DOMAIN_PREFIX = 'shib:'
OPENID_DOMAIN_PREFIX = 'openid:'

################ ADVANCED_COMPONENT_TYPES ###############

ADVANCED_COMPONENT_TYPES = [
    'annotatable',
    'textannotation',  # module for annotating text (with annotation table)
    'videoannotation',  # module for annotating video (with annotation table)
    'imageannotation',  # module for annotating image (with annotation table)
    'word_cloud',
    'graphical_slider_tool',
    'lti',
    # XBlocks from pmitros repos are prototypes. They should not be used
    # except for edX Learning Sciences experiments on edge.edx.org without
    # further work to make them robust, maintainable, finalize data formats,
    # etc.
    'concept',  # Concept mapper. See https://github.com/pmitros/ConceptXBlock
    'done',  # Lets students mark things as done. See https://github.com/pmitros/DoneXBlock
    'audio',  # Embed an audio file. See https://github.com/pmitros/AudioXBlock
    'recommender',  # Crowdsourced recommender. Prototype by dli&pmitros. Intended for roll-out in one place in one course.
    'split_test',
    'combinedopenended',
    'peergrading',
    'notes',
]

# Specify xblocks that should be treated as advanced problems. Each entry is a tuple
# specifying the xblock name and an optional YAML template to be used.
ADVANCED_PROBLEM_TYPES = [
    {
        'component': 'openassessment',
        'boilerplate_name': None,
    }
]
