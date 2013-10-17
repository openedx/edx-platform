# pylint: disable=missing-docstring,maybe-no-member

from datetime import datetime

from mock import patch
from mock import sentinel
from pytz import UTC

from django.test import TestCase
from django.test.client import RequestFactory

from track import views


class TestTrackViews(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()

        patcher = patch('track.views.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

        self._expected_timestamp = datetime.now(UTC)
        self._datetime_patcher = patch('track.views.datetime')
        self.addCleanup(self._datetime_patcher.stop)
        mock_datetime_mod = self._datetime_patcher.start()
        mock_datetime_mod.datetime.now.return_value = self._expected_timestamp  # pylint: disable=maybe-no-member

        self.path_with_course = '/courses/foo/bar/baz/xmod/'
        self.url_with_course = 'http://www.edx.org' + self.path_with_course

        self.event = {
            sentinel.key: sentinel.value
        }

    def test_user_track(self):
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': {}
        })
        views.user_track(request)

        expected_event = {
            'username': 'anonymous',
            'session': '',
            'ip': '127.0.0.1',
            'event_source': 'browser',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': self.url_with_course,
            'time': self._expected_timestamp,
            'host': 'testserver',
            'context': {
                'course_id': 'foo/bar/baz',
                'org_id': 'foo',
            },
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)

    def test_server_track(self):
        request = self.request_factory.get(self.path_with_course)
        views.server_track(request, str(sentinel.event_type), '{}')

        expected_event = {
            'username': 'anonymous',
            'ip': '127.0.0.1',
            'event_source': 'server',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': None,
            'time': self._expected_timestamp,
            'host': 'testserver',
            'context': {},
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)

    def test_task_track(self):
        request_info = {
            'username': 'anonymous',
            'ip': '127.0.0.1',
            'agent': 'agent',
            'host': 'testserver',
        }

        task_info = {
            sentinel.task_key: sentinel.task_value
        }
        expected_event_data = dict(task_info)
        expected_event_data.update(self.event)

        views.task_track(request_info, task_info, str(sentinel.event_type), self.event)

        expected_event = {
            'username': 'anonymous',
            'ip': '127.0.0.1',
            'event_source': 'task',
            'event_type': str(sentinel.event_type),
            'event': expected_event_data,
            'agent': 'agent',
            'page': None,
            'time': self._expected_timestamp,
            'host': 'testserver',
            'context': {
                'course_id': '',
                'org_id': ''
            },
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)
