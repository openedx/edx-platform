import re

from mock import patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from eventtracking import tracker
from track.middleware import TrackMiddleware


class TrackMiddlewareTestCase(TestCase):

    def setUp(self):
        self.track_middleware = TrackMiddleware()
        self.request_factory = RequestFactory()

        patcher = patch('track.views.server_track')
        self.mock_server_track = patcher.start()
        self.addCleanup(patcher.stop)

    def test_normal_request(self):
        request = self.request_factory.get('/somewhere')
        self.track_middleware.process_request(request)
        self.assertTrue(self.mock_server_track.called)

    def test_default_filters_do_not_render_view(self):
        for url in ['/event', '/event/1', '/login', '/heartbeat']:
            request = self.request_factory.get(url)
            self.track_middleware.process_request(request)
            self.assertFalse(self.mock_server_track.called)
            self.mock_server_track.reset_mock()

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[])
    def test_reading_filtered_urls_from_settings(self):
        request = self.request_factory.get('/event')
        self.track_middleware.process_request(request)
        self.assertTrue(self.mock_server_track.called)

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[r'^/some/excluded.*'])
    def test_anchoring_of_patterns_at_beginning(self):
        request = self.request_factory.get('/excluded')
        self.track_middleware.process_request(request)
        self.assertTrue(self.mock_server_track.called)
        self.mock_server_track.reset_mock()

        request = self.request_factory.get('/some/excluded/url')
        self.track_middleware.process_request(request)
        self.assertFalse(self.mock_server_track.called)

    def test_request_in_course_context(self):
        request = self.request_factory.get('/courses/test_org/test_course/test_run/foo')
        self.track_middleware.process_request(request)
        self.assertEquals(
            tracker.get_tracker().resolve_context(),
            {
                'course_id': 'test_org/test_course/test_run',
                'org_id': 'test_org'
            }
        )
        self.track_middleware.process_response(request, None)
        self.assertEquals(
            tracker.get_tracker().resolve_context(),
            {}
        )
