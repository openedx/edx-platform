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
import sys
import os
import tempfile
import glob2
import errno
import hashlib
from collections import defaultdict

import djcelery
from path import path

from .askbotsettings import * # this is where LIVESETTINGS_OPTIONS comes from
from .discussionsettings import *

################################### FEATURES ###################################
COURSEWARE_ENABLED = True
ASKBOT_ENABLED = False
GENERATE_RANDOM_USER_CREDENTIALS = False
PERFSTATS = False

DISCUSSION_SETTINGS = {
    'MAX_COMMENT_DEPTH': 2,
}

# Features
MITX_FEATURES = {
    'SAMPLE' : False,
    'USE_DJANGO_PIPELINE' : True,
    'DISPLAY_HISTOGRAMS_TO_STAFF' : True,
    'REROUTE_ACTIVATION_EMAIL' : False,		# nonempty string = address for all activation emails
    'DEBUG_LEVEL' : 0,				# 0 = lowest level, least verbose, 255 = max level, most verbose

    ## DO NOT SET TO True IN THIS FILE
    ## Doing so will cause all courses to be released on production
    'DISABLE_START_DATES': False,  # When True, all courses will be active, regardless of start date

    # When True, will only publicly list courses by the subdomain. Expects you
    # to define COURSE_LISTINGS, a dictionary mapping subdomains to lists of
    # course_ids (see dev_int.py for an example)
    'SUBDOMAIN_COURSE_LISTINGS' : False,

    # When True, will override certain branding with university specific values
    # Expects a SUBDOMAIN_BRANDING dictionary that maps the subdomain to the
    # university to use for branding purposes
    'SUBDOMAIN_BRANDING': False,

    'FORCE_UNIVERSITY_DOMAIN': False,	# set this to the university domain to use, as an override to HTTP_HOST
                                        # set to None to do no university selection

    'ENABLE_TEXTBOOK' : True,
    'ENABLE_DISCUSSION' : False,
    'ENABLE_DISCUSSION_SERVICE': True,

    'ENABLE_PSYCHOMETRICS': False,	# real-time psychometrics (eg item response theory analysis in instructor dashboard)

    'ENABLE_SQL_TRACKING_LOGS': False,
    'ENABLE_LMS_MIGRATION': False,
    'ENABLE_MANUAL_GIT_RELOAD': False,

    'DISABLE_LOGIN_BUTTON': False,  # used in systems where login is automatic, eg MIT SSL

    # extrernal access methods
    'ACCESS_REQUIRE_STAFF_FOR_COURSE': False,
    'AUTH_USE_OPENID': False,
    'AUTH_USE_MIT_CERTIFICATES' : False,
    'AUTH_USE_OPENID_PROVIDER': False,
}

# Used for A/B testing
DEFAULT_GROUPS = []

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

# Used with XQueue
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5 # seconds

############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /mitx/lms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /mitx is in
ASKBOT_ROOT = REPO_ROOT / "askbot"
COURSES_ROOT = ENV_ROOT / "data"

# FIXME: To support multiple courses, we should walk the courses dir at startup
DATA_DIR = COURSES_ROOT

sys.path.append(REPO_ROOT)
sys.path.append(ASKBOT_ROOT)
sys.path.append(ASKBOT_ROOT / "askbot" / "deps")
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(PROJECT_ROOT / 'lib')
sys.path.append(COMMON_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'lib')

# For Node.js

system_node_path = os.environ.get("NODE_PATH", None)
if system_node_path is None:
    system_node_path = "/usr/local/lib/node_modules"

node_paths = [COMMON_ROOT / "static/js/vendor",
              COMMON_ROOT / "static/coffee/src",
              system_node_path
              ]
NODE_PATH = ':'.join(node_paths)


############################ OpenID Provider  ##################################
OPENID_PROVIDER_TRUSTED_ROOTS = ['cs50.net', '*.cs50.net'] 

