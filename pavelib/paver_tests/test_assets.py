"""Unit tests for the Paver asset tasks."""

import ddt
import os
from unittest import TestCase
from pavelib.assets import collect_assets, COLLECTSTATIC_LOG_DIR_ARG
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
            options={"system": system, "debug": debug, "force": force, "theme_dirs": [TEST_THEME.dirname()],
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
                    options={"background": True, "theme_dirs": [TEST_THEME.dirname()],
                             "themes": [TEST_THEME.basename()]},
                )
                self.assertEqual(mock_register.call_count, 2)

                sass_watcher_args = mock_register.call_args_list[0][0]
                self.assertIsInstance(sass_watcher_args[0], PollingObserver)
                self.assertIsInstance(sass_watcher_args[1], list)
                self.assertItemsEqual(sass_watcher_args[1], self.expected_sass_directories)


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
        expected_messages = self._set_expected_messages(log_location=log_loc, systems=systems)
        if specified_log_loc is None:
            collect_assets(
                systems,
                "devstack"
            )
        else:
            collect_assets(
                systems,
                "devstack",
                **specified_log_dict
            )
        self.assertEqual(self.task_messages, expected_messages)

    def test_collect_assets_debug(self):
        """
        When the method is called specifically with None for the collectstatic log dir, then
        it should run in debug mode and pipe to console.
        """
        expected_log_loc = ""
        systems = ["lms"]
        kwargs = {COLLECTSTATIC_LOG_DIR_ARG: None}
        expected_messages = self._set_expected_messages(log_location=expected_log_loc, systems=systems)
        collect_assets(systems, "devstack", **kwargs)
        self.assertEqual(self.task_messages, expected_messages)

    def _set_expected_messages(self, log_location, systems):
        """
        Returns a list of messages that are expected to be sent from paver
         to the commandline for collectstatic functions. This list is constructed
         based on the log location and systems being passed in.
        """

        expected_messages = []
        for sys in systems:
            expected_messages.append(
                'python manage.py {system} --settings=devstack collectstatic --noinput {log_loc}'.format(
                    system=sys,
                    log_loc=log_location
                )
            )
        return expected_messages


@ddt.ddt
class TestUpdateAssetsTask(PaverTestCase):
    """
    These are nearly end-to-end tests, because they observe output from the commandline request,
    but do not actually execute the commandline on the terminal/process
    """

    @ddt.data(
        [{"expected_substring": "> /dev/null"}],  # go to /dev/null by default
        [{"cmd_args": ["--debug"], "expected_substring": "collectstatic --noinput "}]  # TODO: make this regex
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
            msg="{substring} not found in messages".format(substring=expected_substring)
        )

    def _is_substring_in_list(self, messages_list, expected_substring):
        """
        Return true a given string is somewhere in a list of strings
        """
        for message in messages_list:
            if expected_substring in message:
                return True
        return False
