import os
import platform
import sys
import tempfile

import djcelery

# Configuration option for when we want to grab server error pages
STATIC_GRAB = False
DEV_CONTENT = True

LIB_URL = '/static/lib/'
LIB_URL = 'https://mitxstatic.s3.amazonaws.com/js/'
BOOK_URL = '/static/book/'
BOOK_URL = 'https://mitxstatic.s3.amazonaws.com/book_images/'

# Feature Flags. These should be set to false until they are ready to deploy, and then eventually flag mechanisms removed
GENERATE_PROFILE_SCORES = False # If this is true, random scores will be generated for the purpose of debugging the profile graphs

# Our parent dir (mitx_all) is the BASE_DIR
BASE_DIR = os.path.abspath(os.path.join(__file__, "..", ".."))

COURSEWARE_ENABLED = True
ASKBOT_ENABLED = True
CSRF_COOKIE_DOMAIN = '127.0.0.1'

# Defaults to be overridden
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SITE_NAME = "localhost:8000"

DEFAULT_FROM_EMAIL = 'registration@mitx.mit.edu'
DEFAULT_FEEDBACK_EMAIL = 'feedback@mitx.mit.edu'

GENERATE_RANDOM_USER_CREDENTIALS = False

WIKI_REQUIRE_LOGIN_EDIT = True
WIKI_REQUIRE_LOGIN_VIEW = True

PERFSTATS = False

HTTPS = 'on'

MEDIA_URL = ''
MEDIA_ROOT = ''

# S3BotoStorage insists on a timeout for uploaded assets. We should make it 
# permanent instead, but rather than trying to figure out exactly where that
# setting is, I'm just bumping the expiration time to something absurd (100 
# years). This is only used if DEFAULT_FILE_STORAGE is overriden to use S3
# in the global settings.py
AWS_QUERYSTRING_EXPIRE = 10 * 365 * 24 * 60 * 60 # 10 years

# Needed for Askbot
# Deployed machines: Move to S3
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('MITx Admins', 'admin@mitx.mit.edu'),
)

MANAGERS = ADMINS

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'mitxmako.middleware.MakoMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'mitx.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'courseware',
    'student',
    'django.contrib.humanize',
    'static_template_view',
    'staticbook',
    'simplewiki',
    'track',
    'circuit',
    'perfstats',
    'util',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

#TRACK_DIR = None
DEBUG_TRACK_LOG = False
# Maximum length of a tracking string. We don't want e.g. a file upload in our log
TRACK_MAX_EVENT = 1000 
# Maximum length of log file before starting a new one. 
MAXLOG = 500

LOG_DIR = "/tmp/"
MAKO_MODULE_DIR = None

MAKO_TEMPLATES = {}

# Make sure we execute correctly regardless of where we're called from
execfile(os.path.join(BASE_DIR, "settings.py"))

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

pid = os.getpid()
hostname = platform.node().split(".")[0]
SYSLOG_ADDRESS = ('syslog.m.i4x.org', 514)

handlers = ['console']
if not DEBUG:
    handlers.append('syslogger')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters' : {
        'standard' : {
            'format' : '%(asctime)s %(levelname)s %(process)d [%(name)s] %(filename)s:%(lineno)d - %(message)s',
        },
        'syslog_format' : {
            'format' : '[%(name)s] %(levelname)s [' + hostname + ' %(process)d] [%(filename)s:%(lineno)d] - %(message)s',
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
            'handlers' : [] if DEBUG else ['syslogger'], # handlers,
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



if PERFSTATS :
    MIDDLEWARE_CLASSES = ( 'perfstats.middleware.ProfileMiddleware',) + MIDDLEWARE_CLASSES

if 'TRACK_DIR' not in locals():
    TRACK_DIR = BASE_DIR+'/track_dir/'
if 'STATIC_ROOT' not in locals():
    STATIC_ROOT = BASE_DIR+'/staticroot/'
if 'DATA_DIR' not in locals():
    DATA_DIR = BASE_DIR+'/data/'
if 'TEXTBOOK_DIR' not in locals():
    TEXTBOOK_DIR = BASE_DIR+'/textbook/'

if 'TEMPLATE_DIRS' not in locals():
    TEMPLATE_DIRS = (
        BASE_DIR+'/templates/',
        DATA_DIR+'/templates',
        TEXTBOOK_DIR,
    )

if 'STATICFILES_DIRS' not in locals():
    STATICFILES_DIRS = (
        BASE_DIR+'/3rdParty/static',
        BASE_DIR+'/static', 
    )


if 'ASKBOT_EXTRA_SKINS_DIR' not in locals():
    ASKBOT_EXTRA_SKINS_DIR = BASE_DIR+'/askbot-devel/askbot/skins'
if 'ASKBOT_DIR' not in locals():
    ASKBOT_DIR = BASE_DIR+'/askbot-devel'

sys.path.append(ASKBOT_DIR)
import askbot
import site

STATICFILES_DIRS = STATICFILES_DIRS + ( ASKBOT_DIR+'/askbot/skins',)

ASKBOT_ROOT = os.path.dirname(askbot.__file__)

# Needed for Askbot
# Deployed machines: Move to S3
if MEDIA_ROOT == '':
    MEDIA_ROOT = ASKBOT_DIR+'/askbot/upfiles'
if MEDIA_URL == '':
    MEDIA_URL = '/discussion/upfiles/'

site.addsitedir(os.path.join(os.path.dirname(askbot.__file__), 'deps'))
TEMPLATE_LOADERS = TEMPLATE_LOADERS + ('askbot.skins.loaders.filesystem_load_template_source',)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'util.middleware.ExceptionLoggingMiddleware',
    'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
    'askbot.middleware.forum_mode.ForumModeMiddleware',
    'askbot.middleware.cancel.CancelActionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'askbot.middleware.view_log.ViewLogMiddleware',
    'askbot.middleware.spaceless.SpacelessMiddleware',
   # 'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
)

