"""
Settings used when generating static assets for use in tests.

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.
"""

# Start with the common settings


from openedx.core.lib.derived import derive_settings
from openedx.core.lib.django_require.staticstorage import OptimizedCachedRequireJsStorage

from .common import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Use an in-memory database since this settings file is only used for updating assets
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'ATOMIC_REQUESTS': True,
    },
    'student_module_history': {
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

# Provide a dummy XQUEUE_INTERFACE setting as LMS expects it to exist on start up
XQUEUE_INTERFACE = {
    "url": "https://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

PROCTORING_BACKENDS = {
    'DEFAULT': 'mock',
    'mock': {},
    'mock_proctoring_without_rules': {},
}

######################### PIPELINE ####################################

# Use RequireJS optimized storage
STATICFILES_STORAGE = f"{OptimizedCachedRequireJsStorage.__module__}.{OptimizedCachedRequireJsStorage.__name__}"

# Revert to the default set of finders as we don't want to dynamically pick up files from the pipeline
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openedx.core.lib.xblock_pipeline.finder.XBlockPipelineFinder',
]

# Redirect to the test_root folder within the repo
TEST_ROOT = REPO_ROOT / "test_root"
LOG_DIR = (TEST_ROOT / "log").abspath()

# Store the static files under test root so that they don't overwrite existing static assets
STATIC_ROOT = (TEST_ROOT / "staticfiles" / "lms").abspath()
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

# Disable uglify when tests are running (used by build.js).
# 1. Uglify is by far the slowest part of the build process
# 2. Having full source code makes debugging tests easier for developers
os.environ['REQUIRE_BUILD_PROFILE_OPTIMIZE'] = 'none'

### Override production defaults
API_ACCESS_MANAGER_EMAIL = 'api-access@example.com'
LMS_ROOT_URL = 'https://localhost:18000'
API_ACCESS_FROM_EMAIL = "api-requests@example.com"
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = "SET-ME-PLEASE (ex. bucket-name.s3.amazonaws.com)"
AWS_STORAGE_BUCKET_NAME = "SET-ME-PLEASE (ex. bucket-name)"
BRANCH_IO_KEY = ""
del BROKER_HEARTBEAT
del BROKER_HEARTBEAT_CHECKRATE
del BROKER_USE_SSL
CELERY_BROKER_HOSTNAME = "localhost"
CELERY_BROKER_PASSWORD = "celery"
CELERY_BROKER_TRANSPORT = "amqp"
CELERY_BROKER_USER = "celery"
del CELERY_RESULT_BACKEND
CERT_QUEUE = "certificates"
CHAT_COMPLETION_API = "https://example.com/chat/completion"
CHAT_COMPLETION_API_KEY = "i am a key"
CMS_BASE = "localhost:18010"
COMMENTS_SERVICE_KEY = "password"
COMMENTS_SERVICE_URL = "http://localhost:18080"
del DASHBOARD_COURSE_LIMIT
del DEFAULT_ENTERPRISE_API_URL
del DEFAULT_ENTERPRISE_CONSENT_API_URL
EDX_API_KEY = "PUT_YOUR_API_KEY_HERE"
del EMAIL_FILE_PATH
del ENABLE_REQUIRE_THIRD_PARTY_AUTH
ENTERPRISE_API_URL = "https://localhost:18000/enterprise/api/v1"
del ENTITLEMENTS_EXPIRATION_ROUTING_KEY
FACEBOOK_API_VERSION = "v2.1"
FACEBOOK_APP_ID = "FACEBOOK_APP_ID"
FACEBOOK_APP_SECRET = "FACEBOOK_APP_SECRET"
GOOGLE_ANALYTICS_LINKEDIN = "GOOGLE_ANALYTICS_LINKEDIN_DUMMY"
GOOGLE_SITE_VERIFICATION_ID = ""
del HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS
MAINTENANCE_BANNER_TEXT = "Sample banner message"
del MONGODB_LOG
OPENAPI_CACHE_TIMEOUT = 0
del PYTHON_LIB_FILENAME
del REGISTRATION_CODE_LENGTH
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_DOMAIN = ""
SESSION_ENGINE = "django.contrib.sessions.backends.db"
del SESSION_INACTIVITY_TIMEOUT_IN_SECONDS
SHARED_COOKIE_DOMAIN = ""
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = "edx.lms.core.default"
del SSL_AUTH_DN_FORMAT_STRING
del SSL_AUTH_EMAIL_DOMAIN
STATIC_ROOT_BASE = "/edx/var/edxapp/staticfiles"
STATIC_URL_BASE = "/static/"
VIDEO_CDN_URL = {}
ZENDESK_API_KEY = ""
ZENDESK_USER = ""

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)
