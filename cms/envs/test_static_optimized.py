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
STATIC_ROOT = (TEST_ROOT / "staticfiles" / "cms").abspath()
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

# Disable uglify when tests are running (used by build.js).
# 1. Uglify is by far the slowest part of the build process
# 2. Having full source code makes debugging tests easier for developers
os.environ['REQUIRE_BUILD_PROFILE_OPTIMIZE'] = 'none'

### Override production defaults
LMS_ROOT_URL = 'https://localhost:18000'
del AUTHORING_API_URL
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = "SET-ME-PLEASE (ex. bucket-name.s3.amazonaws.com)"
AWS_STORAGE_BUCKET_NAME = "SET-ME-PLEASE (ex. bucket-name)"
del BROKER_HEARTBEAT
del BROKER_HEARTBEAT_CHECKRATE
del BROKER_USE_SSL
del CELERY_ALWAYS_EAGER
CELERY_BROKER_HOSTNAME = "localhost"
CELERY_BROKER_PASSWORD = "celery"
CELERY_BROKER_TRANSPORT = "amqp"
CELERY_BROKER_USER = "celery"
del CELERY_RESULT_BACKEND
CHAT_COMPLETION_API = "https://example.com/chat/completion"
CHAT_COMPLETION_API_KEY = "i am a key"
del CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION
CMS_BASE = "localhost:18010"
CMS_ROOT_URL = "https://localhost:18010"
del EMAIL_FILE_PATH
INACTIVE_USER_URL = "http://localhost:18010"
LMS_BASE = "localhost:18000"
OPENAPI_CACHE_TIMEOUT = 0
del PARSE_KEYS
POLICY_CHANGE_GRADES_ROUTING_KEY = "edx.lms.core.default"
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_DOMAIN = ""
SESSION_ENGINE = "django.contrib.sessions.backends.db"
del SESSION_INACTIVITY_TIMEOUT_IN_SECONDS
SHARED_COOKIE_DOMAIN = ""
SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY = "edx.lms.core.default"
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = "edx.lms.core.default"
STATIC_ROOT_BASE = "/edx/var/edxapp/staticfiles"
STATIC_URL_BASE = "/static/"
del VIDEO_CDN_URL


########################## Derive Any Derived Settings  #######################

derive_settings(__name__)
