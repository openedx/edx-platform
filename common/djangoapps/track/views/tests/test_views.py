# pylint: disable=missing-docstring,maybe-no-member

from mock import patch, sentinel

from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.test.utils import override_settings

from track import views
from track.middleware import TrackMiddleware
from track.tests import EventTrackingTestCase, FROZEN_TIME
from openedx.core.lib.tests.assertions.events import assert_event_matches


class TestTrackViews(EventTrackingTestCase):

    def setUp(self):
        super(TestTrackViews, self).setUp()

        self.request_factory = RequestFactory()

        patcher = patch('track.views.tracker', autospec=True)
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

        self.path_with_course = '/courses/foo/bar/baz/xmod/'
        self.url_with_course = 'http://www.edx.org' + self.path_with_course

        self.event = {
            sentinel.key: sentinel.value
        }

    def test_user_track(self):
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': '{}'
        })

        views.user_track(request)

        actual_event = self.get_event()
        expected_event = {
            'context': {
                'course_id': 'foo/bar/baz',
                'org_id': 'foo',
                'event_source': 'browser',
                'page': self.url_with_course,
                'username': 'anonymous'
            },
            'data': {},
            'timestamp': FROZEN_TIME,
            'name': str(sentinel.event_type)
        }
        assert_event_matches(expected_event, actual_event)

    def test_user_track_with_missing_values(self):
        request = self.request_factory.get('/event')

        views.user_track(request)

        actual_event = self.get_event()
        expected_event = {
            'context': {
                'course_id': '',
                'org_id': '',
                'event_source': 'browser',
                'page': '',
                'username': 'anonymous'
            },
            'data': {},
            'timestamp': FROZEN_TIME,
            'name': 'unknown'
        }
        assert_event_matches(expected_event, actual_event)

        views.user_track(request)

    def test_user_track_with_empty_event(self):
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': ''
        })

        views.user_track(request)

        actual_event = self.get_event()
        expected_event = {
            'context': {
                'course_id': 'foo/bar/baz',
                'org_id': 'foo',
                'event_source': 'browser',
                'page': self.url_with_course,
                'username': 'anonymous'
            },
            'data': {},
            'timestamp': FROZEN_TIME,
            'name': str(sentinel.event_type)
        }
        assert_event_matches(expected_event, actual_event)

    @override_settings(
        EVENT_TRACKING_PROCESSORS=[{'ENGINE': 'track.shim.LegacyFieldMappingProcessor'}],
    )
    def test_user_track_with_middleware_and_processors(self):
        self.recreate_tracker()

        middleware = TrackMiddleware()
        payload = '{"foo": "bar"}'
        user_id = 1
        request = self.request_factory.get('/event', {
            'page': self.url_with_course,
            'event_type': sentinel.event_type,
            'event': payload
        })
        request.user = User.objects.create(pk=user_id, username=str(sentinel.username))
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_REFERER'] = str(sentinel.referer)
        request.META['HTTP_ACCEPT_LANGUAGE'] = str(sentinel.accept_language)
        request.META['HTTP_USER_AGENT'] = str(sentinel.user_agent)
        request.META['SERVER_NAME'] = 'testserver2'
        middleware.process_request(request)
        try:
            views.user_track(request)

            expected_event = {
                'accept_language': str(sentinel.accept_language),
                'referer': str(sentinel.referer),
                'username': str(sentinel.username),
                'session': '',
                'ip': '10.0.0.1',
                'event_source': 'browser',
                'event_type': str(sentinel.event_type),
                'name': str(sentinel.event_type),
                'event': payload,
                'agent': str(sentinel.user_agent),
                'page': self.url_with_course,
                'time': FROZEN_TIME,
                'host': 'testserver2',
                'context': {
                    'course_id': 'foo/bar/baz',
                    'org_id': 'foo',
                    'user_id': user_id,
                    'path': u'/event'
                },
            }
        finally:
            middleware.process_response(request, None)

        actual_event = self.get_event()
        assert_event_matches(expected_event, actual_event)

    def test_server_track(self):
        request = self.request_factory.get(self.path_with_course)
        views.server_track(request, str(sentinel.event_type), '{}')

        expected_event = {
            'accept_language': '',
            'referer': '',
            'username': 'anonymous',
            'ip': '127.0.0.1',
            'event_source': 'server',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': None,
            'time': FROZEN_TIME,
            'host': 'testserver',
            'context': {},
        }
        self.assert_mock_tracker_call_matches(expected_event)

    def assert_mock_tracker_call_matches(self, expected_event):
        self.assertEqual(len(self.mock_tracker.send.mock_calls), 1)
        actual_event = self.mock_tracker.send.mock_calls[0][1][0]
        assert_event_matches(expected_event, actual_event)

    def test_server_track_with_middleware(self):
        middleware = TrackMiddleware()
        request = self.request_factory.get(self.path_with_course)
        middleware.process_request(request)
        # The middleware emits an event, reset the mock to ignore it since we aren't testing that feature.
        self.mock_tracker.reset_mock()
        try:
            views.server_track(request, str(sentinel.event_type), '{}')

            expected_event = {
                'accept_language': '',
                'referer': '',
                'username': 'anonymous',
                'ip': '127.0.0.1',
                'event_source': 'server',
                'event_type': str(sentinel.event_type),
                'event': '{}',
                'agent': '',
                'page': None,
                'time': FROZEN_TIME,
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

        self.assert_mock_tracker_call_matches(expected_event)

    def test_server_track_with_middleware_and_google_analytics_cookie(self):
        middleware = TrackMiddleware()
        request = self.request_factory.get(self.path_with_course)
        request.COOKIES['_ga'] = 'GA1.2.1033501218.1368477899'
        middleware.process_request(request)
        # The middleware emits an event, reset the mock to ignore it since we aren't testing that feature.
        self.mock_tracker.reset_mock()
        try:
            views.server_track(request, str(sentinel.event_type), '{}')

            expected_event = {
                'accept_language': '',
                'referer': '',
                'username': 'anonymous',
                'ip': '127.0.0.1',
                'event_source': 'server',
                'event_type': str(sentinel.event_type),
                'event': '{}',
                'agent': '',
                'page': None,
                'time': FROZEN_TIME,
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

        self.assert_mock_tracker_call_matches(expected_event)

    def test_server_track_with_no_request(self):
        request = None
        views.server_track(request, str(sentinel.event_type), '{}')

        expected_event = {
            'accept_language': '',
            'referer': '',
            'username': 'anonymous',
            'ip': '',
            'event_source': 'server',
            'event_type': str(sentinel.event_type),
            'event': '{}',
            'agent': '',
            'page': None,
            'time': FROZEN_TIME,
            'host': '',
            'context': {},
        }
        self.assert_mock_tracker_call_matches(expected_event)

    def test_task_track(self):
        request_info = {
            'accept_language': '',
            'referer': '',
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
            'time': FROZEN_TIME,
            'host': 'testserver',
            'context': {
                'course_id': '',
                'org_id': ''
            },
        }
        self.assert_mock_tracker_call_matches(expected_event)
