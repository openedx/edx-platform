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
import os

from path import path

from .discussionsettings import *

################################### FEATURES ###################################
# The display name of the platform to be used in templates/emails/etc.
PLATFORM_NAME = "edX"

COURSEWARE_ENABLED = True
ENABLE_JASMINE = False

GENERATE_RANDOM_USER_CREDENTIALS = False
PERFSTATS = False

DISCUSSION_SETTINGS = {
    'MAX_COMMENT_DEPTH': 2,
}


# Features
MITX_FEATURES = {
    'SAMPLE': False,
    'USE_DJANGO_PIPELINE': True,
    'DISPLAY_HISTOGRAMS_TO_STAFF': True,
    'REROUTE_ACTIVATION_EMAIL': False,  # nonempty string = address for all activation emails
    'DEBUG_LEVEL': 0,  # 0 = lowest level, least verbose, 255 = max level, most verbose

    ## DO NOT SET TO True IN THIS FILE
    ## Doing so will cause all courses to be released on production
    'DISABLE_START_DATES': False,  # When True, all courses will be active, regardless of start date

    # When True, will only publicly list courses by the subdomain. Expects you
    # to define COURSE_LISTINGS, a dictionary mapping subdomains to lists of
    # course_ids (see dev_int.py for an example)
    'SUBDOMAIN_COURSE_LISTINGS': False,

    # When True, will override certain branding with university specific values
    # Expects a SUBDOMAIN_BRANDING dictionary that maps the subdomain to the
    # university to use for branding purposes
    'SUBDOMAIN_BRANDING': False,

    'FORCE_UNIVERSITY_DOMAIN': False,  # set this to the university domain to use, as an override to HTTP_HOST
                                        # set to None to do no university selection

    'ENABLE_TEXTBOOK': True,
    'ENABLE_DISCUSSION_SERVICE': True,

    'ENABLE_PSYCHOMETRICS': False,  # real-time psychometrics (eg item response theory analysis in instructor dashboard)

    'ENABLE_DJANGO_ADMIN_SITE': False,  # set true to enable django's admin site, even on prod (e.g. for course ops)
    'ENABLE_SQL_TRACKING_LOGS': False,
    'ENABLE_LMS_MIGRATION': False,
    'ENABLE_MANUAL_GIT_RELOAD': False,

    'ENABLE_MASQUERADE': True,  # allow course staff to change to student view of courseware

    'DISABLE_LOGIN_BUTTON': False,  # used in systems where login is automatic, eg MIT SSL

    'STUB_VIDEO_FOR_TESTING': False,  # do not display video when running automated acceptance tests

    # extrernal access methods
    'ACCESS_REQUIRE_STAFF_FOR_COURSE': False,
    'AUTH_USE_OPENID': False,
    'AUTH_USE_MIT_CERTIFICATES': False,
    'AUTH_USE_OPENID_PROVIDER': False,
    'AUTH_USE_SHIB': False,

    # This flag disables the requirement of having to agree to the TOS for users registering
    # with Shib.  Feature was requested by Stanford's office of general counsel
    'SHIB_DISABLE_TOS': False,
    
    # Enables ability to restrict enrollment in specific courses by the user account login method
    'RESTRICT_ENROLL_BY_REG_METHOD': False,

    # analytics experiments
    'ENABLE_INSTRUCTOR_ANALYTICS': False,

    # enable analytics server.  
    # WARNING: THIS SHOULD ALWAYS BE SET TO FALSE UNDER NORMAL
    # LMS OPERATION. See analytics.py for details about what
    # this does. 

    'RUN_AS_ANALYTICS_SERVER_ENABLED' : False, 

    # Flip to True when the YouTube iframe API breaks (again)
    'USE_YOUTUBE_OBJECT_API': False,

    # Give a UI to show a student's submission history in a problem by the
    # Staff Debug tool.
    'ENABLE_STUDENT_HISTORY_VIEW': True,

    # segment.io for LMS--need to explicitly turn it on for production.
    'SEGMENT_IO_LMS': False,

    # Enables the student notes API and UI.
    'ENABLE_STUDENT_NOTES': True,

    # Provide a UI to allow users to submit feedback from the LMS
    'ENABLE_FEEDBACK_SUBMISSION': False,

    # Turn on a page that lets staff enter Python code to be run in the
    # sandbox, for testing whether it's enabled properly.
    'ENABLE_DEBUG_RUN_PYTHON': False,

    # Enable URL that shows information about the status of variuous services
    'ENABLE_SERVICE_STATUS': False,

    # Toggle to indicate use of a custom theme
    'USE_CUSTOM_THEME': False,

    # Do autoplay videos for students
    'AUTOPLAY_VIDEOS': True,

    # Enable instructor dash to submit background tasks
    'ENABLE_INSTRUCTOR_BACKGROUND_TASKS': True,

    # Allow use of the hint managment instructor view.
    'ENABLE_HINTER_INSTRUCTOR_VIEW': False,

    # Toggle to enable chat availability (configured on a per-course
    # basis in Studio)
    'ENABLE_CHAT': False
}