################################## MITXWEB #####################################
# This is where we stick our compiled template files. Most of the app uses Mako
# templates
MAKO_MODULE_DIR = tempfile.mkdtemp('mako')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['main'] = [PROJECT_ROOT / 'templates',
                          COMMON_ROOT / 'templates',
                          COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
                          COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates']

# This is where Django Template lookup is defined. There are a few of these
# still left lying around.
TEMPLATE_DIRS = (
    PROJECT_ROOT / "templates",
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'askbot.context.application_settings',
    'django.contrib.messages.context_processors.messages',
    #'django.core.context_processors.i18n',
    'askbot.user_messages.context_processors.user_messages',#must be before auth
    'django.contrib.auth.context_processors.auth', #this is required for admin
    'django.core.context_processors.csrf', #necessary for csrf protection
    
    # Added for django-wiki
    'django.core.context_processors.media',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'sekizai.context_processors.sekizai',
    'course_wiki.course_nav.context_processor',
)

STUDENT_FILEUPLOAD_MAX_SIZE = 4*1000*1000 # 4 MB
MAX_FILEUPLOADS_PER_INPUT = 10

# FIXME:
# We should have separate S3 staged URLs in case we need to make changes to
# these assets and test them.
LIB_URL = '/static/js/'

# Dev machines shouldn't need the book
# BOOK_URL = '/static/book/'
BOOK_URL = 'https://mitxstatic.s3.amazonaws.com/book_images/' # For AWS deploys
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

COURSE_NAME = "6.002_Spring_2012"
COURSE_NUMBER = "6.002x"
COURSE_TITLE = "Circuits and Electronics"

### Dark code. Should be enabled in local settings for devel.

ENABLE_MULTICOURSE = False     # set to False to disable multicourse display (see lib.util.views.mitxhome)
QUICKEDIT = False

WIKI_ENABLED = False

###

COURSE_DEFAULT = '6.002x_Fall_2012'
COURSE_SETTINGS =  {'6.002x_Fall_2012': {'number' : '6.002x',
                                          'title'  :  'Circuits and Electronics',
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

############################ SIGNAL HANDLERS ################################
# This is imported to register the exception signal handling that logs exceptions
import monitoring.exceptions  # noqa

############################### DJANGO BUILT-INS ###############################
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False

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
    PROJECT_ROOT / "askbot" / "skins",
]
if os.path.isdir(DATA_DIR):
    # Add the full course repo if there is no static directory
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir)
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir) and
            not os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]
    # Otherwise, add only the static directory from the course dir
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir / 'static')
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]

# Locale/Internationalization
TIME_ZONE = 'America/New_York' # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en' # http://www.i18nguy.com/unicode/language-identifiers.html
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
AWS_QUERYSTRING_EXPIRE = 10 * 365 * 24 * 60 * 60 # 10 years

################################### ASKBOT #####################################
LIVESETTINGS_OPTIONS['MITX_ROOT_URL'] = MITX_ROOT_URL
skin_settings = LIVESETTINGS_OPTIONS[1]['SETTINGS']['GENERAL_SKIN_SETTINGS']
skin_settings['SITE_FAVICON'] = unicode(MITX_ROOT_URL) + skin_settings['SITE_FAVICON']
skin_settings['SITE_LOGO_URL'] = unicode(MITX_ROOT_URL) +  skin_settings['SITE_LOGO_URL']
skin_settings['LOCAL_LOGIN_ICON'] = unicode(MITX_ROOT_URL) + skin_settings['LOCAL_LOGIN_ICON']
LIVESETTINGS_OPTIONS[1]['SETTINGS']['LOGIN_PROVIDERS']['WORDPRESS_SITE_ICON'] = unicode(MITX_ROOT_URL) + LIVESETTINGS_OPTIONS[1]['SETTINGS']['LOGIN_PROVIDERS']['WORDPRESS_SITE_ICON']
LIVESETTINGS_OPTIONS[1]['SETTINGS']['LICENSE_SETTINGS']['LICENSE_LOGO_URL'] = unicode(MITX_ROOT_URL) + LIVESETTINGS_OPTIONS[1]['SETTINGS']['LICENSE_SETTINGS']['LICENSE_LOGO_URL']

# ASKBOT_EXTRA_SKINS_DIR = ASKBOT_ROOT / "askbot" / "skins"
ASKBOT_EXTRA_SKINS_DIR =  PROJECT_ROOT / "askbot" / "skins"
ASKBOT_ALLOWED_UPLOAD_FILE_TYPES = ('.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff')
ASKBOT_MAX_UPLOAD_FILE_SIZE = 1024 * 1024 # result in bytes

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_PREFIX = SITE_ID
ASKBOT_URL = 'discussion/'
LOGIN_REDIRECT_URL = MITX_ROOT_URL + '/'
LOGIN_URL = MITX_ROOT_URL + '/'

ALLOW_UNICODE_SLUGS = False
ASKBOT_USE_STACKEXCHANGE_URLS = False # mimic url scheme of stackexchange
ASKBOT_CSS_DEVEL = True

# Celery Settings
BROKER_TRANSPORT = "djkombu.transport.DatabaseTransport"
CELERY_ALWAYS_EAGER = True
djcelery.setup_loader()

