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
# pylint: disable=W0401, W0611, W0614, C0103

import sys
import os
import imp
import json

from path import path
from warnings import simplefilter

from .discussionsettings import *
from .modulestore_settings import *

from lms.lib.xblock.mixin import LmsBlockMixin

################################### FEATURES ###################################
# The display name of the platform to be used in templates/emails/etc.
PLATFORM_NAME = "Your Platform Name Here"
CC_MERCHANT_NAME = PLATFORM_NAME
PLATFORM_TWITTER_ACCOUNT = "@YourPlatformTwitterAccount"
PLATFORM_FACEBOOK_ACCOUNT = "http://www.facebook.com/YourPlatformFacebookAccount"

COURSEWARE_ENABLED = True
ENABLE_JASMINE = False

DISCUSSION_SETTINGS = {
    'MAX_COMMENT_DEPTH': 2,
}


# Features
FEATURES = {
    'SAMPLE': False,
    'USE_DJANGO_PIPELINE': True,

    'DISPLAY_DEBUG_INFO_TO_STAFF': True,
    'DISPLAY_HISTOGRAMS_TO_STAFF': False,  # For large courses this slows down courseware access for staff.

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

    # for consistency in user-experience, keep the value of the following 3 settings
    # in sync with the corresponding ones in cms/envs/common.py
    'ENABLE_DISCUSSION_SERVICE': True,
    'ENABLE_TEXTBOOK': True,
    'ENABLE_STUDENT_NOTES': True,  # enables the student notes API and UI.

    # discussion home panel, which includes a subscription on/off setting for discussion digest emails.
    # this should remain off in production until digest notifications are online.
    'ENABLE_DISCUSSION_HOME_PANEL': False,

    'ENABLE_PSYCHOMETRICS': False,  # real-time psychometrics (eg item response theory analysis in instructor dashboard)

    'ENABLE_DJANGO_ADMIN_SITE': True,  # set true to enable django's admin site, even on prod (e.g. for course ops)
    'ENABLE_SQL_TRACKING_LOGS': False,
    'ENABLE_LMS_MIGRATION': False,
    'ENABLE_MANUAL_GIT_RELOAD': False,

    'ENABLE_MASQUERADE': True,  # allow course staff to change to student view of courseware

    'ENABLE_SYSADMIN_DASHBOARD': False,  # sysadmin dashboard, to see what courses are loaded, to delete & load courses

    'DISABLE_LOGIN_BUTTON': False,  # used in systems where login is automatic, eg MIT SSL

    # extrernal access methods
    'ACCESS_REQUIRE_STAFF_FOR_COURSE': False,
    'AUTH_USE_OPENID': False,
    'AUTH_USE_CERTIFICATES': False,
    'AUTH_USE_OPENID_PROVIDER': False,
    # Even though external_auth is in common, shib assumes the LMS views / urls, so it should only be enabled
    # in LMS
    'AUTH_USE_SHIB': False,
    'AUTH_USE_CAS': False,

    # This flag disables the requirement of having to agree to the TOS for users registering
    # with Shib.  Feature was requested by Stanford's office of general counsel
    'SHIB_DISABLE_TOS': False,

    # Can be turned off if course lists need to be hidden. Effects views and templates.
    'COURSES_ARE_BROWSABLE': True,

    # Enables ability to restrict enrollment in specific courses by the user account login method
    'RESTRICT_ENROLL_BY_REG_METHOD': False,

    # Enables the LMS bulk email feature for course staff
    'ENABLE_INSTRUCTOR_EMAIL': True,
    # If True and ENABLE_INSTRUCTOR_EMAIL: Forces email to be explicitly turned on
    #   for each course via django-admin interface.
    # If False and ENABLE_INSTRUCTOR_EMAIL: Email will be turned on by default
    #   for all Mongo-backed courses.
    'REQUIRE_COURSE_EMAIL_AUTH': True,

    # Analytics experiments - shows instructor analytics tab in LMS instructor dashboard.
    # Enabling this feature depends on installation of a separate analytics server.
    'ENABLE_INSTRUCTOR_ANALYTICS': False,

    # enable analytics server.
    # WARNING: THIS SHOULD ALWAYS BE SET TO FALSE UNDER NORMAL
    # LMS OPERATION. See analytics.py for details about what
    # this does.
    'RUN_AS_ANALYTICS_SERVER_ENABLED': False,

    # Flip to True when the YouTube iframe API breaks (again)
    'USE_YOUTUBE_OBJECT_API': False,

    # Give a UI to show a student's submission history in a problem by the
    # Staff Debug tool.
    'ENABLE_STUDENT_HISTORY_VIEW': True,

    # segment.io for LMS--need to explicitly turn it on for production.
    'SEGMENT_IO_LMS': False,

    # Provide a UI to allow users to submit feedback from the LMS (left-hand help modal)
    'ENABLE_FEEDBACK_SUBMISSION': False,

    # Turn on a page that lets staff enter Python code to be run in the
    # sandbox, for testing whether it's enabled properly.
    'ENABLE_DEBUG_RUN_PYTHON': False,

    # Enable URL that shows information about the status of variuous services
    'ENABLE_SERVICE_STATUS': False,

    # Toggle to indicate use of a custom theme
    'USE_CUSTOM_THEME': False,

    # Don't autoplay videos for students
    'AUTOPLAY_VIDEOS': False,

    # Enable instructor dash to submit background tasks
    'ENABLE_INSTRUCTOR_BACKGROUND_TASKS': True,

    # Enable instructor to assign individual due dates
    'INDIVIDUAL_DUE_DATES': False,

    # Enable legacy instructor dashboard
    'ENABLE_INSTRUCTOR_LEGACY_DASHBOARD': True,
    # Is this an edX-owned domain? (used on instructor dashboard)
    'IS_EDX_DOMAIN': False,

    # Toggle to enable certificates of courses on dashboard
    'ENABLE_VERIFIED_CERTIFICATES': False,

    # Allow use of the hint managment instructor view.
    'ENABLE_HINTER_INSTRUCTOR_VIEW': False,

    # for load testing
    'AUTOMATIC_AUTH_FOR_TESTING': False,

    # Toggle to enable chat availability (configured on a per-course
    # basis in Studio)
    'ENABLE_CHAT': False,

    # Allow users to enroll with methods other than just honor code certificates
    'MULTIPLE_ENROLLMENT_ROLES': False,

    # Toggle the availability of the shopping cart page
    'ENABLE_SHOPPING_CART': False,

    # Toggle storing detailed billing information
    'STORE_BILLING_INFO': False,

    # Enable flow for payments for course registration (DIFFERENT from verified student flow)
    'ENABLE_PAID_COURSE_REGISTRATION': False,

    # Automatically approve student identity verification attempts
    'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': False,

    # Disable instructor dash buttons for downloading course data
    # when enrollment exceeds this number
    'MAX_ENROLLMENT_INSTR_BUTTONS': 200,

    # Grade calculation started from the new instructor dashboard will write
    # grades CSV files to S3 and give links for downloads.
    'ENABLE_S3_GRADE_DOWNLOADS': False,

    # whether to use password policy enforcement or not
    'ENFORCE_PASSWORD_POLICY': False,

    # Give course staff unrestricted access to grade downloads (if set to False,
    # only edX superusers can perform the downloads)
    'ALLOW_COURSE_STAFF_GRADE_DOWNLOADS': False,

    'ENABLED_PAYMENT_REPORTS': ["refund_report", "itemized_purchase_report", "university_revenue_share", "certificate_status"],

    # Turn off account locking if failed login attempts exceeds a limit
    'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': False,

    # Hide any Personally Identifiable Information from application logs
    'SQUELCH_PII_IN_LOGS': False,

    # Toggles the embargo functionality, which enable embargoing for particular courses
    'EMBARGO': False,

    # Toggles the embargo site functionality, which enable embargoing for the whole site
    'SITE_EMBARGOED': False,

    # Whether the Wiki subsystem should be accessible via the direct /wiki/ paths. Setting this to True means
    # that people can submit content and modify the Wiki in any arbitrary manner. We're leaving this as True in the
    # defaults, so that we maintain current behavior
    'ALLOW_WIKI_ROOT_ACCESS': True,

    # Turn on/off Microsites feature
    'USE_MICROSITES': False,

    # Turn on third-party auth. Disabled for now because full implementations are not yet available. Remember to syncdb
    # if you enable this; we don't create tables by default.
    'ENABLE_THIRD_PARTY_AUTH': False,

    # Toggle to enable alternate urls for marketing links
    'ENABLE_MKTG_SITE': False,

    # Prevent concurrent logins per user
    'PREVENT_CONCURRENT_LOGINS': False,

    # Turn off Advanced Security by default
    'ADVANCED_SECURITY': False,

    # Show a "Download your certificate" on the Progress page if the lowest
    # nonzero grade cutoff is met
    'SHOW_PROGRESS_SUCCESS_BUTTON': False,
}

