# pylint: disable=missing-docstring,maybe-no-member

from track import views
from track.middleware import TrackMiddleware
from mock import patch, sentinel
from freezegun import freeze_time

from django.test import TestCase
from django.test.client import RequestFactory

from eventtracking import tracker

from datetime import datetime
expected_time = datetime(2013, 10, 3, 8, 24, 55)


class TestTrackViews(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()

        patcher = patch('track.views.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

        self.path_with_course = '/courses/foo/bar/baz/xmod/'
        self.url_with_course = 'http://www.edx.org' + self.path_with_course

        self.event = {
            sentinel.key: sentinel.value
        }

    @freeze_time(expected_time)
    def test_user_track(self):
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': {}
        })
        with tracker.get_tracker().context('edx.request', {'session': sentinel.session}):
            views.user_track(request)

        expected_event = {
            'username': 'anonymous',
            'session': sentinel.session,
            'ip': '127.0.0.1',
            'event_source': 'browser',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': self.url_with_course,
            'time': expected_time,
            'host': 'testserver',
            'context': {
                'course_id': 'foo/bar/baz',
                'org_id': 'foo',
            },
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)

    @freeze_time(expected_time)
    def test_user_track_with_middleware(self):
        middleware = TrackMiddleware()
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': {}
        })
        middleware.process_request(request)
        try:
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
                'time': expected_time,
                'host': 'testserver',
                'context': {
                    'course_id': 'foo/bar/baz',
                    'org_id': 'foo',
                    'user_id': '',
                    'path': u'/event'
                },
            }
        finally:
            middleware.process_response(request, None)

        self.mock_tracker.send.assert_called_once_with(expected_event)

    @freeze_time(expected_time)
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
            'time': expected_time,
            'host': 'testserver',
            'context': {},
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)

    @freeze_time(expected_time)
    def test_server_track_with_middleware(self):
        middleware = TrackMiddleware()
        request = self.request_factory.get(self.path_with_course)
        middleware.process_request(request)
        # The middleware emits an event, reset the mock to ignore it since we aren't testing that feature.
        self.mock_tracker.reset_mock()
        try:
            views.server_track(request, str(sentinel.event_type), '{}')

            expected_event = {
                'username': 'anonymous',
                'ip': '127.0.0.1',
                'event_source': 'server',
                'event_type': str(sentinel.event_type),
                'event': '{}',
                'agent': '',
                'page': None,
                'time': expected_time,
                'host': 'testserver',
                'context': {
                    'user_id': '',
                    'course_id': u'foo/bar/baz',
                    'org_id': 'foo',
                    'path': u'/courses/foo/bar/baz/xmod/'
                },
            }
        finally:
            middleware.process_response(request, None)

        self.mock_tracker.send.assert_called_once_with(expected_event)

    @freeze_time(expected_time)
    def test_server_track_with_no_request(self):
        request = None
        views.server_track(request, str(sentinel.event_type), '{}')

        expected_event = {
            'username': 'anonymous',
            'ip': '',
            'event_source': 'server',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': None,
            'time': expected_time,
            'host': '',
            'context': {},
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)

    @freeze_time(expected_time)
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
            'time': expected_time,
            'host': 'testserver',
            'context': {
                'course_id': '',
                'org_id': ''
            },
        }
        self.mock_tracker.send.assert_called_once_with(expected_event)