################################# SIMPLEWIKI ###################################
SIMPLE_WIKI_REQUIRE_LOGIN_EDIT = True
SIMPLE_WIKI_REQUIRE_LOGIN_VIEW = False

################################# WIKI ###################################
WIKI_ACCOUNT_HANDLING = False
WIKI_EDITOR = 'course_wiki.editors.CodeMirror'
WIKI_SHOW_MAX_CHILDREN = 0 # We don't use the little menu that shows children of an article in the breadcrumb
WIKI_ANONYMOUS = False # Don't allow anonymous access until the styling is figured out
WIKI_CAN_CHANGE_PERMISSIONS = lambda article, user: user.is_staff or user.is_superuser
WIKI_CAN_ASSIGN = lambda article, user: user.is_staff or user.is_superuser

WIKI_USE_BOOTSTRAP_SELECT_WIDGET = False
WIKI_LINK_LIVE_LOOKUPS = False
WIKI_LINK_DEFAULT_LEVEL = 2 

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
    
    #'askbot.skins.loaders.filesystem_load_template_source',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
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

    'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
    'askbot.middleware.forum_mode.ForumModeMiddleware',
    'askbot.middleware.cancel.CancelActionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'askbot.middleware.view_log.ViewLogMiddleware',
    'askbot.middleware.spaceless.SpacelessMiddleware',
    # 'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django_comment_client.utils.ViewNameMiddleware',
)

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS = {
    'application': {
        'source_filenames': ['sass/application.scss'],
        'output_filename': 'css/lms-application.css',
    },
    'course': {
      'source_filenames': ['js/vendor/CodeMirror/codemirror.css', 'css/vendor/jquery.treeview.css', 'css/vendor/ui-lightness/jquery-ui-1.8.22.custom.css', 'css/vendor/jquery.qtip.min.css', 'sass/course.scss'],
      'output_filename': 'css/lms-course.css',
      },
    'ie-fixes': {
        'source_filenames': ['sass/ie.scss'],
        'output_filename': 'css/lms-ie.css',
    },
}

PIPELINE_ALWAYS_RECOMPILE = ['sass/application.scss', 'sass/ie.scss', 'sass/course.scss']

courseware_only_js = [
    PROJECT_ROOT / 'static/coffee/src/' + pth + '.coffee'
    for pth
    in ['courseware', 'histogram', 'navigation', 'time']
]
courseware_only_js += [
    pth for pth
    in glob2.glob(PROJECT_ROOT / 'static/coffee/src/modules/**/*.coffee')
]

main_vendor_js = [
  'js/vendor/jquery.min.js',
  'js/vendor/jquery-ui.min.js',
  'js/vendor/jquery.cookie.js',
  'js/vendor/jquery.qtip.min.js',
  'js/vendor/swfobject/swfobject.js',
]

discussion_js = sorted(glob2.glob(PROJECT_ROOT / 'static/coffee/src/discussion/**/*.coffee'))

# Load javascript from all of the available xmodules, and
# prep it for use in pipeline js
from xmodule.x_module import XModuleDescriptor
from xmodule.hidden_module import HiddenDescriptor
js_file_dir = PROJECT_ROOT / "static" / "coffee" / "module"
css_file_dir = PROJECT_ROOT / "static" / "sass" / "module"
module_styles_path = css_file_dir / "_module-styles.scss"

for dir_ in (js_file_dir, css_file_dir):
    try:
        os.makedirs(dir_)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

js_fragments = set()
css_fragments = defaultdict(set)
for descriptor in XModuleDescriptor.load_classes() + [HiddenDescriptor]:
    module_js = descriptor.module_class.get_javascript()
    for filetype in ('coffee', 'js'):
        for idx, fragment in enumerate(module_js.get(filetype, [])):
            js_fragments.add((idx, filetype, fragment))

    module_css = descriptor.module_class.get_css()
    for filetype in ('sass', 'scss', 'css'):
        for idx, fragment in enumerate(module_css.get(filetype, [])):
            css_fragments[idx, filetype, fragment].add(descriptor.module_class.__name__)

module_js_sources = []
for idx, filetype, fragment in sorted(js_fragments):
    path = js_file_dir / "{idx}-{hash}.{type}".format(
        idx=idx,
        hash=hashlib.md5(fragment).hexdigest(),
        type=filetype)
    with open(path, 'w') as js_file:
        js_file.write(fragment)
    module_js_sources.append(path.replace(PROJECT_ROOT / "static/", ""))