# Used for A/B testing
DEFAULT_GROUPS = []

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

# Used with XQueue
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds


############################# SET PATH INFORMATION #############################
PROJECT_ROOT = path(__file__).abspath().dirname().dirname()  # /edx-platform/lms
REPO_ROOT = PROJECT_ROOT.dirname()
COMMON_ROOT = REPO_ROOT / "common"
ENV_ROOT = REPO_ROOT.dirname()  # virtualenv dir /edx-platform is in
COURSES_ROOT = ENV_ROOT / "data"

DATA_DIR = COURSES_ROOT

# TODO: Remove the rest of the sys.path modification here and in cms/envs/common.py
sys.path.append(REPO_ROOT)
sys.path.append(PROJECT_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'djangoapps')
sys.path.append(COMMON_ROOT / 'lib')

# For Node.js

system_node_path = os.environ.get("NODE_PATH", REPO_ROOT / 'node_modules')

node_paths = [
    COMMON_ROOT / "static/js/vendor",
    COMMON_ROOT / "static/coffee/src",
    system_node_path,
]
NODE_PATH = ':'.join(node_paths)

# For geolocation ip database
GEOIP_PATH = REPO_ROOT / "common/static/data/geoip/GeoIP.dat"


# Where to look for a status message
STATUS_MESSAGE_PATH = ENV_ROOT / "status_message.json"