# Used for A/B testing
DEFAULT_GROUPS = []

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

# Used with XQueue
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds


############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /mitx/lms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /mitx is in
COURSES_ROOT = ENV_ROOT / "data"

DATA_DIR = COURSES_ROOT

sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(PROJECT_ROOT / 'lib')
sys.path.append(COMMON_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'lib')

# For Node.js

system_node_path = os.environ.get("NODE_PATH", REPO_ROOT / 'node_modules')

node_paths = [COMMON_ROOT / "static/js/vendor",
              COMMON_ROOT / "static/coffee/src",
              system_node_path
              ]
NODE_PATH = ':'.join(node_paths)


# Where to look for a status message
STATUS_MESSAGE_PATH = ENV_ROOT / "status_message.json"

############################ OpenID Provider  ##################################
OPENID_PROVIDER_TRUSTED_ROOTS = ['cs50.net', '*.cs50.net']

################################## MITXWEB #####################################
# This is where we stick our compiled template files. Most of the app uses Mako
# templates
from tempdir import mkdtemp_clean
MAKO_MODULE_DIR = mkdtemp_clean('mako')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['main'] = [PROJECT_ROOT / 'templates',
                          COMMON_ROOT / 'templates',
                          COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
                          COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates']

# This is where Django Template lookup is defined. There are a few of these
# still left lying around.
TEMPLATE_DIRS = [
    PROJECT_ROOT / "templates",
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    #'django.core.context_processors.i18n',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.core.context_processors.csrf',  # necessary for csrf protection

    # Added for django-wiki
    'django.core.context_processors.media',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'sekizai.context_processors.sekizai',
    'course_wiki.course_nav.context_processor',

    # Hack to get required link URLs to password reset templates
    'mitxmako.shortcuts.marketing_link_context_processor',
)

STUDENT_FILEUPLOAD_MAX_SIZE = 4 * 1000 * 1000  # 4 MB
MAX_FILEUPLOADS_PER_INPUT = 20

# FIXME:
# We should have separate S3 staged URLs in case we need to make changes to
# these assets and test them.
LIB_URL = '/static/js/'

# Dev machines shouldn't need the book
# BOOK_URL = '/static/book/'
BOOK_URL = 'https://mitxstatic.s3.amazonaws.com/book_images/'  # For AWS deploys
# RSS_URL = r'lms/templates/feed.rss'
# PRESS_URL = r''
RSS_TIMEOUT = 600

# Configuration option for when we want to grab server error pages
STATIC_GRAB = False
DEV_CONTENT = True

# FIXME: Should we be doing this truncation?
TRACK_MAX_EVENT = 10000
DEBUG_TRACK_LOG = False

MITX_ROOT_URL = ''

LOGIN_REDIRECT_URL = MITX_ROOT_URL + '/accounts/login'
LOGIN_URL = MITX_ROOT_URL + '/accounts/login'

COURSE_NAME = "6.002_Spring_2012"
COURSE_NUMBER = "6.002x"
COURSE_TITLE = "Circuits and Electronics"

### Dark code. Should be enabled in local settings for devel.

ENABLE_MULTICOURSE = False  # set to False to disable multicourse display (see lib.util.views.mitxhome)

WIKI_ENABLED = False

###

COURSE_DEFAULT = '6.002x_Fall_2012'
COURSE_SETTINGS = {'6.002x_Fall_2012': {'number': '6.002x',
                                          'title': 'Circuits and Electronics',
                                          'xmlpath': '6002x/',
                                          'location': 'i4x://edx/6002xs12/course/6.002x_Fall_2012',
                                          }
                    }

# IP addresses that are allowed to reload the course, etc.
# TODO (vshnayder): Will probably need to change as we get real access control in.
LMS_MIGRATION_ALLOWED_IPS = []

######################## subdomain specific settings ###########################
COURSE_LISTINGS = {}
SUBDOMAIN_BRANDING = {}


############################### XModule Store ##################################
MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
        'OPTIONS': {
            'data_dir': DATA_DIR,
            'default_class': 'xmodule.hidden_module.HiddenDescriptor',
        }
    }
}
CONTENTSTORE = None

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
        # How large a file can jailed code write?
        'FSIZE': 50000,
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

