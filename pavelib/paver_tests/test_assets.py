"""Unit tests for the Paver asset tasks."""

import ddt
import os
from unittest import TestCase
from paver.easy import call_task, path
from mock import patch
from watchdog.observers.polling import PollingObserver
from .utils import PaverTestCase

ROOT_PATH = path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
TEST_THEME = ROOT_PATH / "common/test/test-theme"  # pylint: disable=invalid-name


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
        if "--system=studio" not in parameters:
            system += ["lms"]
        if "--system=lms" not in parameters:
            system += ["studio"]
        debug = "--debug" in parameters
        force = "--force" in parameters
        self.reset_task_messages()
        call_task('pavelib.assets.compile_sass', options={"system": system, "debug": debug, "force": force})
        expected_messages = []
        if force:
            expected_messages.append("rm -rf common/static/css/*.css")
        expected_messages.append("libsass common/static/sass")

        if "lms" in system:
            if force:
                expected_messages.append("rm -rf lms/static/css/*.css")
            expected_messages.append("libsass lms/static/sass")
            if force:
                expected_messages.append("rm -rf lms/static/certificates/css/*.css")
            expected_messages.append("libsass lms/static/certificates/sass")
        if "studio" in system:
            if force:
                expected_messages.append("rm -rf cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")

        self.assertEquals(self.task_messages, expected_messages)


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

        if "--system=studio" not in parameters:
            system += ["lms"]
        if "--system=lms" not in parameters:
            system += ["studio"]
        debug = "--debug" in parameters
        force = "--force" in parameters

        self.reset_task_messages()
        call_task(
            'pavelib.assets.compile_sass',
            options={"system": system, "debug": debug, "force": force, "theme-dirs": [TEST_THEME.dirname()],
                     "themes": [TEST_THEME.basename()]},
        )
        expected_messages = []
        if force:
            expected_messages.append("rm -rf common/static/css/*.css")
        expected_messages.append("libsass common/static/sass")

        if "lms" in system:
            expected_messages.append("mkdir_p " + repr(TEST_THEME / "lms/static/css"))

            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/lms/static/css/*.css")
            expected_messages.append("libsass lms/static/sass")
            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/lms/static/css/*.css")
            expected_messages.append("libsass " + str(TEST_THEME) + "/lms/static/sass")
            if force:
                expected_messages.append("rm -rf lms/static/css/*.css")
            expected_messages.append("libsass lms/static/sass")
            if force:
                expected_messages.append("rm -rf lms/static/certificates/css/*.css")
            expected_messages.append("libsass lms/static/certificates/sass")

        if "studio" in system:
            expected_messages.append("mkdir_p " + repr(TEST_THEME / "cms/static/css"))
            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")
            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/cms/static/css/*.css")
            expected_messages.append("libsass " + str(TEST_THEME) + "/cms/static/sass")

            if force:
                expected_messages.append("rm -rf cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")

        self.assertEquals(self.task_messages, expected_messages)


class TestPaverWatchAssetTasks(TestCase):
    """
    Test the Paver watch asset tasks.
    """

    def setUp(self):
        self.expected_sass_directories = [
            path('common/static/sass'),
            path('common/static'),
            path('node_modules'),
            path('node_modules/edx-pattern-library/node_modules'),
            path('lms/static/sass/partials'),
            path('lms/static/sass'),
            path('lms/static/certificates/sass'),
            path('cms/static/sass'),
            path('cms/static/sass/partials'),
        ]
        super(TestPaverWatchAssetTasks, self).setUp()

    def tearDown(self):
        self.expected_sass_directories = []
        super(TestPaverWatchAssetTasks, self).tearDown()

    def test_watch_assets(self):
        """
        Test the "compile_sass" task.
        """
        with patch('pavelib.assets.SassWatcher.register') as mock_register:
            with patch('pavelib.assets.PollingObserver.start'):
                call_task(
                    'pavelib.assets.watch_assets',
                    options={"background": True},
                )
                self.assertEqual(mock_register.call_count, 2)

                sass_watcher_args = mock_register.call_args_list[0][0]

                self.assertIsInstance(sass_watcher_args[0], PollingObserver)
                self.assertIsInstance(sass_watcher_args[1], list)
                self.assertItemsEqual(sass_watcher_args[1], self.expected_sass_directories)

    def test_watch_theme_assets(self):
        """
        Test the Paver watch asset tasks with theming enabled.
        """
        self.expected_sass_directories.extend([
            path(TEST_THEME) / 'lms/static/sass',
            path(TEST_THEME) / 'lms/static/sass/partials',
            path(TEST_THEME) / 'cms/static/sass',
            path(TEST_THEME) / 'cms/static/sass/partials',
        ])

        with patch('pavelib.assets.SassWatcher.register') as mock_register:
            with patch('pavelib.assets.PollingObserver.start'):
                call_task(
                    'pavelib.assets.watch_assets',
                    options={"background": True, "theme-dirs": [TEST_THEME.dirname()],
                             "themes": [TEST_THEME.basename()]},
                )
                self.assertEqual(mock_register.call_count, 2)

                sass_watcher_args = mock_register.call_args_list[0][0]
                self.assertIsInstance(sass_watcher_args[0], PollingObserver)
                self.assertIsInstance(sass_watcher_args[1], list)
                self.assertItemsEqual(sass_watcher_args[1], self.expected_sass_directories)