############################ OpenID Provider  ##################################
OPENID_PROVIDER_TRUSTED_ROOTS = ['cs50.net', '*.cs50.net']

################################## EDX WEB #####################################
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
    'django.core.context_processors.i18n',
    'django.contrib.auth.context_processors.auth',  # this is required for admin
    'django.core.context_processors.csrf',

    # Added for django-wiki
    'django.core.context_processors.media',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'sekizai.context_processors.sekizai',

    # Hack to get required link URLs to password reset templates
    'edxmako.shortcuts.marketing_link_context_processor',

    # Shoppingcart processor (detects if request.user has a cart)
    'shoppingcart.context_processor.user_has_cart_context_processor',
)

# use the ratelimit backend to prevent brute force attacks
AUTHENTICATION_BACKENDS = (
    'ratelimitbackend.backends.RateLimitModelBackend',
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
RSS_TIMEOUT = 600

# Configuration option for when we want to grab server error pages
STATIC_GRAB = False
DEV_CONTENT = True

EDX_ROOT_URL = ''

LOGIN_REDIRECT_URL = EDX_ROOT_URL + '/accounts/login'
LOGIN_URL = EDX_ROOT_URL + '/accounts/login'

COURSE_NAME = "6.002_Spring_2012"
COURSE_NUMBER = "6.002x"
COURSE_TITLE = "Circuits and Electronics"

### Dark code. Should be enabled in local settings for devel.

ENABLE_MULTICOURSE = False  # set to False to disable multicourse display (see lib.util.views.edXhome)

WIKI_ENABLED = False

###

COURSE_DEFAULT = '6.002x_Fall_2012'
COURSE_SETTINGS = {
    '6.002x_Fall_2012': {
        'number': '6.002x',
        'title': 'Circuits and Electronics',
        'xmlpath': '6002x/',
        'location': 'i4x://edx/6002xs12/course/6.002x_Fall_2012',
    }
}

# IP addresses that are allowed to reload the course, etc.
# TODO (vshnayder): Will probably need to change as we get real access control in.
LMS_MIGRATION_ALLOWED_IPS = []

# These are standard regexes for pulling out info like course_ids, usage_ids, etc.
# They are used so that URLs with deprecated-format strings still work.
COURSE_ID_PATTERN = r'(?P<course_id>(?:[^/]+/[^/]+/[^/]+)|(?:[^/]+))'
COURSE_KEY_PATTERN = r'(?P<course_key_string>(?:[^/]+/[^/]+/[^/]+)|(?:[^/]+))'
USAGE_KEY_PATTERN = r'(?P<usage_key_string>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'
ASSET_KEY_PATTERN = r'(?P<asset_key_string>(?:/?c4x(:/)?/[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'
USAGE_ID_PATTERN = r'(?P<usage_id>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'


############################## EVENT TRACKING #################################

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

######################## GOOGLE ANALYTICS ###########################
GOOGLE_ANALYTICS_ACCOUNT = None
GOOGLE_ANALYTICS_LINKEDIN = 'GOOGLE_ANALYTICS_LINKEDIN_DUMMY'

######################## subdomain specific settings ###########################
COURSE_LISTINGS = {}
SUBDOMAIN_BRANDING = {}
VIRTUAL_UNIVERSITIES = []

############# XBlock Configuration ##########

# Import after sys.path fixup
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore import prefer_xmodules
from xmodule.x_module import XModuleMixin

# This should be moved into an XBlock Runtime/Application object
# once the responsibility of XBlock creation is moved out of modulestore - cpennington
XBLOCK_MIXINS = (LmsBlockMixin, InheritanceMixin, XModuleMixin)

# Allow any XBlock in the LMS
XBLOCK_SELECT_FUNCTION = prefer_xmodules

############# ModuleStore Configuration ##########

MODULESTORE_BRANCH = 'published-only'
CONTENTSTORE = None
DOC_STORE_CONFIG = {
    'host': 'localhost',
    'db': 'xmodule',
    'collection': 'modulestore',
}
MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
        'OPTIONS': {
            'mappings': {},
            'reference_type': 'Location',
            'stores': [
                {
                    'NAME': 'draft',
                    'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': DATA_DIR,
                        'render_template': 'edxmako.shortcuts.render_to_string',
                    }
                },
                {
                    'NAME': 'xml',
                    'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
                    'OPTIONS': {
                        'data_dir': DATA_DIR,
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                    }
                },
            ]
        }
    }
}

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
# Change DEBUG/TEMPLATE_DEBUG in your environment settings files, not here
DEBUG = False
TEMPLATE_DEBUG = False
USE_TZ = True

