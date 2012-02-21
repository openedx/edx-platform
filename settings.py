import os
import platform
import sys
import tempfile

import djcelery

# from settings2.askbotsettings import LIVESETTINGS_OPTIONS

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
    'keyedcache', # TODO: Main askbot tree has this installed, but we get intermittent errors if we include it. 
    'robots',
    'django_countries',
    'djcelery',
    'djkombu',
    'followit',
)

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
ASKBOT_URL = 'discussion/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'

# ASKBOT_UPLOADED_FILES_URL = '%s%s' % (ASKBOT_URL, 'upfiles/')
ALLOW_UNICODE_SLUGS = False
ASKBOT_USE_STACKEXCHANGE_URLS = False #mimic url scheme of stackexchange
ASKBOT_CSS_DEVEL = True

LIVESETTINGS_OPTIONS = {
    1: {
        'DB' : False,
        'SETTINGS' : {
            'ACCESS_CONTROL' : {
                'ASKBOT_CLOSED_FORUM_MODE' : True,
            },
            'BADGES' : {
                'DISCIPLINED_BADGE_MIN_UPVOTES' : 3,
                'PEER_PRESSURE_BADGE_MIN_DOWNVOTES' : 3,
                'TEACHER_BADGE_MIN_UPVOTES' : 1,
                'NICE_ANSWER_BADGE_MIN_UPVOTES' : 2,
                'GOOD_ANSWER_BADGE_MIN_UPVOTES' : 3,
                'GREAT_ANSWER_BADGE_MIN_UPVOTES' : 5,
                'NICE_QUESTION_BADGE_MIN_UPVOTES' : 2,
                'GOOD_QUESTION_BADGE_MIN_UPVOTES' : 3,
                'GREAT_QUESTION_BADGE_MIN_UPVOTES' : 5,
                'POPULAR_QUESTION_BADGE_MIN_VIEWS' : 150,
                'NOTABLE_QUESTION_BADGE_MIN_VIEWS' : 250,
                'FAMOUS_QUESTION_BADGE_MIN_VIEWS' : 500,
                'SELF_LEARNER_BADGE_MIN_UPVOTES' : 1,
                'CIVIC_DUTY_BADGE_MIN_VOTES' : 100,
                'ENLIGHTENED_BADGE_MIN_UPVOTES' : 3,
                'ASSOCIATE_EDITOR_BADGE_MIN_EDITS' : 20,
                'COMMENTATOR_BADGE_MIN_COMMENTS' : 10,
                'ENTHUSIAST_BADGE_MIN_DAYS' : 30,
                'FAVORITE_QUESTION_BADGE_MIN_STARS' : 3,
                'GURU_BADGE_MIN_UPVOTES' : 5,
                'NECROMANCER_BADGE_MIN_DELAY' : 30,
                'NECROMANCER_BADGE_MIN_UPVOTES' : 1,
                'STELLAR_QUESTION_BADGE_MIN_STARS' : 5,
                'TAXONOMIST_BADGE_MIN_USE_COUNT' : 10,
            },
            'EMAIL' : {
                'EMAIL_SUBJECT_PREFIX' : u'[Django] ',
                'EMAIL_UNIQUE' : True,
                'EMAIL_VALIDATION' : False,
                'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_M_AND_C' : u'w',
                'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ALL' : u'w',
                'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ANS' : u'w',
                'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ASK' : u'w',
                'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_SEL' : u'w',
                'ENABLE_UNANSWERED_REMINDERS' : False,
                'DAYS_BEFORE_SENDING_UNANSWERED_REMINDER' : 1,
                'UNANSWERED_REMINDER_FREQUENCY' : 1,
                'MAX_UNANSWERED_REMINDERS' : 5,
                'ENABLE_ACCEPT_ANSWER_REMINDERS' : False,
                'DAYS_BEFORE_SENDING_ACCEPT_ANSWER_REMINDER' : 3,
                'ACCEPT_ANSWER_REMINDER_FREQUENCY' : 3,
                'MAX_ACCEPT_ANSWER_REMINDERS' : 5,
                'ANONYMOUS_USER_EMAIL' : u'anonymous@askbot.org',
                'ALLOW_ASKING_BY_EMAIL' : False,
                'REPLACE_SPACE_WITH_DASH_IN_EMAILED_TAGS' : True,                
                'MAX_ALERTS_PER_EMAIL' : 7,
            },
            'EMBEDDABLE_WIDGETS' : {
                'QUESTIONS_WIDGET_CSS' : u"\nbody {\n    overflow: hidden;\n}\n#container {\n    width: 200px;\n    height: 350px;\n}\nul {\n    list-style: none;\n    padding: 5px;\n    margin: 5px;\n}\nli {\n    border-bottom: #CCC 1px solid;\n    padding-bottom: 5px;\n    padding-top: 5px;\n}\nli:last-child {\n    border: none;\n}\na {\n    text-decoration: none;\n    color: #464646;\n    font-family: 'Yanone Kaffeesatz', sans-serif;\n    font-size: 15px;\n}\n",
                'QUESTIONS_WIDGET_FOOTER' : u"\n<link \n    href='http://fonts.googleapis.com/css?family=Yanone+Kaffeesatz:300,400,700'\n    rel='stylesheet'\n    type='text/css'\n>\n",
                'QUESTIONS_WIDGET_HEADER' : u'',
                'QUESTIONS_WIDGET_MAX_QUESTIONS' : 7,                
            },
            'EXTERNAL_KEYS' : {
                'RECAPTCHA_KEY' : u'',
                'RECAPTCHA_SECRET' : u'',
                'FACEBOOK_KEY' : u'',
                'FACEBOOK_SECRET' : u'',
                'HOW_TO_CHANGE_LDAP_PASSWORD' : u'',
                'IDENTICA_KEY' : u'',
                'IDENTICA_SECRET' : u'',
                'GOOGLE_ANALYTICS_KEY' : u'',
                'GOOGLE_SITEMAP_CODE' : u'',
                'LDAP_PROVIDER_NAME' : u'',
                'LDAP_URL' : u'',
                'LINKEDIN_KEY' : u'',
                'LINKEDIN_SECRET' : u'',
                'TWITTER_KEY' : u'',
                'TWITTER_SECRET' : u'',
                'USE_LDAP_FOR_PASSWORD_LOGIN' : False,
                'USE_RECAPTCHA' : False,
            },
            'FLATPAGES' : {
                'FORUM_ABOUT' : u'',
                'FORUM_FAQ' : u'',
                'FORUM_PRIVACY' : u'',
            },
            'FORUM_DATA_RULES' : {
                'MIN_TITLE_LENGTH' : 1,
                'MIN_QUESTION_BODY_LENGTH' : 1,
                'MIN_ANSWER_BODY_LENGTH' : 1,
                'WIKI_ON' : True,
                'ALLOW_ASK_ANONYMOUSLY' : True,
                'ALLOW_POSTING_BEFORE_LOGGING_IN' : True,
                'ALLOW_SWAPPING_QUESTION_WITH_ANSWER' : False,
                'MAX_TAG_LENGTH' : 20,
                'MIN_TITLE_LENGTH' : 1,
                'MIN_QUESTION_BODY_LENGTH' : 1,
                'MIN_ANSWER_BODY_LENGTH' : 1,
                'MANDATORY_TAGS' : u'',
                'FORCE_LOWERCASE_TAGS' : False,
                'TAG_LIST_FORMAT' : u'list',
                'USE_WILDCARD_TAGS' : False,
                'MAX_COMMENTS_TO_SHOW' : 5,
                'MAX_COMMENT_LENGTH' : 300,
                'USE_TIME_LIMIT_TO_EDIT_COMMENT' : True,
                'MINUTES_TO_EDIT_COMMENT' : 10,
                'SAVE_COMMENT_ON_ENTER' : True,
                'MIN_SEARCH_WORD_LENGTH' : 4,
                'DECOUPLE_TEXT_QUERY_FROM_SEARCH_STATE' : False,
                'MAX_TAGS_PER_POST' : 5,
                'DEFAULT_QUESTIONS_PAGE_SIZE' : u'30',
                'UNANSWERED_QUESTION_MEANING' : u'NO_ACCEPTED_ANSWERS',

                # Enabling video requires forked version of markdown
                # pip uninstall markdown2
                # pip install -e git+git://github.com/andryuha/python-markdown2.git#egg=markdown2
                'ENABLE_VIDEO_EMBEDDING' : False,
            },
            'GENERAL_SKIN_SETTINGS' : {
                'CUSTOM_CSS' : u'',
                'CUSTOM_FOOTER' : u'',
                'CUSTOM_HEADER' : u'',
                'CUSTOM_HTML_HEAD' : u'',
                'CUSTOM_JS' : u'',
                'SITE_FAVICON' : u'/images/favicon.gif',
                'SITE_LOGO_URL' : u'/images/logo.gif',
                'SHOW_LOGO' : False,
                'LOCAL_LOGIN_ICON' : u'/images/pw-login.gif',
                'ALWAYS_SHOW_ALL_UI_FUNCTIONS' : False,
                'ASKBOT_DEFAULT_SKIN' : u'default',
                'USE_CUSTOM_HTML_HEAD' : False,
                'FOOTER_MODE' : u'default',
                'USE_CUSTOM_CSS' : False,
                'USE_CUSTOM_JS' : False,
            },
            'LEADING_SIDEBAR' : {
                'ENABLE_LEADING_SIDEBAR' : False,
                'LEADING_SIDEBAR' : u'',
            },
            'LOGIN_PROVIDERS' : {
                'PASSWORD_REGISTER_SHOW_PROVIDER_BUTTONS' : True,
                'SIGNIN_ALWAYS_SHOW_LOCAL_LOGIN' : True,
                'SIGNIN_AOL_ENABLED' : True,
                'SIGNIN_BLOGGER_ENABLED' : True,
                'SIGNIN_CLAIMID_ENABLED' : True,
                'SIGNIN_FACEBOOK_ENABLED' : True,
                'SIGNIN_FLICKR_ENABLED' : True,
                'SIGNIN_GOOGLE_ENABLED' : True,
                'SIGNIN_IDENTI.CA_ENABLED' : True,
                'SIGNIN_LINKEDIN_ENABLED' : True,
                'SIGNIN_LIVEJOURNAL_ENABLED' : True,
                'SIGNIN_LOCAL_ENABLED' : True,
                'SIGNIN_OPENID_ENABLED' : True,
                'SIGNIN_TECHNORATI_ENABLED' : True,
                'SIGNIN_TWITTER_ENABLED' : True,
                'SIGNIN_VERISIGN_ENABLED' : True,
                'SIGNIN_VIDOOP_ENABLED' : True,
                'SIGNIN_WORDPRESS_ENABLED' : True,
                'SIGNIN_WORDPRESS_SITE_ENABLED' : False,
                'SIGNIN_YAHOO_ENABLED' : True,
                'WORDPRESS_SITE_ICON' : u'/images/logo.gif',
                'WORDPRESS_SITE_URL' : '',                   
            },
            'LICENSE_SETTINGS' : {
                'LICENSE_ACRONYM' : u'cc-by-sa',
                'LICENSE_LOGO_URL' : u'/images/cc-by-sa.png',
                'LICENSE_TITLE' : u'Creative Commons Attribution Share Alike 3.0',
                'LICENSE_URL' : 'http://creativecommons.org/licenses/by-sa/3.0/legalcode',
                'LICENSE_USE_LOGO' : True,
                'LICENSE_USE_URL' : True,
                'USE_LICENSE' : True,
            },
            'MARKUP' : {
                'MARKUP_CODE_FRIENDLY' : False,
                'ENABLE_MATHJAX' : False,  # FIXME: Test with this enabled
                'MATHJAX_BASE_URL' : u'',
                'ENABLE_AUTO_LINKING' : False,
                'AUTO_LINK_PATTERNS' : u'',
                'AUTO_LINK_URLS' : u'',
            },
            'MIN_REP' : {
                'MIN_REP_TO_ACCEPT_OWN_ANSWER' : 1,
                'MIN_REP_TO_ANSWER_OWN_QUESTION' : 1,
                'MIN_REP_TO_CLOSE_OTHERS_QUESTIONS' : 100,
                'MIN_REP_TO_CLOSE_OWN_QUESTIONS' : 1,
                'MIN_REP_TO_DELETE_OTHERS_COMMENTS' : 2000,
                'MIN_REP_TO_DELETE_OTHERS_POSTS' : 5000,
                'MIN_REP_TO_EDIT_OTHERS_POSTS' : 2000,
                'MIN_REP_TO_EDIT_WIKI' : 1,
                'MIN_REP_TO_FLAG_OFFENSIVE' : 1,
                'MIN_REP_TO_HAVE_STRONG_URL' : 250,
                'MIN_REP_TO_LEAVE_COMMENTS' : 1,
                'MIN_REP_TO_LOCK_POSTS' : 4000,
                'MIN_REP_TO_REOPEN_OWN_QUESTIONS' : 1,
                'MIN_REP_TO_RETAG_OTHERS_QUESTIONS' : 1,
                'MIN_REP_TO_UPLOAD_FILES' : 1,
                'MIN_REP_TO_VIEW_OFFENSIVE_FLAGS' : 2000,
                'MIN_REP_TO_VOTE_DOWN' : 1,
                'MIN_REP_TO_VOTE_UP' : 1,
            },
            'QA_SITE_SETTINGS' : {
                'APP_COPYRIGHT' : u'Copyright Askbot, 2010-2011.',
                'APP_DESCRIPTION' : u'Open source question and answer forum written in Python and Django',
                'APP_KEYWORDS' : u'Askbot,CNPROG,forum,community',
                'APP_SHORT_NAME' : u'Askbot',
                'APP_TITLE' : u'Askbot: Open Source Q&A Forum',
                'APP_URL' : u'http://askbot.org',
                'FEEDBACK_SITE_URL' : u'',
                'ENABLE_GREETING_FOR_ANON_USER' : True,
                'GREETING_FOR_ANONYMOUS_USER' : u'First time here? Check out the FAQ!',
            },
            'REP_CHANGES' : {
                'MAX_REP_GAIN_PER_USER_PER_DAY' : 200,
                'REP_GAIN_FOR_ACCEPTING_ANSWER' : 2,
                'REP_GAIN_FOR_CANCELING_DOWNVOTE' : 1,
                'REP_GAIN_FOR_RECEIVING_ANSWER_ACCEPTANCE' : 15,
                'REP_GAIN_FOR_RECEIVING_DOWNVOTE_CANCELATION' : 2,
                'REP_GAIN_FOR_RECEIVING_UPVOTE' : 10,
                'REP_LOSS_FOR_CANCELING_ANSWER_ACCEPTANCE' : -2,
                'REP_LOSS_FOR_DOWNVOTING' : -2,
                'REP_LOSS_FOR_RECEIVING_CANCELATION_OF_ANSWER_ACCEPTANCE' : -5,
                'REP_LOSS_FOR_RECEIVING_DOWNVOTE' : -1,
                'REP_LOSS_FOR_RECEIVING_FIVE_FLAGS_PER_REVISION' : -100,
                'REP_LOSS_FOR_RECEIVING_FLAG' : -2,
                'REP_LOSS_FOR_RECEIVING_THREE_FLAGS_PER_REVISION' : -30,
                'REP_LOSS_FOR_RECEIVING_UPVOTE_CANCELATION' : -10,
            },
            'SOCIAL_SHARING' : {
                'ENABLE_SHARING_TWITTER' : False,
                'ENABLE_SHARING_FACEBOOK' : False,
                'ENABLE_SHARING_LINKEDIN' : False,
                'ENABLE_SHARING_IDENTICA' : False,
                'ENABLE_SHARING_GOOGLE' : False,
            },
            'SIDEBAR_MAIN' : {
                'SIDEBAR_MAIN_AVATAR_LIMIT' : 16,
                'SIDEBAR_MAIN_FOOTER' : u'',
                'SIDEBAR_MAIN_HEADER' : u'',
                'SIDEBAR_MAIN_SHOW_AVATARS' : True,
                'SIDEBAR_MAIN_SHOW_TAGS' : True,
                'SIDEBAR_MAIN_SHOW_TAG_SELECTOR' : True,                
            },
            'SIDEBAR_PROFILE' : {
                'SIDEBAR_PROFILE_FOOTER' : u'',
                'SIDEBAR_PROFILE_HEADER' : u'',
            },
            'SIDEBAR_QUESTION' : {
                'SIDEBAR_QUESTION_FOOTER' : u'',
                'SIDEBAR_QUESTION_HEADER' : u'',
                'SIDEBAR_QUESTION_SHOW_META' : True,
                'SIDEBAR_QUESTION_SHOW_RELATED' : True,
                'SIDEBAR_QUESTION_SHOW_TAGS' : True,
            },
            'SITE_MODES' : {
                'ACTIVATE_BOOTSTRAP_MODE' : False,
            },
            'SKIN_COUNTER_SETTINGS' : {
                
            },
            'SPAM_AND_MODERATION' : {
                'AKISMET_API_KEY' : u'',
                'USE_AKISMET' : False,
            },
            'USER_SETTINGS' : {
                'EDITABLE_SCREEN_NAME' : False,
                'EDITABLE_EMAIL' : False,
                'ALLOW_ADD_REMOVE_LOGIN_METHODS' : False,
                'ENABLE_GRAVATAR' : False,
                'GRAVATAR_TYPE' : u'identicon',
                'NAME_OF_ANONYMOUS_USER' : u'',
                'DEFAULT_AVATAR_URL' : u'/images/nophoto.png',
                'MIN_USERNAME_LENGTH' : 1,
                'ALLOW_ACCOUNT_RECOVERY_BY_EMAIL' : True,
            },
            'VOTE_RULES' : {
                'MAX_VOTES_PER_USER_PER_DAY' : 30,
                'MAX_FLAGS_PER_USER_PER_DAY' : 5,
                'MIN_DAYS_FOR_STAFF_TO_ACCEPT_ANSWER' : 7,
                'MIN_DAYS_TO_ANSWER_OWN_QUESTION' : 0,
                'MIN_FLAGS_TO_DELETE_POST' : 5,
                'MIN_FLAGS_TO_HIDE_POST' : 3,
                'MAX_DAYS_TO_CANCEL_VOTE' : 1,
                'VOTES_LEFT_WARNING_THRESHOLD' : 5,
            },
        },
    },
}

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

