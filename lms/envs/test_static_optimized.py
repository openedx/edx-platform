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

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)