# CMS base
CMS_BASE = 'localhost:8001'

# Site info
SITE_ID = 1
SITE_NAME = "example.com"
HTTPS = 'on'
ROOT_URLCONF = 'lms.urls'
# NOTE: Please set ALLOWED_HOSTS to some sane value, as we do not allow the default '*'

# Platform Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'registration@example.com'
DEFAULT_FEEDBACK_EMAIL = 'feedback@example.com'
SERVER_EMAIL = 'devops@example.com'
TECH_SUPPORT_EMAIL = 'technical@example.com'
CONTACT_EMAIL = 'info@example.com'
BUGS_EMAIL = 'bugs@example.com'
UNIVERSITY_EMAIL = 'university@example.com'
PRESS_EMAIL = 'press@example.com'
ADMINS = ()
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

# Sourced from http://www.localeplanet.com/icu/ and wikipedia
LANGUAGES = (
    ('en', u'English'),
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
    ('ta', u'தமிழ்'),  # Tamil
    ('th', u'ไทย'),  # Thai
    ('tr-tr', u'Türkçe (Türkiye)'),  # Turkish (Turkey)
    ('uk', u'Українська'),  # Ukranian
    ('ur', u'اردو'),  # Urdu
    ('vi', u'Tiếng Việt'),  # Vietnamese
    ('zh-cn', u'中文 (简体)'),  # Chinese (China)
    ('zh-hk', u'中文 (香港)'),  # Chinese (Hong Kong)
    ('zh-tw', u'中文 (台灣)'),  # Chinese (Taiwan)
)

