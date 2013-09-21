import re

from mock import patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from track.middleware import TrackMiddleware


@patch('track.views.server_track')
class TrackMiddlewareTestCase(TestCase):

    def setUp(self):
        self.track_middleware = TrackMiddleware()
        self.request_factory = RequestFactory()

    def test_normal_request(self, mock_server_track):
        request = self.request_factory.get('/somewhere')
        self.track_middleware.process_request(request)
        self.assertTrue(mock_server_track.called)

    def test_default_filters_do_not_render_view(self, mock_server_track):
        for url in ['/event', '/event/1', '/login', '/heartbeat']:
            request = self.request_factory.get(url)
            self.track_middleware.process_request(request)
            self.assertFalse(mock_server_track.called)
            mock_server_track.reset_mock()

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[])
    def test_reading_filtered_urls_from_settings(self, mock_server_track):
        request = self.request_factory.get('/event')
        self.track_middleware.process_request(request)
        self.assertTrue(mock_server_track.called)

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[r'^/some/excluded.*'])
    def test_anchoring_of_patterns_at_beginning(self, mock_server_track):
        request = self.request_factory.get('/excluded')
        self.track_middleware.process_request(request)
        self.assertTrue(mock_server_track.called)
        mock_server_track.reset_mock()

        request = self.request_factory.get('/some/excluded/url')
        self.track_middleware.process_request(request)
        self.assertFalse(mock_server_track.called)
