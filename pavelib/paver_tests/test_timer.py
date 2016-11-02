"""
Tests of the pavelib.utils.timer module.
"""

from datetime import datetime, timedelta
from mock import patch, MagicMock
from unittest import TestCase

from pavelib.utils import timer


@timer.timed
def identity(*args, **kwargs):
    """
    An identity function used as a default task to test the timing of.
    """
    return args, kwargs


MOCK_OPEN = MagicMock(spec=open)


@patch.dict('pavelib.utils.timer.__builtins__', open=MOCK_OPEN)
class TimedDecoratorTests(TestCase):
    """
    Tests of the pavelib.utils.timer:timed decorator.
    """
    def setUp(self):
        super(TimedDecoratorTests, self).setUp()

        patch_dumps = patch.object(timer.json, 'dump', autospec=True)
        self.mock_dump = patch_dumps.start()
        self.addCleanup(patch_dumps.stop)

        patch_makedirs = patch.object(timer.os, 'makedirs', autospec=True)
        self.mock_makedirs = patch_makedirs.start()
        self.addCleanup(patch_makedirs.stop)

        patch_datetime = patch.object(timer, 'datetime', autospec=True)
        self.mock_datetime = patch_datetime.start()
        self.addCleanup(patch_datetime.stop)

        patch_exists = patch.object(timer, 'exists', autospec=True)
        self.mock_exists = patch_exists.start()
        self.addCleanup(patch_exists.stop)

        MOCK_OPEN.reset_mock()

    def get_log_messages(self, task=identity, args=None, kwargs=None, raises=None):
        """
        Return all timing messages recorded during the execution of ``task``.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        if raises is None:
            task(*args, **kwargs)
        else:
            self.assertRaises(raises, task, *args, **kwargs)

        return [
            call[0][0]  # log_message
            for call in self.mock_dump.call_args_list
        ]

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_times(self):
        start = datetime(2016, 7, 20, 10, 56, 19)
        end = start + timedelta(seconds=35.6)

        self.mock_datetime.utcnow.side_effect = [start, end]

        messages = self.get_log_messages()
        self.assertEquals(len(messages), 1)

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        self.assertIn('duration', messages[0])
        self.assertEquals(35.6, messages[0]['duration'])

        self.assertIn('started_at', messages[0])
        self.assertEquals(start.isoformat(' '), messages[0]['started_at'])

        self.assertIn('ended_at', messages[0])
        self.assertEquals(end.isoformat(' '), messages[0]['ended_at'])

    @patch.object(timer, 'PAVER_TIMER_LOG', None)
    def test_no_logs(self):
        messages = self.get_log_messages()
        self.assertEquals(len(messages), 0)

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_arguments(self):
        messages = self.get_log_messages(args=(1, 'foo'), kwargs=dict(bar='baz'))
        self.assertEquals(len(messages), 1)

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        self.assertIn('args', messages[0])
        self.assertEquals([repr(1), repr('foo')], messages[0]['args'])
        self.assertIn('kwargs', messages[0])
        self.assertEquals({'bar': repr('baz')}, messages[0]['kwargs'])

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_task_name(self):
        messages = self.get_log_messages()
        self.assertEquals(len(messages), 1)

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        self.assertIn('task', messages[0])
        self.assertEquals('pavelib.paver_tests.test_timer.identity', messages[0]['task'])

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_exceptions(self):

        @timer.timed
        def raises():
            """
            A task used for testing exception handling of the timed decorator.
            """
            raise Exception('The Message!')

        messages = self.get_log_messages(task=raises, raises=Exception)
        self.assertEquals(len(messages), 1)

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        self.assertIn('exception', messages[0])
        self.assertEquals("Exception: The Message!", messages[0]['exception'])

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log-%Y-%m-%d-%H-%M-%S.log')
    def test_date_formatting(self):
        start = datetime(2016, 7, 20, 10, 56, 19)
        end = start + timedelta(seconds=35.6)

        self.mock_datetime.utcnow.side_effect = [start, end]

        messages = self.get_log_messages()
        self.assertEquals(len(messages), 1)

        MOCK_OPEN.assert_called_once_with('/tmp/some-log-2016-07-20-10-56-19.log', 'a')

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_nested_tasks(self):

        @timer.timed
        def parent():
            """
            A timed task that calls another task
            """
            identity()

        parent_start = datetime(2016, 7, 20, 10, 56, 19)
        parent_end = parent_start + timedelta(seconds=60)
        child_start = parent_start + timedelta(seconds=10)
        child_end = parent_end - timedelta(seconds=10)

        self.mock_datetime.utcnow.side_effect = [parent_start, child_start, child_end, parent_end]

        messages = self.get_log_messages(task=parent)
        self.assertEquals(len(messages), 2)

        # Child messages first
        self.assertIn('duration', messages[0])
        self.assertEquals(40, messages[0]['duration'])

        self.assertIn('started_at', messages[0])
        self.assertEquals(child_start.isoformat(' '), messages[0]['started_at'])

        self.assertIn('ended_at', messages[0])
        self.assertEquals(child_end.isoformat(' '), messages[0]['ended_at'])

        # Parent messages after
        self.assertIn('duration', messages[1])
        self.assertEquals(60, messages[1]['duration'])

        self.assertIn('started_at', messages[1])
        self.assertEquals(parent_start.isoformat(' '), messages[1]['started_at'])

        self.assertIn('ended_at', messages[1])
        self.assertEquals(parent_end.isoformat(' '), messages[1]['ended_at'])