LANGUAGE_DICT = dict(LANGUAGES)

USE_I18N = True
USE_L10N = True

# Localization strings (e.g. django.po) are under this directory
LOCALE_PATHS = (REPO_ROOT + '/conf/locale',)  # edx-platform/conf/locale/
# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

#################################### GITHUB #######################################
# gitreload is used in LMS-workflow to pull content from github
# gitreload requests are only allowed from these IP addresses, which are
# the advertised public IPs of the github WebHook servers.
# These are listed, eg at https://github.com/edx/edx-platform/admin/hooks

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
ZENDESK_URL = None
ZENDESK_USER = None
ZENDESK_API_KEY = None

##### EMBARGO #####
EMBARGO_SITE_REDIRECT_URL = None

##### shoppingcart Payment #####
PAYMENT_SUPPORT_EMAIL = 'payment@example.com'
##### Using cybersource by default #####
CC_PROCESSOR = {
    'CyberSource': {
        'SHARED_SECRET': '',
        'MERCHANT_ID': '',
        'SERIAL_NUMBER': '',
        'ORDERPAGE_VERSION': '7',
        'PURCHASE_ENDPOINT': '',
    }
}
# Setting for PAID_COURSE_REGISTRATION, DOES NOT AFFECT VERIFIED STUDENTS
PAID_COURSE_REGISTRATION_CURRENCY = ['usd', '$']

# Members of this group are allowed to generate payment reports
PAYMENT_REPORT_GENERATOR_GROUP = 'shoppingcart_report_access'

################################# open ended grading config  #####################

#By setting up the default settings with an incorrect user name and password,
# will get an error when attempting to connect
OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'http://example.com/peer_grading',
    'username': 'incorrect_user',
    'password': 'incorrect_pass',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller'
}

# Used for testing, debugging peer grading
MOCK_PEER_GRADING = False

# Used for testing, debugging staff grading
MOCK_STAFF_GRADING = False

################################# Jasmine ##################################
JASMINE_TEST_DIRECTORY = PROJECT_ROOT + '/static/coffee'

################################# Deprecation warnings #####################

# Ignore deprecation warnings (so we don't clutter Jenkins builds/production)
simplefilter('ignore')

################################# Waffle ###################################

# Name prepended to cookies set by Waffle
WAFFLE_COOKIE = "waffle_flag_%s"

# Two weeks (in sec)
WAFFLE_MAX_AGE = 1209600

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
    'edxmako.makoloader.MakoFilesystemLoader',
    'edxmako.makoloader.MakoAppDirectoriesLoader',

    # 'django.template.loaders.filesystem.Loader',
    # 'django.template.loaders.app_directories.Loader',

)

MIDDLEWARE_CLASSES = (
    'request_cache.middleware.RequestCache',
    'microsite_configuration.middleware.MicrositeMiddleware',
    'django_comment_client.middleware.AjaxExceptionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Instead of AuthenticationMiddleware, we use a cached backed version
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',
    'student.middleware.UserStandingMiddleware',
    'contentserver.middleware.StaticContentServer',
    'crum.CurrentRequestUserMiddleware',

    # Adds user tags to tracking events
    # Must go before TrackMiddleware, to get the context set up
    'user_api.middleware.UserTagsEventContextMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'track.middleware.TrackMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'splash.middleware.SplashMiddleware',

    # Allows us to dark-launch particular languages
    'dark_lang.middleware.DarkLangMiddleware',
    'geoinfo.middleware.CountryMiddleware',
    'embargo.middleware.EmbargoMiddleware',

    # Allows us to set user preferences
    # should be after DarkLangMiddleware
    'lang_pref.middleware.LanguagePreferenceMiddleware',

    # Detects user-requested locale from 'accept-language' header in http request
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.transaction.TransactionMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django_comment_client.utils.ViewNameMiddleware',
    'codejail.django_integration.ConfigureCodeJailMiddleware',

    # catches any uncaught RateLimitExceptions and returns a 403 instead of a 500
    'ratelimitbackend.middleware.RateLimitMiddleware',
    # needs to run after locale middleware (or anything that modifies the request context)
    'edxmako.middleware.MakoMiddleware',

    # For A/B testing
    'waffle.middleware.WaffleMiddleware',

    # for expiring inactive sessions
    'session_inactivity_timeout.middleware.SessionInactivityTimeout',

    # use Django built in clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'course_wiki.middleware.WikiAccessMiddleware',
)

