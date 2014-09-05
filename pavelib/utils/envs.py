"""
Helper functions for loading environment settings.
"""
from __future__ import print_function
import os
import sys
import json
from lazy import lazy
from path import path
import memcache

class Env(object):
    """
    Load information about the execution environment.
    """

    # Root of the git repository (edx-platform)
    REPO_ROOT = path(__file__).abspath().parent.parent.parent

    # Reports Directory
    REPORT_DIR = REPO_ROOT / 'reports'

    # Bok_choy dirs
    BOK_CHOY_DIR = REPO_ROOT / "common" / "test" / "acceptance"
    BOK_CHOY_LOG_DIR = REPO_ROOT / "test_root" / "log"
    BOK_CHOY_REPORT_DIR = REPORT_DIR / "bok_choy"
    BOK_CHOY_COVERAGERC = BOK_CHOY_DIR / ".coveragerc"

    # For the time being, stubs are used by both the bok-choy and lettuce acceptance tests
    # For this reason, the stubs package is currently located in the Django app called "terrain"
    # where other lettuce configuration is stored.
    BOK_CHOY_STUB_DIR = REPO_ROOT / "common" / "djangoapps" / "terrain"

    # Directory that videos are served from
    VIDEO_SOURCE_DIR = REPO_ROOT / "test_root" / "data" / "video"

    BOK_CHOY_SERVERS = {
        'lms': {
            'port': 8003,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_lms.log"
        },
        'cms': {
            'port': 8031,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_studio.log"
        }
    }

    BOK_CHOY_STUBS = {

        'xqueue': {
            'port': 8040,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_xqueue.log",
            'config': 'register_submission_url=http://0.0.0.0:8041/test/register_submission',
        },

        'ora': {
            'port': 8041,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_ora.log",
            'config': '',
        },

        'comments': {
            'port': 4567,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_comments.log",
        },

        'video': {
            'port': 8777,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_video_sources.log",
            'config': "root_dir={}".format(VIDEO_SOURCE_DIR),
        },

        'youtube': {
            'port': 9080,
            'log': BOK_CHOY_LOG_DIR / "bok_choy_youtube.log",
        }
    }

    # Mongo databases that will be dropped before/after the tests run
    BOK_CHOY_MONGO_DATABASE = "test"
    BOK_CHOY_CACHE = memcache.Client(['0.0.0.0:11211'], debug=0)

    # Test Ids Directory
    TEST_DIR = REPO_ROOT / ".testids"

    # Files used to run each of the js test suites
    # TODO:  Store this as a dict. Order seems to matter for some
    # reason. See issue TE-415.
    JS_TEST_ID_FILES = [
        REPO_ROOT / 'lms/static/js_test.yml',
        REPO_ROOT / 'cms/static/js_test.yml',
        REPO_ROOT / 'cms/static/js_test_squire.yml',
        REPO_ROOT / 'common/lib/xmodule/xmodule/js/js_test.yml',
        REPO_ROOT / 'common/static/js_test.yml',
    ]

    JS_TEST_ID_KEYS = [
        'lms',
        'cms',
        'cms-squire',
        'xmodule',
        'common',
    ]

    JS_REPORT_DIR = REPORT_DIR / 'javascript'

    # Directories used for common/lib/ tests
    LIB_TEST_DIRS = []
    for item in (REPO_ROOT / "common/lib").listdir():
        if (REPO_ROOT / 'common/lib' / item).isdir():
            LIB_TEST_DIRS.append(path("common/lib") / item.basename())
    LIB_TEST_DIRS.append(path("pavelib/paver_tests"))

    # Directory for i18n test reports
    I18N_REPORT_DIR = REPORT_DIR / 'i18n'

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

    @lazy
    def env_tokens(self):
        """
        Return a dict of environment settings.
        If we couldn't find the JSON file, issue a warning and return an empty dict.
        """

        # Find the env JSON file
        if self.SERVICE_VARIANT:
            env_path = self.REPO_ROOT.parent / "{service}.env.json".format(service=self.SERVICE_VARIANT)
        else:
            env_path = path("env.json").abspath()

        # If the file does not exist, here or one level up,
        # issue a warning and return an empty dict
        if not env_path.isfile():
            env_path = env_path.parent.parent / env_path.basename()
        if not env_path.isfile():
            print(
                "Warning: could not find environment JSON file "
                "at '{path}'".format(path=env_path),
                file=sys.stderr,
            )
            return dict()

        # Otherwise, load the file as JSON and return the resulting dict
        try:
            with open(env_path) as env_file:
                return json.load(env_file)

        except ValueError:
            print(
                "Error: Could not parse JSON "
                "in {path}".format(path=env_path),
                file=sys.stderr,
            )
            sys.exit(1)

    @lazy
    def feature_flags(self):
        """
        Return a dictionary of feature flags configured by the environment.
        """
        return self.env_tokens.get('FEATURES', dict())
