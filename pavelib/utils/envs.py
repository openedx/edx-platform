"""
Helper functions for loading environment settings.
"""
import configparser
import json
import os
import sys
from time import sleep

import memcache
from lazy import lazy
from path import Path as path
from paver.easy import BuildFailure, sh

from pavelib.utils.cmd import django_cmd


def repo_root():
    """
    Get the root of the git repository (edx-platform).

    This sometimes fails on Docker Devstack, so it's been broken
    down with some additional error handling.  It usually starts
    working within 30 seconds or so; for more details, see
    https://openedx.atlassian.net/browse/PLAT-1629 and
    https://github.com/docker/for-mac/issues/1509
    """
    file_path = path(__file__)
    attempt = 1
    while True:
        try:
            absolute_path = file_path.abspath()
            break
        except OSError:
            print(f'Attempt {attempt}/180 to get an absolute path failed')
            if attempt < 180:
                attempt += 1
                sleep(1)
            else:
                print('Unable to determine the absolute path of the edx-platform repo, aborting')
                raise
    return absolute_path.parent.parent.parent


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

    @classmethod
    def get_django_settings(cls, django_settings, system, settings=None, print_setting_args=None):
        """
        Interrogate Django environment for specific settings values
        :param django_settings: list of django settings values to get
        :param system: the django app to use when asking for the setting (lms | cms)
        :param settings: the settings file to use when asking for the value
        :param print_setting_args: the additional arguments to send to print_settings
        :return: unicode value of the django setting
        """
        if not settings:
            settings = os.environ.get("EDX_PLATFORM_SETTINGS", "aws")
        log_dir = os.path.dirname(cls.PRINT_SETTINGS_LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        settings_length = len(django_settings)
        django_settings = ' '.join(django_settings)  # parse_known_args makes a list again
        print_setting_args = ' '.join(print_setting_args or [])
        try:
            value = sh(
                django_cmd(
                    system,
                    settings,
                    "print_setting {django_settings} 2>{log_file} {print_setting_args}".format(
                        django_settings=django_settings,
                        print_setting_args=print_setting_args,
                        log_file=cls.PRINT_SETTINGS_LOG_FILE
                    ).strip()
                ),
                capture=True
            )
            # else for cases where values are not found & sh returns one None value
            return tuple(str(value).splitlines()) if value else tuple(None for _ in range(settings_length))
        except BuildFailure:
            print(f"Unable to print the value of the {django_settings} setting:")
            with open(cls.PRINT_SETTINGS_LOG_FILE) as f:
                print(f.read())
            sys.exit(1)

    @classmethod
    def get_django_json_settings(cls, django_settings, system, settings=None):
        """
        Interrogate Django environment for specific settings value
        :param django_settings: list of django settings values to get
        :param system: the django app to use when asking for the setting (lms | cms)
        :param settings: the settings file to use when asking for the value
        :return: json string value of the django setting
        """
        return cls.get_django_settings(
            django_settings,
            system,
            settings=settings,
            print_setting_args=["--json"],
        )

    @classmethod
    def covered_modules(cls):
        """
        List the source modules listed in .coveragerc for which coverage
        will be measured.
        """
        coveragerc = configparser.RawConfigParser()
        coveragerc.read(cls.PYTHON_COVERAGERC)
        modules = coveragerc.get('run', 'source')
        result = []
        for module in modules.split('\n'):
            module = module.strip()
            if module:
                result.append(module)
        return result

    @lazy
    def env_tokens(self):
        """
        Return a dict of environment settings.
        If we couldn't find the JSON file, issue a warning and return an empty dict.
        """

        # Find the env JSON file
        if self.SERVICE_VARIANT:
            env_path = self.REPO_ROOT.parent / f"{self.SERVICE_VARIANT}.env.json"
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
            return {}

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
        return self.env_tokens.get('FEATURES', {})

    @classmethod
    def rsync_dirs(cls):
        """
        List the directories that should be synced during pytest-xdist
        execution.  Needs to include all modules for which coverage is
        measured, not just the tests being run.
        """
        result = set()
        for module in cls.covered_modules():
            result.add(module.split('/')[0])
        return result