# Clickjacking protection can be enabled by setting this to 'DENY'
X_FRAME_OPTIONS = 'ALLOW'

############################### Pipeline #######################################

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

from rooted_paths import rooted_glob

courseware_js = (
    [
        'coffee/src/' + pth + '.js'
        for pth in ['courseware', 'histogram', 'navigation', 'time']
    ] +
    ['js/' + pth + '.js' for pth in ['ajax-error']] +
    sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/modules/**/*.js'))
)

main_vendor_js = [
    'js/vendor/require.js',
    'js/RequireJS-namespace-undefine.js',
    'js/vendor/json2.js',
    'js/vendor/jquery.min.js',
    'js/vendor/jquery-ui.min.js',
    'js/vendor/jquery.cookie.js',
    'js/vendor/jquery.qtip.min.js',
    'js/vendor/swfobject/swfobject.js',
    'js/vendor/jquery.ba-bbq.min.js',
    'js/vendor/ova/annotator-full.js',
    'js/vendor/ova/annotator-full-firebase-auth.js',
    'js/vendor/ova/video.dev.js',
    'js/vendor/ova/vjs.youtube.js',
    'js/vendor/ova/rangeslider.js',
    'js/vendor/ova/share-annotator.js',
    'js/vendor/ova/richText-annotator.js',
    'js/vendor/ova/reply-annotator.js',
    'js/vendor/ova/tags-annotator.js',
    'js/vendor/ova/flagging-annotator.js',
    'js/vendor/ova/diacritic-annotator.js',
    'js/vendor/ova/jquery-Watch.js',
    'js/vendor/ova/openseadragon.js',
    'js/vendor/ova/OpenSeaDragonAnnotation.js',
    'js/vendor/ova/ova.js',
    'js/vendor/ova/catch/js/catch.js',
    'js/vendor/ova/catch/js/handlebars-1.1.2.js',
    'js/vendor/URI.min.js',
]

