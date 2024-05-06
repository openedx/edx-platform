"""Unit tests for the Paver asset tasks."""

import json
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import ddt
import paver.easy
from paver import tasks

import pavelib.assets
from pavelib.assets import Env


REPO_ROOT = Path(__file__).parent.parent.parent

LMS_SETTINGS = {
    "WEBPACK_CONFIG_PATH": "webpack.fake.config.js",
    "STATIC_ROOT": "/fake/lms/staticfiles",

}
CMS_SETTINGS = {
    "WEBPACK_CONFIG_PATH": "webpack.fake.config",
    "STATIC_ROOT": "/fake/cms/staticfiles",
    "JS_ENV_EXTRA_CONFIG": json.dumps({"key1": [True, False], "key2": {"key2.1": 1369, "key2.2": "1369"}}),
}


def _mock_get_django_settings(django_settings, system, settings=None):  # pylint: disable=unused-argument
    return [(LMS_SETTINGS if system == "lms" else CMS_SETTINGS)[s] for s in django_settings]


@ddt.ddt
@patch.object(Env, 'get_django_settings', _mock_get_django_settings)
@patch.object(Env, 'get_django_json_settings', _mock_get_django_settings)
class TestDeprecatedPaverAssets(TestCase):
    """
    Simple test to ensure that the soon-to-be-removed Paver commands are correctly translated into the new npm-run
    commands.
    """
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        os.environ['NO_PREREQ_INSTALL'] = 'true'
        tasks.environment = tasks.Environment()

    def tearDown(self):
        super().tearDown()
        del os.environ['NO_PREREQ_INSTALL']

    @ddt.data(
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={},
            expected=["npm run compile-sass --"],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"system": "lms,studio"},
            expected=["npm run compile-sass --"],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"debug": True},
            expected=["npm run compile-sass-dev --"],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"system": "lms"},
            expected=["npm run compile-sass -- --skip-cms"],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"system": "studio"},
            expected=["npm run compile-sass -- --skip-lms"],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"system": "cms", "theme_dirs": f"{REPO_ROOT}/common/test,{REPO_ROOT}/themes"},
            expected=[
                "npm run compile-sass -- --skip-lms " +
                f"--theme-dir {REPO_ROOT}/common/test --theme-dir {REPO_ROOT}/themes"
            ],
        ),
        dict(
            task_name='pavelib.assets.compile_sass',
            args=[],
            kwargs={"theme_dirs": f"{REPO_ROOT}/common/test,{REPO_ROOT}/themes", "themes": "red-theme,test-theme"},
            expected=[
                "npm run compile-sass -- " +
                f"--theme-dir {REPO_ROOT}/common/test --theme-dir {REPO_ROOT}/themes " +
                "--theme red-theme --theme test-theme"
            ],
        ),
        dict(
            task_name='pavelib.assets.update_assets',
            args=["lms", "studio", "--settings=fake.settings"],
            kwargs={},
            expected=[
                (
                    "WEBPACK_CONFIG_PATH=webpack.fake.config.js " +
                    "NODE_ENV=production " +
                    "STATIC_ROOT_LMS=/fake/lms/staticfiles " +
                    "STATIC_ROOT_CMS=/fake/cms/staticfiles " +
                    'JS_ENV_EXTRA_CONFIG=' + +
                    '"{\\"key1\\": [true, false], \\"key2\\": {\\"key2.1\\": 1369, \\"key2.2\\": \\"1369\\"}}" ' +
                    "npm run webpack"
                ),
                "python manage.py lms --settings=fake.settings compile_sass lms ",
                "python manage.py cms --settings=fake.settings compile_sass cms ",
                (
                    "( ./manage.py lms --settings=fake.settings collectstatic --noinput ) && " +
                    "( ./manage.py cms --settings=fake.settings collectstatic --noinput )"
                ),
            ],
        ),
    )
    @ddt.unpack
    @patch.object(pavelib.assets, 'sh')
    def test_paver_assets_wrapper_invokes_new_commands(self, mock_sh, task_name, args, kwargs, expected):
        paver.easy.call_task(task_name, args=args, options=kwargs)
        assert [call_args[0] for (call_args, call_kwargs) in mock_sh.call_args_list] == expected