FILE_UPLOAD_TEMP_DIR = os.path.join(os.path.dirname(__file__), 'tmp').replace('\\','/')
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)
ASKBOT_ALLOWED_UPLOAD_FILE_TYPES = ('.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff')
ASKBOT_MAX_UPLOAD_FILE_SIZE = 1024 * 1024 #result in bytes
#   ASKBOT_FILE_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'askbot', 'upfiles')

PROJECT_ROOT = os.path.dirname(__file__)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'askbot.context.application_settings',
    #'django.core.context_processors.i18n',
    'askbot.user_messages.context_processors.user_messages',#must be before auth
    'django.core.context_processors.auth', #this is required for admin
    'django.core.context_processors.csrf', #necessary for csrf protection
)

INSTALLED_APPS = INSTALLED_APPS + (
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'south',
    'askbot.deps.livesettings',
    'askbot',
    #'keyedcache', # TODO: Main askbot tree has this installed, but we get intermittent errors if we include it. 
    'robots',
    'django_countries',
    'djcelery',
    'djkombu',
    'followit',
)

# askbot livesettings
LIVESETTINGS_OPTIONS = {
    1: {
        'SETTINGS' : {
            'FORUM_DATA_RULES' : {
                'MIN_TITLE_LENGTH' : 1,
                'MIN_QUESTION_BODY_LENGTH' : 1,
                'MIN_ANSWER_BODY_LENGTH' : 1,

                # 'ENABLE_VIDEO_EMBEDDING' : True,
                #
                # Enabling video requires forked version of markdown
                # pip uninstall markdown2
                # pip install -e git+git://github.com/andryuha/python-markdown2.git#egg=markdown2
            },
            'MIN_REP' : {
                'MIN_REP_TO_VOTE_UP' : 1,
                'MIN_REP_TO_VOTE_DOWN' : 1,
                'MIN_REP_TO_ANSWER_OWN_QUESTION' : 1,
                'MIN_REP_TO_ACCEPT_OWN_ANSWER' : 1,
                'MIN_REP_TO_FLAG_OFFENSIVE' : 1,
                'MIN_REP_TO_LEAVE_COMMENTS' : 1,
                'MIN_REP_TO_CLOSE_OWN_QUESTIONS' : 1,
                'MIN_REP_TO_RETAG_OTHERS_QUESTIONS' : 1,
                'MIN_REP_TO_REOPEN_OWN_QUESTIONS' : 1,
                'MIN_REP_TO_EDIT_WIKI' : 1,
                'MIN_REP_TO_CLOSE_OTHERS_QUESTIONS' : 100,
                'MIN_REP_TO_UPLOAD_FILES' : 1,
            },
            'SOCIAL_SHARING' : {
                'ENABLE_SHARING_TWITTER' : False,
                'ENABLE_SHARING_FACEBOOK' : False,
                'ENABLE_SHARING_LINKEDIN' : False,
                'ENABLE_SHARING_IDENTICA' : False,
                'ENABLE_SHARING_GOOGLE' : False,
            },
            'USER_SETTINGS' : {
                'EDITABLE_SCREEN_NAME' : False,
                'EDITABLE_EMAIL' : False,
                'ALLOW_ADD_REMOVE_LOGIN_METHODS' : False,
                'ENABLE_GRAVATAR' : False,
            }
        }
    },
}


CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
ASKBOT_URL = 'discussion/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'

# ASKBOT_UPLOADED_FILES_URL = '%s%s' % (ASKBOT_URL, 'upfiles/')
ALLOW_UNICODE_SLUGS = False
ASKBOT_USE_STACKEXCHANGE_URLS = False #mimic url scheme of stackexchange
ASKBOT_CSS_DEVEL = True

# Celery Settings
BROKER_TRANSPORT = "djkombu.transport.DatabaseTransport"
CELERY_ALWAYS_EAGER = True

ot = MAKO_TEMPLATES
MAKO_TEMPLATES['course'] = [DATA_DIR]
MAKO_TEMPLATES['sections'] = [DATA_DIR+'/sections']
MAKO_TEMPLATES['custom_tags'] = [DATA_DIR+'/custom_tags']
MAKO_TEMPLATES['main'] = [BASE_DIR+'/templates/']


MAKO_TEMPLATES.update(ot)

if MAKO_MODULE_DIR == None:
    MAKO_MODULE_DIR = tempfile.mkdtemp('mako')

djcelery.setup_loader()

