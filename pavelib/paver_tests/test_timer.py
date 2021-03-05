"""
Tests of the pavelib.utils.timer module.
"""


from datetime import datetime, timedelta
from unittest import TestCase

from unittest.mock import MagicMock, patch

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
        super().setUp()

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
        assert len(messages) == 1

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        assert 'duration' in messages[0]
        assert 35.6 == messages[0]['duration']

        assert 'started_at' in messages[0]
        assert start.isoformat(' ') == messages[0]['started_at']

        assert 'ended_at' in messages[0]
        assert end.isoformat(' ') == messages[0]['ended_at']

    @patch.object(timer, 'PAVER_TIMER_LOG', None)
    def test_no_logs(self):
        messages = self.get_log_messages()
        assert len(messages) == 0

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_arguments(self):
        messages = self.get_log_messages(args=(1, 'foo'), kwargs=dict(bar='baz'))
        assert len(messages) == 1

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        assert 'args' in messages[0]
        assert [repr(1), repr('foo')] == messages[0]['args']
        assert 'kwargs' in messages[0]
        assert {'bar': repr('baz')} == messages[0]['kwargs']

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_task_name(self):
        messages = self.get_log_messages()
        assert len(messages) == 1

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        assert 'task' in messages[0]
        assert 'pavelib.paver_tests.test_timer.identity' == messages[0]['task']

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log')
    def test_exceptions(self):

        @timer.timed
        def raises():
            """
            A task used for testing exception handling of the timed decorator.
            """
            raise Exception('The Message!')

        messages = self.get_log_messages(task=raises, raises=Exception)
        assert len(messages) == 1

        # I'm not using assertDictContainsSubset because it is
        # removed in python 3.2 (because the arguments were backwards)
        # and it wasn't ever replaced by anything *headdesk*
        assert 'exception' in messages[0]
        assert 'Exception: The Message!' == messages[0]['exception']

    @patch.object(timer, 'PAVER_TIMER_LOG', '/tmp/some-log-%Y-%m-%d-%H-%M-%S.log')
    def test_date_formatting(self):
        start = datetime(2016, 7, 20, 10, 56, 19)
        end = start + timedelta(seconds=35.6)

        self.mock_datetime.utcnow.side_effect = [start, end]

        messages = self.get_log_messages()
        assert len(messages) == 1

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
        assert len(messages) == 2

        # Child messages first
        assert 'duration' in messages[0]
        assert 40 == messages[0]['duration']

        assert 'started_at' in messages[0]
        assert child_start.isoformat(' ') == messages[0]['started_at']

        assert 'ended_at' in messages[0]
        assert child_end.isoformat(' ') == messages[0]['ended_at']

        # Parent messages after
        assert 'duration' in messages[1]
        assert 60 == messages[1]['duration']

        assert 'started_at' in messages[1]
        assert parent_start.isoformat(' ') == messages[1]['started_at']

        assert 'ended_at' in messages[1]
        assert parent_end.isoformat(' ') == messages[1]['ended_at']
