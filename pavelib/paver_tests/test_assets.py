"""Unit tests for the Paver asset tasks."""


import os
from unittest import TestCase
from unittest.mock import patch

import ddt
import paver.tasks
from paver.easy import call_task, path
from watchdog.observers import Observer

from pavelib.assets import COLLECTSTATIC_LOG_DIR_ARG, collect_assets

from ..utils.envs import Env
from .utils import PaverTestCase

ROOT_PATH = path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
TEST_THEME_DIR = ROOT_PATH / "common/test/test-theme"


@ddt.ddt
class TestPaverAssetTasks(PaverTestCase):
    """
    Test the Paver asset tasks.
    """
    @ddt.data(
        [""],
        ["--force"],
        ["--debug"],
        ["--system=lms"],
        ["--system=lms --force"],
        ["--system=studio"],
        ["--system=studio --force"],
        ["--system=lms,studio"],
        ["--system=lms,studio --force"],
    )
    @ddt.unpack
    def test_compile_sass(self, options):
        """
        Test the "compile_sass" task.
        """
        parameters = options.split(" ")
        system = []
        if '--system=studio' not in parameters:
            system += ['lms']
        if '--system=lms' not in parameters:
            system += ['studio']
        debug = '--debug' in parameters
        force = '--force' in parameters
        self.reset_task_messages()
        call_task('pavelib.assets.compile_sass', options={'system': system, 'debug': debug, 'force': force})
        expected_messages = []
        if force:
            expected_messages.append('rm -rf common/static/css/*.css')
        expected_messages.append('libsass common/static/sass')

        if "lms" in system:
            if force:
                expected_messages.append('rm -rf lms/static/css/*.css')
            expected_messages.append('libsass lms/static/sass')
            expected_messages.append(
                'rtlcss lms/static/css/bootstrap/lms-main.css lms/static/css/bootstrap/lms-main-rtl.css'
            )
            expected_messages.append(
                'rtlcss lms/static/css/discussion/lms-discussion-bootstrap.css'
                ' lms/static/css/discussion/lms-discussion-bootstrap-rtl.css'
            )
            if force:
                expected_messages.append('rm -rf lms/static/certificates/css/*.css')
            expected_messages.append('libsass lms/static/certificates/sass')
        if "studio" in system:
            if force:
                expected_messages.append('rm -rf cms/static/css/*.css')
            expected_messages.append('libsass cms/static/sass')
            expected_messages.append(
                'rtlcss cms/static/css/bootstrap/studio-main.css cms/static/css/bootstrap/studio-main-rtl.css'
            )

        assert len(self.task_messages) == len(expected_messages)


