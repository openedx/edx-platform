"""
This is the common settings file, intended to set sane defaults. If you have a
piece of configuration that's dependent on a set of feature flags being set,
then create a function that returns the calculated value based on the value of
MITX_FEATURES[...]. Modules that extend this one can change the feature
configuration in an environment specific config file and re-calculate those
values.

We should make a method that calls all these config methods so that you just
make one call at the end of your site-specific dev file to reset all the
dependent variables (like INSTALLED_APPS) for you.

Longer TODO:
1. Right now our treatment of static content in general and in particular
   course-specific static content is haphazard.
2. We should have a more disciplined approach to feature flagging, even if it
   just means that we stick them in a dict called MITX_FEATURES.
3. We need to handle configuration for multiple courses. This could be as
   multiple sites, but we do need a way to map their data assets.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0611, W0614

import sys
import lms.envs.common
from lms.envs.common import USE_TZ
from path import path

############################ FEATURE CONFIGURATION #############################

MITX_FEATURES = {
    'USE_DJANGO_PIPELINE': True,

    'GITHUB_PUSH': False,

    'ENABLE_DISCUSSION_SERVICE': False,

    'AUTH_USE_MIT_CERTIFICATES': False,

    # do not display video when running automated acceptance tests
    'STUB_VIDEO_FOR_TESTING': False,

    # email address for studio staff (eg to request course creation)
    'STUDIO_REQUEST_EMAIL': '',

    'STUDIO_NPS_SURVEY': True,

    # Segment.io - must explicitly turn it on for production
    'SEGMENT_IO': False,

    # Enable URL that shows information about the status of various services
    'ENABLE_SERVICE_STATUS': False,

    # Don't autoplay videos for course authors
    'AUTOPLAY_VIDEOS': False,

    # If set to True, new Studio users won't be able to author courses unless
    # edX has explicitly added them to the course creator group.
    'ENABLE_CREATOR_GROUP': False
}
ENABLE_JASMINE = False


############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /mitx/cms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /mitx is in

GITHUB_REPO_ROOT = ENV_ROOT / "data"

sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(PROJECT_ROOT / 'lib')
sys.path.append(COMMON_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'lib')


############################# WEB CONFIGURATION #############################
# This is where we stick our compiled template files.
from tempdir import mkdtemp_clean
MAKO_MODULE_DIR = mkdtemp_clean('mako')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['main'] = [
    PROJECT_ROOT / 'templates',
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates'
]

for namespace, template_dirs in lms.envs.common.MAKO_TEMPLATES.iteritems():
    MAKO_TEMPLATES['lms.' + namespace] = template_dirs

TEMPLATE_DIRS = MAKO_TEMPLATES['main']

MITX_ROOT_URL = ''

LOGIN_REDIRECT_URL = MITX_ROOT_URL + '/signin'
LOGIN_URL = MITX_ROOT_URL + '/signin'


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
)

# add csrf support unless disabled for load testing
if not MITX_FEATURES.get('AUTOMATIC_AUTH_FOR_LOAD_TESTING'):
    TEMPLATE_CONTEXT_PROCESSORS += ('django.core.context_processors.csrf',)  # necessary for csrf protection

LMS_BASE = None

#################### CAPA External Code Evaluation #############################
XQUEUE_INTERFACE = {
    'url': 'http://localhost:8888',
    'django_auth': {'username': 'local',
                    'password': 'local'},
    'basic_auth': None,
}


################################# Middleware ###################################
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'staticfiles.finders.FileSystemFinder',
    'staticfiles.finders.AppDirectoriesFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'contentserver.middleware.StaticContentServer',
    'request_cache.middleware.RequestCache',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'method_override.middleware.MethodOverrideMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'mitxmako.middleware.MakoMiddleware',

    # Detects user-requested locale from 'accept-language' header in http request
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.transaction.TransactionMiddleware'
)

# add in csrf middleware unless disabled for load testing
if not MITX_FEATURES.get('AUTOMATIC_AUTH_FOR_LOAD_TESTING'):
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ('django.middleware.csrf.CsrfViewMiddleware',)

############################ SIGNAL HANDLERS ################################
# This is imported to register the exception signal handling that logs exceptions
import monitoring.exceptions  # noqa

############################ DJANGO_BUILTINS ################################
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False

# Site info
SITE_ID = 1
SITE_NAME = "localhost:8000"
HTTPS = 'on'
ROOT_URLCONF = 'cms.urls'
IGNORABLE_404_ENDS = ('favicon.ico')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'registration@edx.org'
DEFAULT_FEEDBACK_EMAIL = 'feedback@edx.org'
SERVER_EMAIL = 'devops@edx.org'
ADMINS = (
    ('edX Admins', 'admin@edx.org'),
)
MANAGERS = ADMINS

# Static content
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_ROOT = ENV_ROOT / "staticfiles"

STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",

# This is how you would use the textbook images locally
# ("book", ENV_ROOT / "book_images")
]

# Locale/Internationalization
TIME_ZONE = 'America/New_York'  # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html

USE_I18N = True
USE_L10N = True

# Localization strings (e.g. django.po) are under this directory
LOCALE_PATHS = (REPO_ROOT + '/conf/locale',)  # mitx/conf/locale/

# Tracking
TRACK_MAX_EVENT = 10000

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

from rooted_paths import rooted_glob

PIPELINE_CSS = {
    'base-style': {
        'source_filenames': [
            'js/vendor/CodeMirror/codemirror.css',
            'css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css',
            'css/vendor/jquery.qtip.min.css',
            'sass/base-style.css',
            'xmodule/modules.css',
            'xmodule/descriptor.css',
        ],
        'output_filename': 'css/cms-base-style.css',
    },
}

# test_order: Determines the position of this chunk of javascript on
# the jasmine test page
PIPELINE_JS = {
    'main': {
        'source_filenames': sorted(
            rooted_glob(COMMON_ROOT / 'static/', 'coffee/src/**/*.js') +
            rooted_glob(PROJECT_ROOT / 'static/', 'coffee/src/**/*.js')
        ) + ['js/hesitate.js', 'js/base.js', 'js/views/feedback.js',
             'js/models/section.js', 'js/views/section.js',
             'js/models/metadata_model.js', 'js/views/metadata_editor_view.js',
             'js/models/textbook.js', 'js/views/textbook.js',
             'js/views/assets.js'],
        'output_filename': 'js/cms-application.js',
        'test_order': 0
    },
    'module-js': {
        'source_filenames': (
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/descriptors/js/*.js') +
            rooted_glob(COMMON_ROOT / 'static/', 'xmodule/modules/js/*.js')
        ),
        'output_filename': 'js/cms-modules.js',
        'test_order': 1
    },
}

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None

STATICFILES_IGNORE_PATTERNS = (
    "sass/*",
    "coffee/*",
    "*.py",
    "*.pyc"
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

    # Monitor the status of services
    'service_status',

    # For CMS
    'contentstore',
    'auth',
    'course_creators',
    'student',  # misleading name due to sharing with lms
    'course_groups',  # not used in cms (yet), but tests run

    # tracking
    'track',

    # For asset pipelining
    'mitxmako',
    'pipeline',
    'staticfiles',
    'static_replace',

    # comment common
    'django_comment_common',

    # for course creator table
    'django.contrib.admin'
)

################# EDX MARKETING SITE ##################################

EDXMKTG_COOKIE_NAME = 'edxloggedin'
MKTG_URLS = {}
MKTG_URL_LINK_MAP = {
    'ABOUT': 'about_edx',
    'CONTACT': 'contact',
    'FAQ': 'help_edx',
    'COURSES': 'courses',
    'ROOT': 'root',
    'TOS': 'tos',
    'HONOR': 'honor',
    'PRIVACY': 'privacy_edx',
}

COURSES_WITH_UNSAFE_CODE = []
