"""Unit tests for the Paver asset tasks."""

import ddt
from paver.easy import call_task
from mock import patch
from unittest import TestCase
from watchdog.observers.polling import PollingObserver

from .utils import PaverTestCase


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
                expected_messages.append("rm -rf lms/static/css/*.css")
            expected_messages.append("libsass lms/static/themed_sass")
            if force:
                expected_messages.append("rm -rf lms/static/certificates/css/*.css")
            expected_messages.append("libsass lms/static/certificates/sass")
        if "studio" in system:
            if force:
                expected_messages.append("rm -rf cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")
        self.assertEquals(self.task_messages, expected_messages)


class TestPaverWatchAssetTasks(TestCase):
    """
    Test the Paver watch asset tasks.
    """

    def setUp(self):
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