discussion_js = sorted(rooted_glob(COMMON_ROOT / 'static', 'coffee/src/discussion/**/*.js'))
staff_grading_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/staff_grading/**/*.js'))
open_ended_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/open_ended/**/*.js'))
notes_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/notes/**/*.js'))
instructor_dash_js = sorted(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/instructor_dashboard/**/*.js'))

PIPELINE_CSS = {
    'style-vendor': {
        'source_filenames': [
            'css/vendor/font-awesome.css',
            'css/vendor/jquery.qtip.min.css',
            'css/vendor/responsive-carousel/responsive-carousel.css',
            'css/vendor/responsive-carousel/responsive-carousel.slide.css',
            'css/vendor/ova/annotator.css',
            'css/vendor/ova/edx-annotator.css',
            'css/vendor/ova/video-js.min.css',
            'css/vendor/ova/rangeslider.css',
            'css/vendor/ova/share-annotator.css',
            'css/vendor/ova/richText-annotator.css',
            'css/vendor/ova/tags-annotator.css',
            'css/vendor/ova/flagging-annotator.css',
            'css/vendor/ova/diacritic-annotator.css',
            'css/vendor/ova/ova.css',
            'js/vendor/ova/catch/css/main.css'
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
    'style-app': {
        'source_filenames': [
            'sass/application.css',
            'sass/ie.css'
        ],
        'output_filename': 'css/lms-style-app.css',
    },
    'style-app-extend1': {
        'source_filenames': [
            'sass/application-extend1.css',
        ],
        'output_filename': 'css/lms-style-app-extend1.css',
    },
    'style-app-extend2': {
        'source_filenames': [
            'sass/application-extend2.css',
        ],
        'output_filename': 'css/lms-style-app-extend2.css',
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
            'sass/course.css',
            'xmodule/modules.css',
        ],
        'output_filename': 'css/lms-style-course.css',
    },
}


common_js = set(rooted_glob(COMMON_ROOT / 'static', 'coffee/src/**/*.js')) - set(courseware_js + discussion_js + staff_grading_js + open_ended_js + notes_js + instructor_dash_js)
project_js = set(rooted_glob(PROJECT_ROOT / 'static', 'coffee/src/**/*.js')) - set(courseware_js + discussion_js + staff_grading_js + open_ended_js + notes_js + instructor_dash_js)



# test_order: Determines the position of this chunk of javascript on
# the jasmine test page
PIPELINE_JS = {
    'application': {

        # Application will contain all paths not in courseware_only_js
        'source_filenames': sorted(common_js) + sorted(project_js) + [
            'js/form.ext.js',
            'js/my_courses_dropdown.js',
            'js/toggle_login_modal.js',
            'js/sticky_filter.js',
            'js/query-params.js',
            'js/src/utility.js',
            'js/src/accessibility_tools.js',
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
    'module-descriptor-js': {
        'source_filenames': rooted_glob(COMMON_ROOT / 'static/', 'xmodule/descriptors/js/*.js'),
        'output_filename': 'js/lms-module-descriptors.js',
        'test_order': 8,
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
    'instructor_dash': {
        'source_filenames': instructor_dash_js,
        'output_filename': 'js/instructor_dash.js',
        'test_order': 9,
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

    # Symlinks used by js-test-tool
    "xmodule_js",
    "common_static",
)

PIPELINE_YUI_BINARY = 'yui-compressor'

# Setting that will only affect the edX version of django-pipeline until our changes are merged upstream
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
HIGH_MEM_QUEUE = 'edx.core.high_mem'

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_CREATE_MISSING_QUEUES = True

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {},
    HIGH_MEM_QUEUE: {},
}

# let logging work as configured:
CELERYD_HIJACK_ROOT_LOGGER = False

################################ Bulk Email ###################################

# Suffix used to construct 'from' email address for bulk emails.
# A course-specific identifier is prepended.
BULK_EMAIL_DEFAULT_FROM_EMAIL = 'no-reply@example.com'

# Parameters for breaking down course enrollment into subtasks.
BULK_EMAIL_EMAILS_PER_TASK = 100

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

# Flag to indicate if individual email addresses should be logged as they are sent
# a bulk email message.
BULK_EMAIL_LOG_SENT_EMAILS = False

# Delay in seconds to sleep between individual mail messages being sent,
# when a bulk email task is retried for rate-related reasons.  Choose this
# value depending on the number of workers that might be sending email in
# parallel, and what the SES rate is.
BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS = 0.02


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

    # Database-backed configuration
    'config_models',

    # Monitor the status of services
    'service_status',

    # For asset pipelining
    'edxmako',
    'pipeline',
    'staticfiles',
    'static_replace',

    # Our courseware
    'circuit',
    'courseware',
    'student',
    'static_template_view',
    'staticbook',
    'track',
    'eventtracking.django',
    'util',
    'certificates',
    'dashboard',
    'instructor',
    'instructor_task',
    'open_ended_grading',
    'psychometrics',
    'licenses',
    'course_groups',
    'bulk_email',

    # External auth (OpenID, shib)
    'external_auth',
    'django_openid_auth',

    # For the wiki
    'wiki',  # The new django-wiki from benjaoming
    'django_notify',
    'course_wiki',  # Our customizations
    'mptt',
    'sekizai',
    #'wiki.plugins.attachments',
    'wiki.plugins.links',
    'wiki.plugins.notifications',
    'course_wiki.plugins.markdownedx',

    # Foldit integration
    'foldit',

    # For A/B testing
    'waffle',

    # For testing
    'django.contrib.admin',  # only used in DEBUG mode
    'django_nose',
    'debug',

    # Discussion forums
    'django_comment_client',
    'django_comment_common',
    'notes',

    # Splash screen
    'splash',

    # Monitoring
    'datadog',

    # User API
    'rest_framework',
    'user_api',

    # Shopping cart
    'shoppingcart',

    # Notification preferences setting
    'notification_prefs',

    # Different Course Modes
    'course_modes',

    # Student Identity Verification
    'verify_student',

    # Dark-launching languages
    'dark_lang',

    # Microsite configuration
    'microsite_configuration',

    # Student Identity Reverification
    'reverification',

    'embargo',

    # Monitoring functionality
    'monitoring',
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
    'JOBS': 'jobs',
    'PRESS': 'press',

    # Verified Certificates
    'WHAT_IS_VERIFIED_CERT': 'verified-certificate',
}


################# Student Verification #################
VERIFY_STUDENT = {
    "DAYS_GOOD_FOR": 365,  # How many days is a verficiation good for?
}

### This enables the Metrics tab for the Instructor dashboard ###########
FEATURES['CLASS_DASHBOARD'] = False
if FEATURES.get('CLASS_DASHBOARD'):
    INSTALLED_APPS += ('class_dashboard',)

######################## CAS authentication ###########################

if FEATURES.get('AUTH_USE_CAS'):
    CAS_SERVER_URL = 'https://provide_your_cas_url_here'
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
    )
    INSTALLED_APPS += ('django_cas',)
    MIDDLEWARE_CLASSES += ('django_cas.middleware.CASMiddleware',)

###################### Registration ##################################

# For each of the fields, give one of the following values:
# - 'required': to display the field, and make it mandatory
# - 'optional': to display the field, and make it non-mandatory
# - 'hidden': to not display the field

REGISTRATION_EXTRA_FIELDS = {
    'level_of_education': 'optional',
    'gender': 'optional',
    'year_of_birth': 'optional',
    'mailing_address': 'optional',
    'goals': 'optional',
    'honor_code': 'required',
    'city': 'hidden',
    'country': 'hidden',
}

########################## CERTIFICATE NAME ########################
CERT_NAME_SHORT = "Certificate"
CERT_NAME_LONG = "Certificate of Achievement"

###################### Grade Downloads ######################
GRADES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

GRADES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': '/tmp/edx-s3/grades',
}

######################## PROGRESS SUCCESS BUTTON ##############################
# The following fields are available in the URL: {course_id} {student_id}
PROGRESS_SUCCESS_BUTTON_URL = 'http://<domain>/<path>/{course_id}'
PROGRESS_SUCCESS_BUTTON_TEXT_OVERRIDE = None

#### PASSWORD POLICY SETTINGS #####

PASSWORD_MIN_LENGTH = None
PASSWORD_MAX_LENGTH = None
PASSWORD_COMPLEXITY = {}
PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD = None
PASSWORD_DICTIONARY = []

##################### LinkedIn #####################
INSTALLED_APPS += ('django_openid_auth',)


############################ LinkedIn Integration #############################
INSTALLED_APPS += ('linkedin',)
LINKEDIN_API = {
    'EMAIL_WHITELIST': [],
    'COMPANY_ID': '2746406',
}


############################ ORA 2 ############################################

# By default, don't use a file prefix
ORA2_FILE_PREFIX = None


##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = 5
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = 15 * 60


##### LMS DEADLINE DISPLAY TIME_ZONE #######
TIME_ZONE_DISPLAYED_FOR_DEADLINES = 'UTC'


# Source:
# http://loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt according to http://en.wikipedia.org/wiki/ISO_639-1
ALL_LANGUAGES = (
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
)


### Apps only installed in some instances
OPTIONAL_APPS = (
    'edx_jsdraw',
    'mentoring',

    # edx-ora2
    'submissions',
    'openassessment',
    'openassessment.assessment',
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

# Stub for third_party_auth options.
# See common/djangoapps/third_party_auth/settings.py for configuration details.
THIRD_PARTY_AUTH = {}

### ADVANCED_SECURITY_CONFIG
# Empty by default
ADVANCED_SECURITY_CONFIG = {}
