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

TODO:
1. Right now our treatment of static content in general and in particular 
   course-specific static content is haphazard.
2. We should have a more disciplined approach to feature flagging, even if it
   just means that we stick them in a dict called MITX_FEATURES.
3. We need to handle configuration for multiple courses. This could be as 
   multiple sites, but we do need a way to map their data assets.
"""
import os
import platform
import sys
import tempfile

import djcelery
from path import path

from askbotsettings import LIVESETTINGS_OPTIONS

################################### FEATURES ###################################
COURSEWARE_ENABLED = True
ASKBOT_ENABLED = True
GENERATE_RANDOM_USER_CREDENTIALS = False
PERFSTATS = False

# Features
MITX_FEATURES = {
    'SAMPLE' : False
}

# Used for A/B testing
DEFAULT_GROUPS = []

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname() # /mitxweb
ENV_ROOT = PROJECT_ROOT.dirname() # virtualenv dir /mitxweb is in
ASKBOT_ROOT = ENV_ROOT / "askbot-devel"
COURSES_ROOT = ENV_ROOT / "data"

# FIXME: To support multiple courses, we should walk the courses dir at startup
DATA_DIR = COURSES_ROOT

sys.path.append(ENV_ROOT)
sys.path.append(ASKBOT_ROOT)
sys.path.append(ASKBOT_ROOT / "askbot" / "deps")
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(PROJECT_ROOT / 'lib')

################################## MITXWEB #####################################
# This is where we stick our compiled template files. Most of the app uses Mako
# templates
MAKO_MODULE_DIR = tempfile.mkdtemp('mako')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['course'] = [DATA_DIR]
MAKO_TEMPLATES['sections'] = [DATA_DIR / 'sections']
MAKO_TEMPLATES['custom_tags'] = [DATA_DIR / 'custom_tags']
MAKO_TEMPLATES['main'] = [PROJECT_ROOT / 'templates', DATA_DIR / 'info']

# This is where Django Template lookup is defined. There are a few of these 
# still left lying around.
TEMPLATE_DIRS = (
    PROJECT_ROOT / "templates",
    DATA_DIR / "templates",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'askbot.context.application_settings',
    #'django.core.context_processors.i18n',
    'askbot.user_messages.context_processors.user_messages',#must be before auth
    'django.core.context_processors.auth', #this is required for admin
    'django.core.context_processors.csrf', #necessary for csrf protection
)


# FIXME: We're not checking this out in this location yet
# TEXTBOOK_DIR = ENV_ROOT / "books" / "circuits_agarwal_lang" # What it should eventually be
TEXTBOOK_DIR = ENV_ROOT / "book_images"

# FIXME: 
# We should have separate S3 staged URLs in case we need to make changes to 
# these assets and test them.
LIB_URL = '/static/js/'
# LIB_URL = 'https://mitxstatic.s3.amazonaws.com/js/' # For AWS deploys

# Dev machines shouldn't need the book
# BOOK_URL = '/static/book/'
BOOK_URL = 'https://mitxstatic.s3.amazonaws.com/book_images/' # For AWS deploys

# Configuration option for when we want to grab server error pages
STATIC_GRAB = False
DEV_CONTENT = True

# FIXME: Should we be doing this truncation?
TRACK_MAX_EVENT = 10000 
DEBUG_TRACK_LOG = False

############################### DJANGO BUILT-INS ###############################
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False

# Site info
SITE_ID = 1
SITE_NAME = "localhost:8000"
CSRF_COOKIE_DOMAIN = '127.0.0.1'
HTTPS = 'on'
ROOT_URLCONF = 'mitx.urls'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'registration@mitx.mit.edu'
DEFAULT_FEEDBACK_EMAIL = 'feedback@mitx.mit.edu'
ADMINS = (
    ('MITx Admins', 'admin@mitx.mit.edu'),
)
MANAGERS = ADMINS

# Static content
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_ROOT = ENV_ROOT / "staticfiles" # FIXME: Should this and uploads be moved out of the repo?

# FIXME: We should iterate through the courses we have, adding the static 
#        contents for each of them. (Right now we just use symlinks.)
STATICFILES_DIRS = (
# FIXME: Need to add entries for book, data/images, etc.
    PROJECT_ROOT / "static",
    ASKBOT_ROOT / "askbot" / "skins",

# Something like this will probably need to be enabled when we're really doing
# multiple courses.
#    ("circuits", DATA_DIR / "images"),
#    ("handouts", DATA_DIR / "handouts"),
#    ("subs", DATA_DIR / "subs"),
#    ("book", TEXTBOOK_DIR)
)

# Storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = ENV_ROOT / "uploads"
MEDIA_URL = "/discussion/upfiles/"
FILE_UPLOAD_TEMP_DIR = ENV_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

# Locale/Internationalization
TIME_ZONE = 'America/New_York' # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en' # http://www.i18nguy.com/unicode/language-identifiers.html
USE_I18N = True
USE_L10N = True

################################### LOGGING ####################################
# Might want to rewrite this to use logger code and push more things to the root
# logger.
pid = os.getpid() # So we can log which process is creating the log
hostname = platform.node().split(".")[0]

LOG_DIR = "/tmp"
SYSLOG_ADDRESS = ('syslog.m.i4x.org', 514)
TRACKING_LOG_FILE = LOG_DIR + "/tracking_{0}.log".format(pid)

handlers = ['console']

# FIXME: re-enable syslogger later
# if not DEBUG:
#     handlers.append('syslogger')

LOGGING_ENV = "dev" # override this in different environments

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters' : {
        'standard' : {
            'format' : '%(asctime)s %(levelname)s %(process)d [%(name)s] %(filename)s:%(lineno)d - %(message)s',
        },
        'syslog_format' : {
            'format' : '[%(name)s][env:' + LOGGING_ENV + '] %(levelname)s [' + \
                        hostname + ' %(process)d] [%(filename)s:%(lineno)d] - %(message)s',
        },
        'raw' : {
            'format' : '%(message)s',
        }
    },
    'handlers' : {
        'console' : {
            'level' : 'DEBUG' if DEBUG else 'INFO',
            'class' : 'logging.StreamHandler',
            'formatter' : 'standard',
            'stream' : sys.stdout,
        },
        'console_err' : {
            'level' : 'ERROR',
            'class' : 'logging.StreamHandler',
            'formatter' : 'standard',
            'stream' : sys.stderr,
        },
        'syslogger' : {
            'level' : 'INFO',
            'class' : 'logging.handlers.SysLogHandler',
            'address' : SYSLOG_ADDRESS,
            'formatter' : 'syslog_format',
        },
        'tracking' : {
            'level' : 'DEBUG',
            'class' : 'logging.handlers.WatchedFileHandler',
            'filename' : TRACKING_LOG_FILE,
            'formatter' : 'raw',
        },
        'mail_admins' : {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers' : {
        'django' : {
            'handlers' : handlers + ['mail_admins'],
            'propagate' : True,
            'level' : 'INFO'
        },
        'tracking' : {
            'handlers' : ['tracking'],
            'level' : 'DEBUG',
            'propagate' : False,
        },
        'root' : {
            'handlers' : handlers,
            'level' : 'DEBUG',
            'propagate' : False
        },
        'mitx' : {
            'handlers' : handlers,
            'level' : 'DEBUG',
            'propagate' : False
        },
    }
}

#################################### AWS #######################################
# S3BotoStorage insists on a timeout for uploaded assets. We should make it 
# permanent instead, but rather than trying to figure out exactly where that
# setting is, I'm just bumping the expiration time to something absurd (100 
# years). This is only used if DEFAULT_FILE_STORAGE is overriden to use S3
# in the global settings.py
AWS_QUERYSTRING_EXPIRE = 10 * 365 * 24 * 60 * 60 # 10 years

################################### ASKBOT #####################################
ASKBOT_EXTRA_SKINS_DIR = ASKBOT_ROOT / "askbot" / "skins"
ASKBOT_ALLOWED_UPLOAD_FILE_TYPES = ('.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff')
ASKBOT_MAX_UPLOAD_FILE_SIZE = 1024 * 1024 # result in bytes

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
ASKBOT_URL = 'discussion/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'

ALLOW_UNICODE_SLUGS = False
ASKBOT_USE_STACKEXCHANGE_URLS = False # mimic url scheme of stackexchange
ASKBOT_CSS_DEVEL = True

# Celery Settings
BROKER_TRANSPORT = "djkombu.transport.DatabaseTransport"
CELERY_ALWAYS_EAGER = True
djcelery.setup_loader()

################################# SIMPLEWIKI ###################################
WIKI_REQUIRE_LOGIN_EDIT = True
WIKI_REQUIRE_LOGIN_VIEW = True

################################# Middleware ###################################
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'askbot.skins.loaders.filesystem_load_template_source',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'util.middleware.ExceptionLoggingMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'mitxmako.middleware.MakoMiddleware',

    'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
    'askbot.middleware.forum_mode.ForumModeMiddleware',
    'askbot.middleware.cancel.CancelActionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'askbot.middleware.view_log.ViewLogMiddleware',
    'askbot.middleware.spaceless.SpacelessMiddleware',
    # 'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

################################### APPS #######################################
def installed_apps(extras=()):
    """If you want to get a different set of INSTALLED_APPS out of this, you'll
    have to set ASKBOT_ENABLED and COURSEWARE_ENABLED to True/False and call 
    this method. We can't just take these as params because other pieces of the
    code check fo the value of these constants.
    """
    # We always install these
    STANDARD_APPS = ['django.contrib.auth',
                     'django.contrib.contenttypes',
                     'django.contrib.humanize',
                     'django.contrib.sessions',
                     'django.contrib.sites',
                     'django.contrib.messages',
                     'django.contrib.staticfiles',
                     'track',
                     'util']
    COURSEWARE_APPS = ['circuit',
                       'courseware',
                       'student',
                       'static_template_view',
                       'staticbook',
                       'simplewiki',
                       'perfstats']
    ASKBOT_APPS = ['django.contrib.sitemaps',
                   'django.contrib.admin',
                   'south',
                   'askbot.deps.livesettings',
                   'askbot',
                   'keyedcache',
                   'robots',
                   'django_countries',
                   'djcelery',
                   'djkombu',
                   'followit']
    
    return tuple(STANDARD_APPS + 
                 (COURSEWARE_APPS if COURSEWARE_ENABLED else []) +
                 (ASKBOT_APPS if ASKBOT_ENABLED else []) + 
                 list(extras))

INSTALLED_APPS = installed_apps()