############################ SIGNAL HANDLERS ################################
# This is imported to register the exception signal handling that logs exceptions
import monitoring.exceptions  # noqa

############################### DJANGO BUILT-INS ###############################
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False
USE_TZ = True

# Site info
SITE_ID = 1
SITE_NAME = "edx.org"
HTTPS = 'on'
ROOT_URLCONF = 'lms.urls'
IGNORABLE_404_ENDS = ('favicon.ico')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'registration@edx.org'
DEFAULT_FEEDBACK_EMAIL = 'feedback@edx.org'
SERVER_EMAIL = 'devops@edx.org'
TECH_SUPPORT_EMAIL = 'technical@edx.org'
CONTACT_EMAIL = 'info@edx.org'
BUGS_EMAIL = 'bugs@edx.org'
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
]

FAVICON_PATH = 'images/favicon.ico'

# Locale/Internationalization
TIME_ZONE = 'America/New_York'  # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en'  # http://www.i18nguy.com/unicode/language-identifiers.html
USE_I18N = True
USE_L10N = True

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

#################################### GITHUB #######################################
# gitreload is used in LMS-workflow to pull content from github
# gitreload requests are only allowed from these IP addresses, which are
# the advertised public IPs of the github WebHook servers.
# These are listed, eg at https://github.com/MITx/mitx/admin/hooks

ALLOWED_GITRELOAD_IPS = ['207.97.227.253', '50.57.128.197', '108.171.174.178']

#################################### AWS #######################################
# S3BotoStorage insists on a timeout for uploaded assets. We should make it
# permanent instead, but rather than trying to figure out exactly where that
# setting is, I'm just bumping the expiration time to something absurd (100
# years). This is only used if DEFAULT_FILE_STORAGE is overriden to use S3
# in the global settings.py
AWS_QUERYSTRING_EXPIRE = 10 * 365 * 24 * 60 * 60  # 10 years

################################# SIMPLEWIKI ###################################
SIMPLE_WIKI_REQUIRE_LOGIN_EDIT = True
SIMPLE_WIKI_REQUIRE_LOGIN_VIEW = False

################################# WIKI ###################################
WIKI_ACCOUNT_HANDLING = False
WIKI_EDITOR = 'course_wiki.editors.CodeMirror'
WIKI_SHOW_MAX_CHILDREN = 0  # We don't use the little menu that shows children of an article in the breadcrumb
WIKI_ANONYMOUS = False  # Don't allow anonymous access until the styling is figured out
WIKI_CAN_CHANGE_PERMISSIONS = lambda article, user: user.is_staff or user.is_superuser
WIKI_CAN_ASSIGN = lambda article, user: user.is_staff or user.is_superuser

WIKI_USE_BOOTSTRAP_SELECT_WIDGET = False
WIKI_LINK_LIVE_LOOKUPS = False
WIKI_LINK_DEFAULT_LEVEL = 2

################################# Pearson TestCenter config  ################

PEARSONVUE_SIGNINPAGE_URL = "https://www1.pearsonvue.com/testtaker/signin/SignInPage/EDX"
# TESTCENTER_ACCOMMODATION_REQUEST_EMAIL = "exam-help@edx.org"

##### Feedback submission mechanism #####
FEEDBACK_SUBMISSION_EMAIL = None

##### Zendesk #####
ZENDESK_URL = None
ZENDESK_USER = None
ZENDESK_API_KEY = None

################################# open ended grading config  #####################

