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
import tempfile
import os.path
import os
import errno
import glob2
import lms.envs.common
import hashlib
from collections import defaultdict
from path import path

############################ FEATURE CONFIGURATION #############################

MITX_FEATURES = {
    'USE_DJANGO_PIPELINE': True,
    'GITHUB_PUSH': False,
    'ENABLE_DISCUSSION_SERVICE': False
}

# needed to use lms student app
GENERATE_RANDOM_USER_CREDENTIALS = False


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
MAKO_MODULE_DIR = tempfile.mkdtemp('mako')
MAKO_TEMPLATES = {}
MAKO_TEMPLATES['main'] = [
    PROJECT_ROOT / 'templates',
    COMMON_ROOT / 'templates',
    COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates'
]

for namespace, template_dirs in lms.envs.common.MAKO_TEMPLATES.iteritems():
    MAKO_TEMPLATES['lms.' + namespace] = template_dirs

TEMPLATE_DIRS = (
    PROJECT_ROOT / "templates",
)

MITX_ROOT_URL = ''

LOGIN_REDIRECT_URL = MITX_ROOT_URL + '/login'
LOGIN_URL = MITX_ROOT_URL + '/login'


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.core.context_processors.csrf',  # necessary for csrf protection
)

LMS_BASE = None

################################# Jasmine ###################################
JASMINE_TEST_DIRECTORY = PROJECT_ROOT + '/static/coffee'


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
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Instead of AuthenticationMiddleware, we use a cache-backed version
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'mitxmako.middleware.MakoMiddleware',

    'django.middleware.transaction.TransactionMiddleware'
)

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
#    ("book", ENV_ROOT / "book_images")
]
if os.path.isdir(GITHUB_REPO_ROOT):
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses aren't loaded from github, remove this
        (course_dir, GITHUB_REPO_ROOT / course_dir)
        for course_dir in os.listdir(GITHUB_REPO_ROOT)
        if os.path.isdir(GITHUB_REPO_ROOT / course_dir)
    ]

# Locale/Internationalization
TIME_ZONE = 'America/New_York'  # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en'            # http://www.i18nguy.com/unicode/language-identifiers.html
USE_I18N = True
USE_L10N = True

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# Load javascript and css from all of the available descriptors, and
# prep it for use in pipeline js
from xmodule.x_module import XModuleDescriptor
from xmodule.raw_module import RawDescriptor
from xmodule.error_module import ErrorDescriptor
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
for _, descriptor in XModuleDescriptor.load_classes() + [(None, RawDescriptor), (None, ErrorDescriptor)]:
    descriptor_js = descriptor.get_javascript()
    module_js = descriptor.module_class.get_javascript()

    for filetype in ('coffee', 'js'):
        for idx, fragment in enumerate(descriptor_js.get(filetype, []) + module_js.get(filetype, [])):
            js_fragments.add((idx, filetype, fragment))

    for class_ in (descriptor, descriptor.module_class):
        fragments = class_.get_css()
        for filetype in ('sass', 'scss', 'css'):
            for idx, fragment in enumerate(fragments.get(filetype, [])):
                css_fragments[idx, filetype, fragment].add(class_.__name__)

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

PIPELINE_CSS = {
    'base-style': {
        'source_filenames': ['sass/base-style.scss'],
        'output_filename': 'css/cms-base-style.css',
    },
}

PIPELINE_ALWAYS_RECOMPILE = ['sass/base-style.scss']

PIPELINE_JS = {
    'main': {
        'source_filenames': [
            pth.replace(COMMON_ROOT / 'static/', '')
            for pth
            in glob2.glob(COMMON_ROOT / 'static/coffee/src/**/*.coffee')
        ] + [
            pth.replace(PROJECT_ROOT / 'static/', '')
            for pth
            in glob2.glob(PROJECT_ROOT / 'static/coffee/src/**/*.coffee')
        ],
        'output_filename': 'js/cms-application.js',
    },
    'module-js': {
        'source_filenames': module_js_sources,
        'output_filename': 'js/cms-modules.js',
    },
    'spec': {
        'source_filenames': [pth.replace(PROJECT_ROOT / 'static/', '') for pth in glob2.glob(PROJECT_ROOT / 'static/coffee/spec/**/*.coffee')],
        'output_filename': 'js/cms-spec.js'
    }
}

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

############################ APPS #####################################

INSTALLED_APPS = (
    # Standard apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'south',

    # For CMS
    'contentstore',
    'github_sync',
    'student',  # misleading name due to sharing with lms

    # For asset pipelining
    'pipeline',
    'staticfiles',

    # For testing
    'django_jasmine',
)