@ddt.ddt
class TestPaverThemeAssetTasks(PaverTestCase):
    """
    Test the Paver asset tasks.
    """
    @ddt.data(
        [""],
        ["--force"],
        ["--debug"],
        ["--system=lms"],
        ["--system=lms --force"],
        ["--system=studio"],
        ["--system=studio --force"],
        ["--system=lms,studio"],
        ["--system=lms,studio --force"],
    )
    @ddt.unpack
    def test_compile_theme_sass(self, options):
        """
        Test the "compile_sass" task.
        """
        parameters = options.split(" ")
        system = []

        if '--system=studio' not in parameters:
            system += ['lms']
        if "--system=lms" not in parameters:
            system += ['studio']
        debug = '--debug' in parameters
        force = '--force' in parameters

        self.reset_task_messages()
        call_task(
            'pavelib.assets.compile_sass',
            options=dict(
                system=system,
                debug=debug,
                force=force,
                theme_dirs=[TEST_THEME_DIR.dirname()],
                themes=[TEST_THEME_DIR.basename()]
            ),
        )
        expected_messages = []
        if force:
            expected_messages.append('rm -rf common/static/css/*.css')
        expected_messages.append('libsass common/static/sass')

        if 'lms' in system:
            expected_messages.append('mkdir_p ' + repr(TEST_THEME_DIR / 'lms/static/css'))
            if force:
                expected_messages.append(
                    f'rm -rf {str(TEST_THEME_DIR)}/lms/static/css/*.css'
                )
            expected_messages.append("libsass lms/static/sass")
            expected_messages.append(
                'rtlcss {test_theme_dir}/lms/static/css/bootstrap/lms-main.css'
                ' {test_theme_dir}/lms/static/css/bootstrap/lms-main-rtl.css'.format(
                    test_theme_dir=str(TEST_THEME_DIR),
                )
            )
            expected_messages.append(
                'rtlcss {test_theme_dir}/lms/static/css/discussion/lms-discussion-bootstrap.css'
                ' {test_theme_dir}/lms/static/css/discussion/lms-discussion-bootstrap-rtl.css'.format(
                    test_theme_dir=str(TEST_THEME_DIR),
                )
            )
            if force:
                expected_messages.append(
                    f'rm -rf {str(TEST_THEME_DIR)}/lms/static/css/*.css'
                )
            expected_messages.append(
                f'libsass {str(TEST_THEME_DIR)}/lms/static/sass'
            )
            if force:
                expected_messages.append('rm -rf lms/static/css/*.css')
            expected_messages.append('libsass lms/static/sass')
            expected_messages.append(
                'rtlcss lms/static/css/bootstrap/lms-main.css lms/static/css/bootstrap/lms-main-rtl.css'
            )
            expected_messages.append(
                'rtlcss lms/static/css/discussion/lms-discussion-bootstrap.css'
                ' lms/static/css/discussion/lms-discussion-bootstrap-rtl.css'
            )
            if force:
                expected_messages.append('rm -rf lms/static/certificates/css/*.css')
            expected_messages.append('libsass lms/static/certificates/sass')

        if "studio" in system:
            expected_messages.append('mkdir_p ' + repr(TEST_THEME_DIR / 'cms/static/css'))
            if force:
                expected_messages.append(
                    f'rm -rf {str(TEST_THEME_DIR)}/cms/static/css/*.css'
                )
            expected_messages.append('libsass cms/static/sass')
            expected_messages.append(
                'rtlcss {test_theme_dir}/cms/static/css/bootstrap/studio-main.css'
                ' {test_theme_dir}/cms/static/css/bootstrap/studio-main-rtl.css'.format(
                    test_theme_dir=str(TEST_THEME_DIR),
                )
            )
            if force:
                expected_messages.append(
                    f'rm -rf {str(TEST_THEME_DIR)}/cms/static/css/*.css'
                )
            expected_messages.append(
                f'libsass {str(TEST_THEME_DIR)}/cms/static/sass'
            )
            if force:
                expected_messages.append('rm -rf cms/static/css/*.css')
            expected_messages.append('libsass cms/static/sass')
            expected_messages.append(
                'rtlcss cms/static/css/bootstrap/studio-main.css cms/static/css/bootstrap/studio-main-rtl.css'
            )

        assert len(self.task_messages) == len(expected_messages)


class TestPaverWatchAssetTasks(TestCase):
    """
    Test the Paver watch asset tasks.
    """

    def setUp(self):
        self.expected_sass_directories = [
            path('common/static/sass'),
            path('common/static'),
            path('node_modules/@edx'),
            path('node_modules'),
            path('lms/static/sass/partials'),
            path('lms/static/sass'),
            path('lms/static/certificates/sass'),
            path('cms/static/sass'),
            path('cms/static/sass/partials'),
        ]

        # Reset the options that paver stores in a global variable (thus polluting tests)
        if 'pavelib.assets.watch_assets' in paver.tasks.environment.options:
            del paver.tasks.environment.options['pavelib.assets.watch_assets']

        super().setUp()

    def tearDown(self):
        self.expected_sass_directories = []
        super().tearDown()

    def test_watch_assets(self):
        """
        Test the "compile_sass" task.
        """
        with patch('pavelib.assets.SassWatcher.register') as mock_register:
            with patch('pavelib.assets.Observer.start'):
                with patch('pavelib.assets.execute_webpack_watch') as mock_webpack:
                    call_task(
                        'pavelib.assets.watch_assets',
                        options={"background": True},
                    )
                    assert mock_register.call_count == 2
                    assert mock_webpack.call_count == 1

                    sass_watcher_args = mock_register.call_args_list[0][0]

                    assert isinstance(sass_watcher_args[0], Observer)
                    assert isinstance(sass_watcher_args[1], list)
                    assert len(sass_watcher_args[1]) == len(self.expected_sass_directories)

    def test_watch_theme_assets(self):
        """
        Test the Paver watch asset tasks with theming enabled.
        """
        self.expected_sass_directories.extend([
            path(TEST_THEME_DIR) / 'lms/static/sass',
            path(TEST_THEME_DIR) / 'lms/static/sass/partials',
            path(TEST_THEME_DIR) / 'lms/static/certificates/sass',
            path(TEST_THEME_DIR) / 'cms/static/sass',
            path(TEST_THEME_DIR) / 'cms/static/sass/partials',
        ])

        with patch('pavelib.assets.SassWatcher.register') as mock_register:
            with patch('pavelib.assets.Observer.start'):
                with patch('pavelib.assets.execute_webpack_watch') as mock_webpack:
                    call_task(
                        'pavelib.assets.watch_assets',
                        options={
                            "background": True,
                            "theme_dirs": [TEST_THEME_DIR.dirname()],
                            "themes": [TEST_THEME_DIR.basename()]
                        },
                    )
                    assert mock_register.call_count == 2
                    assert mock_webpack.call_count == 1

                    sass_watcher_args = mock_register.call_args_list[0][0]
                    assert isinstance(sass_watcher_args[0], Observer)
                    assert isinstance(sass_watcher_args[1], list)
                    assert len(sass_watcher_args[1]) == len(self.expected_sass_directories)