#By setting up the default settings with an incorrect user name and password,
# will get an error when attempting to connect
OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'http://sandbox-grader-001.m.edx.org/peer_grading',
    'username': 'incorrect_user',
    'password': 'incorrect_pass',
    'staff_grading' : 'staff_grading',
    'peer_grading' : 'peer_grading',
    'grading_controller' : 'grading_controller'
    }

# Used for testing, debugging peer grading
MOCK_PEER_GRADING = False

# Used for testing, debugging staff grading
MOCK_STAFF_GRADING = False

################################# Jasmine ###################################
JASMINE_TEST_DIRECTORY = PROJECT_ROOT + '/static/coffee'

################################# Middleware ###################################
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'staticfiles.finders.FileSystemFinder',
    'staticfiles.finders.AppDirectoriesFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'mitxmako.makoloader.MakoFilesystemLoader',
    'mitxmako.makoloader.MakoAppDirectoriesLoader',

    # 'django.template.loaders.filesystem.Loader',
    # 'django.template.loaders.app_directories.Loader',

)

MIDDLEWARE_CLASSES = (
    'contentserver.middleware.StaticContentServer',
    'request_cache.middleware.RequestCache',
    'django_comment_client.middleware.AjaxExceptionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Instead of AuthenticationMiddleware, we use a cached backed version
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'mitxmako.middleware.MakoMiddleware',

    'course_wiki.course_nav.Middleware',

    'django.middleware.transaction.TransactionMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django_comment_client.utils.ViewNameMiddleware',
    'codejail.django_integration.ConfigureCodeJailMiddleware',
)

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

from rooted_paths import rooted_glob

courseware_js = (
    [
        'coffee/src/' + pth + '.js'
        for pth in ['courseware', 'histogram', 'navigation', 'time']
    ] +
    sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/modules/**/*.js'))
)

# 'js/vendor/RequireJS.js' - Require JS wrapper.
# See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
main_vendor_js = [
  'js/vendor/RequireJS.js',
  'js/vendor/json2.js',
  'js/vendor/jquery.min.js',
  'js/vendor/jquery-ui.min.js',
  'js/vendor/jquery.cookie.js',
  'js/vendor/jquery.qtip.min.js',
  'js/vendor/swfobject/swfobject.js',
  'js/vendor/jquery.ba-bbq.min.js',
  'js/vendor/annotator.min.js',
  'js/vendor/annotator.store.min.js',
  'js/vendor/annotator.tags.min.js'
]

discussion_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/discussion/**/*.js'))
staff_grading_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/staff_grading/**/*.js'))
open_ended_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/open_ended/**/*.js'))
notes_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/notes/**/*.coffee'))

PIPELINE_CSS = {
    'application': {
        'source_filenames': ['sass/application.css'],
        'output_filename': 'css/lms-application.css',
    },
    'course': {
        'source_filenames': [
            'js/vendor/CodeMirror/codemirror.css',
            'css/vendor/jquery.treeview.css',
            'css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css',
            'css/vendor/jquery.qtip.min.css',
            'css/vendor/annotator.min.css',
            'sass/course.css',
            'xmodule/modules.css',
        ],
        'output_filename': 'css/lms-course.css',
    },
    'ie-fixes': {
        'source_filenames': ['sass/ie.css'],
        'output_filename': 'css/lms-ie.css',
    },
}


