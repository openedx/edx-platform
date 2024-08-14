"""
Helper functions for loading environment settings.
"""

# import json
import os
import sys
# import subprocess
from time import sleep

from path import Path as path
from pathlib import Path

def repo_root():
    """
    Get the root of the git repository (edx-platform).

    This sometimes fails on Docker Devstack, so it's been broken
    down with some additional error handling.  It usually starts
    working within 30 seconds or so; for more details, see
    https://openedx.atlassian.net/browse/PLAT-1629 and
    https://github.com/docker/for-mac/issues/1509
    """
    import pdb; pdb.set_trace()
    file_path = Path(__file__)
    max_attempts = 180
    for attempt in range(1, max_attempts + 1):
        try:
            absolute_path = file_path.resolve(strict=True)
            return absolute_path.parents[2]
        except OSError:
            print(f'Attempt {attempt}/{max_attempts} to get an absolute path failed')
            if attempt < max_attempts:
                sleep(1)
            else:
                print('Unable to determine the absolute path of the edx-platform repo, aborting')
                raise RuntimeError('Could not determine the repository root after multiple attempts')


class Env:
    """
    Load information about the execution environment.
    """

    # Root of the git repository (edx-platform)
    REPO_ROOT = repo_root()

    # Reports Directory
    REPORT_DIR = REPO_ROOT / 'reports'
    METRICS_DIR = REPORT_DIR / 'metrics'
    QUALITY_DIR = REPORT_DIR / 'quality_junitxml'

    # Generic log dir
    GEN_LOG_DIR = REPO_ROOT / "test_root" / "log"

    # Python unittest dirs
    PYTHON_COVERAGERC = REPO_ROOT / ".coveragerc"

    # Which Python version should be used in xdist workers?
    PYTHON_VERSION = os.environ.get("PYTHON_VERSION", "2.7")

    # Directory that videos are served from
    VIDEO_SOURCE_DIR = REPO_ROOT / "test_root" / "data" / "video"

    PRINT_SETTINGS_LOG_FILE = GEN_LOG_DIR / "print_settings.log"

    # Detect if in a Docker container, and if so which one
    FRONTEND_TEST_SERVER_HOST = os.environ.get('FRONTEND_TEST_SERVER_HOSTNAME', '0.0.0.0')
    USING_DOCKER = FRONTEND_TEST_SERVER_HOST != '0.0.0.0'
    DEVSTACK_SETTINGS = 'devstack_docker' if USING_DOCKER else 'devstack'
    TEST_SETTINGS = 'test'

    # Mongo databases that will be dropped before/after the tests run
    MONGO_HOST = 'localhost'

    # Test Ids Directory
    TEST_DIR = REPO_ROOT / ".testids"

    # Configured browser to use for the js test suites
    SELENIUM_BROWSER = os.environ.get('SELENIUM_BROWSER', 'firefox')
    if USING_DOCKER:
        KARMA_BROWSER = 'ChromeDocker' if SELENIUM_BROWSER == 'chrome' else 'FirefoxDocker'
    else:
        KARMA_BROWSER = 'FirefoxNoUpdates'

    # Files used to run each of the js test suites
    # TODO:  Store this as a dict. Order seems to matter for some
    # reason. See issue TE-415.
    KARMA_CONFIG_FILES = [
        REPO_ROOT / 'cms/static/karma_cms.conf.js',
        REPO_ROOT / 'cms/static/karma_cms_squire.conf.js',
        REPO_ROOT / 'cms/static/karma_cms_webpack.conf.js',
        REPO_ROOT / 'lms/static/karma_lms.conf.js',
        REPO_ROOT / 'xmodule/js/karma_xmodule.conf.js',
        REPO_ROOT / 'xmodule/js/karma_xmodule_webpack.conf.js',
        REPO_ROOT / 'common/static/karma_common.conf.js',
        REPO_ROOT / 'common/static/karma_common_requirejs.conf.js',
    ]

    JS_TEST_ID_KEYS = [
        'cms',
        'cms-squire',
        'cms-webpack',
        'lms',
        'xmodule',
        'xmodule-webpack',
        'common',
        'common-requirejs',
        'jest-snapshot'
    ]

    JS_REPORT_DIR = REPORT_DIR / 'javascript'

    # Directories used for pavelib/ tests
    IGNORED_TEST_DIRS = ('__pycache__', '.cache', '.pytest_cache')
    LIB_TEST_DIRS = [path("pavelib/paver_tests"), path("scripts/xsslint/tests")]

    # Directory for i18n test reports
    I18N_REPORT_DIR = REPORT_DIR / 'i18n'

    # Directory for keeping src folder that comes with pip installation.
    # Setting this is equivalent to passing `--src <dir>` to pip directly.
    PIP_SRC = os.environ.get("PIP_SRC")

    # Service variant (lms, cms, etc.) configured with an environment variable
    # We use this to determine which envs.json file to load.
    SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

    # If service variant not configured in env, then pass the correct
    # environment for lms / cms
    if not SERVICE_VARIANT:  # this will intentionally catch "";
        if any(i in sys.argv[1:] for i in ('cms', 'studio')):
            SERVICE_VARIANT = 'cms'
        else:
            SERVICE_VARIANT = 'lms'
