from mock import patch
from mock import sentinel

from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from eventtracking import tracker
from track.middleware import TrackMiddleware


class TrackMiddlewareTestCase(TestCase):

    def setUp(self):
        super(TrackMiddlewareTestCase, self).setUp()
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

    def test_default_request_context(self):
        context = self.get_context_for_path('/courses/')
        self.assertEquals(context, {
            'accept_language': '',
            'referer': '',
            'user_id': '',
            'session': '',
            'username': '',
            'ip': '127.0.0.1',
            'host': 'testserver',
            'agent': '',
            'path': '/courses/',
            'org_id': '',
            'course_id': '',
            'client_id': None,
        })

    def get_context_for_path(self, path):
        """Extract the generated event tracking context for a given request for the given path."""
        request = self.request_factory.get(path)
        return self.get_context_for_request(request)

    def get_context_for_request(self, request):
        """Extract the generated event tracking context for the given request."""
        self.track_middleware.process_request(request)
        try:
            captured_context = tracker.get_tracker().resolve_context()
        finally:
            self.track_middleware.process_response(request, None)

        self.assertEquals(
            tracker.get_tracker().resolve_context(),
            {}
        )

        return captured_context

    def test_request_in_course_context(self):
        captured_context = self.get_context_for_path('/courses/test_org/test_course/test_run/foo')
        expected_context_subset = {
            'course_id': 'test_org/test_course/test_run',
            'org_id': 'test_org',
        }
        self.assert_dict_subset(captured_context, expected_context_subset)

    def assert_dict_subset(self, superset, subset):
        """Assert that the superset dict contains all of the key-value pairs found in the subset dict."""
        for key, expected_value in subset.iteritems():
            self.assertEquals(superset[key], expected_value)

    def test_request_with_user(self):
        user_id = 1
        username = sentinel.username

        request = self.request_factory.get('/courses/')
        request.user = User(pk=user_id, username=username)

        context = self.get_context_for_request(request)
        self.assert_dict_subset(context, {
            'user_id': user_id,
            'username': username,
        })

    def test_request_with_session(self):
        request = self.request_factory.get('/courses/')
        SessionMiddleware().process_request(request)
        request.session.save()
        session_key = request.session.session_key
        expected_session_key = self.track_middleware.encrypt_session_key(session_key)
        self.assertEquals(len(session_key), len(expected_session_key))
        context = self.get_context_for_request(request)
        self.assert_dict_subset(context, {
            'session': expected_session_key,
        })

    @override_settings(SECRET_KEY='85920908f28904ed733fe576320db18cabd7b6cd')
    def test_session_key_encryption(self):
        session_key = '665924b49a93e22b46ee9365abf28c2a'
        expected_session_key = '3b81f559d14130180065d635a4f35dd2'
        encrypted_session_key = self.track_middleware.encrypt_session_key(session_key)
        self.assertEquals(encrypted_session_key, expected_session_key)

    def test_request_headers(self):
        ip_address = '10.0.0.0'
        user_agent = 'UnitTest/1.0'

        factory = RequestFactory(REMOTE_ADDR=ip_address, HTTP_USER_AGENT=user_agent)
        request = factory.get('/some-path')
        context = self.get_context_for_request(request)

        self.assert_dict_subset(context, {
            'ip': ip_address,
            'agent': user_agent,
        })