@ddt.ddt
class TestCollectAssets(PaverTestCase):
    """
    Test the collectstatic process call.

    ddt data is organized thusly:
      * debug: whether or not collect_assets is called with the debug flag
      * specified_log_location: used when collect_assets is called with a specific
          log location for collectstatic output
      * expected_log_location: the expected string to be used for piping collectstatic logs
    """

    @ddt.data(
        [{
            "collect_log_args": {},  # Test for default behavior
            "expected_log_location": "> /dev/null"
        }],
        [{
            "collect_log_args": {COLLECTSTATIC_LOG_DIR_ARG: "/foo/bar"},
            "expected_log_location": "> /foo/bar/lms-collectstatic.log"
        }],  # can use specified log location
        [{
            "systems": ["lms", "cms"],
            "collect_log_args": {},
            "expected_log_location": "> /dev/null"
        }],  # multiple systems can be called
    )
    @ddt.unpack
    def test_collect_assets(self, options):
        """
        Ensure commands sent to the environment for collect_assets are as expected
        """
        specified_log_loc = options.get("collect_log_args", {})
        specified_log_dict = specified_log_loc
        log_loc = options.get("expected_log_location", "> /dev/null")
        systems = options.get("systems", ["lms"])
        if specified_log_loc is None:
            collect_assets(
                systems,
                Env.DEVSTACK_SETTINGS
            )
        else:
            collect_assets(
                systems,
                Env.DEVSTACK_SETTINGS,
                **specified_log_dict
            )
        self._assert_correct_messages(log_location=log_loc, systems=systems)

    def test_collect_assets_debug(self):
        """
        When the method is called specifically with None for the collectstatic log dir, then
        it should run in debug mode and pipe to console.
        """
        expected_log_loc = ""
        systems = ["lms"]
        kwargs = {COLLECTSTATIC_LOG_DIR_ARG: None}
        collect_assets(systems, Env.DEVSTACK_SETTINGS, **kwargs)
        self._assert_correct_messages(log_location=expected_log_loc, systems=systems)

    def _assert_correct_messages(self, log_location, systems):
        """
        Asserts that the expected commands were run.

        We just extract the pieces we care about here instead of specifying an
        exact command, so that small arg changes don't break this test.
        """
        for i, sys in enumerate(systems):
            msg = self.task_messages[i]
            assert msg.startswith(f'python manage.py {sys}')
            assert ' collectstatic ' in msg
            assert f'--settings={Env.DEVSTACK_SETTINGS}' in msg
            assert msg.endswith(f' {log_location}')


@ddt.ddt
class TestUpdateAssetsTask(PaverTestCase):
    """
    These are nearly end-to-end tests, because they observe output from the commandline request,
    but do not actually execute the commandline on the terminal/process
    """

    @ddt.data(
        [{"expected_substring": "> /dev/null"}],  # go to /dev/null by default
        [{"cmd_args": ["--debug"], "expected_substring": "collectstatic"}]  # TODO: make this regex
    )
    @ddt.unpack
    def test_update_assets_task_collectstatic_log_arg(self, options):
        """
        Scoped test that only looks at what is passed to the collecstatic options
        """
        cmd_args = options.get("cmd_args", [""])
        expected_substring = options.get("expected_substring", None)
        call_task('pavelib.assets.update_assets', args=cmd_args)
        self.assertTrue(
            self._is_substring_in_list(self.task_messages, expected_substring),
            msg=f"{expected_substring} not found in messages"
        )

    def _is_substring_in_list(self, messages_list, expected_substring):
        """
        Return true a given string is somewhere in a list of strings
        """
        for message in messages_list:
            if expected_substring in message:
                return True
        return False