css_imports = defaultdict(set)
for (idx, filetype, fragment), classes in sorted(css_fragments.items()):
    fragment_name = "{idx}-{hash}.{type}".format(
        idx=idx,
        hash=hashlib.md5(fragment).hexdigest(),
        type=filetype)
    # Prepend _ so that sass just includes the files into a single file
    with open(css_file_dir / '_' + fragment_name, 'w') as js_file:
        js_file.write(fragment)

    for class_ in classes:
        css_imports[class_].add(fragment_name)

with open(module_styles_path, 'w') as module_styles:
    for class_, fragment_names in css_imports.items():
        imports = "\n".join('@import "{0}";'.format(name) for name in fragment_names)
        module_styles.write(""".xmodule_{class_} {{ {imports} }}""".format(
            class_=class_, imports=imports
        ))

PIPELINE_JS = {
    'application': {
        # Application will contain all paths not in courseware_only_js
        'source_filenames': [
            pth.replace(COMMON_ROOT / 'static/', '')
            for pth
            in sorted(glob2.glob(COMMON_ROOT / 'static/coffee/src/**/*.coffee'))
        ] + [
            pth.replace(PROJECT_ROOT / 'static/', '')
            for pth in sorted(glob2.glob(PROJECT_ROOT / 'static/coffee/src/**/*.coffee'))\
            if pth not in courseware_only_js and pth not in discussion_js
        ] + [
            'js/form.ext.js',
            'js/my_courses_dropdown.js',
            'js/toggle_login_modal.js',
            'js/sticky_filter.js',
        ],
        'output_filename': 'js/lms-application.js'
    },
    'courseware': {
        'source_filenames': [pth.replace(PROJECT_ROOT / 'static/', '') for pth in courseware_only_js],
        'output_filename': 'js/lms-courseware.js'
    },
    'main_vendor': {
        'source_filenames': main_vendor_js,
        'output_filename': 'js/lms-main_vendor.js',
    },
    'module-js': {
        'source_filenames': module_js_sources,
        'output_filename': 'js/lms-modules.js',
    },
    'spec': {
        'source_filenames': [pth.replace(PROJECT_ROOT / 'static/', '') for pth in glob2.glob(PROJECT_ROOT / 'static/coffee/spec/**/*.coffee')],
        'output_filename': 'js/lms-spec.js'
    },
    'discussion' : {
        'source_filenames': [pth.replace(PROJECT_ROOT / 'static/', '')  for pth in discussion_js],
        'output_filename': 'js/discussion.js'
    }
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
                    js_timestamp     = os.stat(js_dir / new_filename).st_mtime
                    if coffee_timestamp <= js_timestamp:
                        continue
                os.system("rm %s" % (js_dir / new_filename))
                os.system("coffee -c %s" % (js_dir / filename))

PIPELINE_COMPILERS = [
    'pipeline.compilers.sass.SASSCompiler',
    'pipeline.compilers.coffee.CoffeeScriptCompiler',
]

PIPELINE_SASS_ARGUMENTS = '-t compressed -r {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None

STATICFILES_IGNORE_PATTERNS = (
    "sass/*",
    "coffee/*",
    "*.py",
    "*.pyc"
)

PIPELINE_YUI_BINARY = 'yui-compressor'
PIPELINE_SASS_BINARY = 'sass'
PIPELINE_COFFEE_SCRIPT_BINARY = 'coffee'

# Setting that will only affect the MITx version of django-pipeline until our changes are merged upstream
PIPELINE_COMPILE_INPLACE = True

################################### APPS #######################################
INSTALLED_APPS = (
    # Standard ones that are always installed...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'south',

    # For asset pipelining
    'pipeline',
    'staticfiles',

    # Our courseware
    'circuit',
    'courseware',
    'perfstats',
    'student',
    'static_template_view',
    'staticbook',
    'simplewiki',
    'track',
    'util',
    'certificates',
    'instructor',
    'psychometrics',
    
    #For the wiki
    'wiki', # The new django-wiki from benjaoming
    'django_notify',
    'course_wiki', # Our customizations
    'mptt',
    'sekizai',
    #'wiki.plugins.attachments',
    'wiki.plugins.links',
    'wiki.plugins.notifications',
    'course_wiki.plugins.markdownedx',

    # For testing
    'django_jasmine',

    # Discussion
    'django_comment_client',

    # For Askbot
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'django_countries',
    'djcelery',
    'djkombu',
    'askbot',
    'askbot.deps.livesettings',
    'followit',
    'keyedcache',
    'robots'
)