# test_order: Determines the position of this chunk of javascript on
# the jasmine test page
PIPELINE_JS = {
    'application': {

        # Application will contain all paths not in courseware_only_js
        'source_filenames': sorted(
            set(rooted_glob(COMMON_ROOT / 'static', 'coffee/src/**/*.js') +
                rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/**/*.js')) -
            set(courseware_js + discussion_js + staff_grading_js + open_ended_js + notes_js)
        ) + [
            'js/form.ext.js',
            'js/my_courses_dropdown.js',
            'js/toggle_login_modal.js',
            'js/sticky_filter.js',
            'js/query-params.js',
        ],
        'output_filename': 'js/lms-application.js',

        'test_order': 1,
    },
    'courseware': {
        'source_filenames': courseware_js,
        'output_filename': 'js/lms-courseware.js',
        'test_order': 2,
    },
    'main_vendor': {
        'source_filenames': main_vendor_js,
        'output_filename': 'js/lms-main_vendor.js',
        'test_order': 0,
    },
    'module-js': {
        'source_filenames': rooted_glob(COMMON_ROOT / 'static', 'xmodule/modules/js/*.js'),
        'output_filename': 'js/lms-modules.js',
        'test_order': 3,
    },
    'discussion': {
        'source_filenames': discussion_js,
        'output_filename': 'js/discussion.js',
        'test_order': 4,
    },
    'staff_grading': {
        'source_filenames': staff_grading_js,
        'output_filename': 'js/staff_grading.js',
        'test_order': 5,
    },
    'open_ended': {
        'source_filenames': open_ended_js,
        'output_filename': 'js/open_ended.js',
        'test_order': 6,
    },
    'notes': {
        'source_filenames': notes_js,
        'output_filename': 'js/notes.js',
        'test_order': 7
    },
}

PIPELINE_DISABLE_WRAPPER = True

# Compile all coffee files in course data directories if they are out of date.
# TODO: Remove this once we move data into Mongo. This is only temporary while
# course data directories are still in use.
if os.path.isdir(DATA_DIR):
    for course_dir in os.listdir(DATA_DIR):
        js_dir = DATA_DIR / course_dir / "js"
        if not os.path.isdir(js_dir):
            continue
        for filename in os.listdir(js_dir):
            if filename.endswith('coffee'):
                new_filename = os.path.splitext(filename)[0] + ".js"
                if os.path.exists(js_dir / new_filename):
                    coffee_timestamp = os.stat(js_dir / filename).st_mtime
                    js_timestamp = os.stat(js_dir / new_filename).st_mtime
                    if coffee_timestamp <= js_timestamp:
                        continue
                os.system("rm %s" % (js_dir / new_filename))
                os.system("coffee -c %s" % (js_dir / filename))


PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None

STATICFILES_IGNORE_PATTERNS = (
    "sass/*",
    "coffee/*",
)

PIPELINE_YUI_BINARY = 'yui-compressor'

# Setting that will only affect the MITx version of django-pipeline until our changes are merged upstream
PIPELINE_COMPILE_INPLACE = True

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

################################### APPS ######################################
INSTALLED_APPS = (
    # Standard ones that are always installed...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djcelery',
    'south',

    # Monitor the status of services
    'service_status',

    # For asset pipelining
    'mitxmako',
    'pipeline',
    'staticfiles',
    'static_replace',

    # Our courseware
    'circuit',
    'courseware',
    'perfstats',
    'student',
    'static_template_view',
    'staticbook',
    'track',
    'util',
    'certificates',
    'instructor',
    'instructor_task',
    'open_ended_grading',
    'psychometrics',
    'licenses',
    'course_groups',

    # External auth (OpenID, shib)
    'external_auth',
    'django_openid_auth',

    #For the wiki
    'wiki',  # The new django-wiki from benjaoming
    'django_notify',
    'course_wiki',  # Our customizations
    'mptt',
    'sekizai',
    #'wiki.plugins.attachments',
    'wiki.plugins.links',
    'wiki.plugins.notifications',
    'course_wiki.plugins.markdownedx',

    # foldit integration
    'foldit',

    # For testing
    'django.contrib.admin',  # only used in DEBUG mode
    'debug',

    # Discussion forums
    'django_comment_client',
    'django_comment_common',
    'notes',

    # User API
    'rest_framework',
    'user_api',

    # Notification preferences setting
    'notification_prefs',
)

######################### MARKETING SITE ###############################
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

############################### THEME ################################
def enable_theme(theme_name):
    """
    Enable the settings for a custom theme, whose files should be stored
    in ENV_ROOT/themes/THEME_NAME (e.g., edx_all/themes/stanford).

    The THEME_NAME setting should be configured separately since it can't
    be set here (this function closes too early). An idiom for doing this
    is:

    THEME_NAME = "stanford"
    enable_theme(THEME_NAME)
    """
    MITX_FEATURES['USE_CUSTOM_THEME'] = True

    # Calculate the location of the theme's files
    theme_root = ENV_ROOT / "themes" / theme_name

    # Include the theme's templates in the template search paths
    TEMPLATE_DIRS.append(theme_root / 'templates')
    MAKO_TEMPLATES['main'].append(theme_root / 'templates')

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    STATICFILES_DIRS.append((u'themes/%s' % theme_name,
                             theme_root / 'static'))

