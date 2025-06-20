"""
Unit tests for SessionInactivityTimeout middleware.
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory, override_settings

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import get_mock_request

from ..middleware import (
    SessionInactivityTimeout,
    LAST_TOUCH_KEYNAME,
    LAST_SESSION_SAVE_TIME_KEYNAME
)


class SessionInactivityTimeoutTestCase(TestCase):
    """
    Test cases for SessionInactivityTimeout middleware.
    """

    def setUp(self):
        """
        Set up test data.
        """
        super().setUp()
        self.user = UserFactory.create()
        self.middleware = SessionInactivityTimeout(get_response=lambda request: None)
        self.request = get_mock_request(self.user)
        
        # Create a proper session object with all necessary attributes
        from django.contrib.sessions.backends.db import SessionStore
        self.request.session = SessionStore()
        self.request.session.create()
        self.request.session.modified = False

    def test_process_request_unauthenticated_user_does_nothing(self):
        """
        Test that middleware does nothing for unauthenticated users.
        """
        self.request.user = AnonymousUser()
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert LAST_TOUCH_KEYNAME not in self.request.session

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=None)
    def test_process_request_timeout_disabled_does_nothing(self):
        """
        Test that middleware does nothing when timeout is disabled.
        """
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert LAST_TOUCH_KEYNAME not in self.request.session

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_first_visit_sets_timestamp(self, mock_datetime):
        """
        Test that first visit sets timestamp in session.
        """
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        with self.assertLogs('openedx.core.djangoapps.session_inactivity_timeout.middleware', level='DEBUG') as log:
            response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()
        assert self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] == mock_now.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_within_timeout_updates_timestamp(self, mock_datetime):
        """
        Test that request within timeout period and updates timestamp.
        """
        # Set up existing timestamp (5 minutes ago)
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 4, 0)  # 4 minutes later
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
        # Should not log out user
        assert hasattr(self.request, 'user')

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_process_request_timeout_exceeded_logs_out_user(self, mock_auth, mock_datetime):
        """
        Test that request exceeding timeout period logs out user.
        """
        # Set up existing timestamp (10 minutes ago)
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 10, 0)  # 10 minutes later
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        
        # Mock all datetime.utcnow() calls to return current_time
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        # The middleware deletes the key before logging out
        assert LAST_TOUCH_KEYNAME not in self.request.session
        mock_auth.logout.assert_called_once_with(self.request)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_invalid_timestamp_handles_gracefully(self, mock_datetime):
        """
        Test that invalid timestamp in session is handled gracefully.
        """
        # Set up invalid timestamp
        self.request.session[LAST_TOUCH_KEYNAME] = "invalid-timestamp"
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        # Should set new timestamp despite invalid old one
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()

    @override_settings(
        SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=900,  # 15 minutes timeout
        SESSION_ACTIVITY_SAVE_DELAY_SECONDS=600  # 10 minutes save frequency
    )
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_session_save_frequency_within_period(self, mock_datetime):
        """
        Test that session.modified is set to False when within save frequency period.
        """
        # Set up times
        last_save = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 5, 0)  # 5 minutes later (< 10 min frequency, < 15 min timeout)
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_save.isoformat()
        self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] = last_save.isoformat()
        
        # Mock datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session.modified is False

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=3600)  # 1 hour  
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_session_save_frequency_exceeded(self, mock_datetime):
        """
        Test that session save time is updated when frequency period is exceeded.
        """
        # Set up times - Note: we need 60+ seconds difference for the save frequency to be exceeded  
        last_save = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 11, 0)  # 11 minutes (660 seconds) later

        self.request.session[LAST_TOUCH_KEYNAME] = last_save.isoformat()
        # DON'T set LAST_SESSION_SAVE_TIME_KEYNAME - let the "not last_save" condition trigger

        # Mock datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat

        response = self.middleware.process_request(self.request)

        assert response is None
        assert self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] == current_time.isoformat()
        # session.modified should not be explicitly set to False

    @override_settings(
        SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300,
        SESSION_SAVE_FREQUENCY_SECONDS=600
    )
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_no_last_save_time_sets_new_save_time(self, mock_datetime):
        """
        Test that when no last save time exists, a new one is set.
        """
        current_time = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] == current_time.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_type_error_in_timestamp_parsing(self, mock_datetime):
        """
        Test that TypeError in timestamp parsing is handled gracefully.
        """
        # Set up session with non-string value that would cause TypeError
        self.request.session[LAST_TOUCH_KEYNAME] = 12345  # Not a string
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        # Should set new timestamp despite type error
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_process_request_exact_timeout_logs_out_user(self, mock_auth, mock_datetime):
        """
        Test that request just after timeout period logs out user.
        """
        # Set up existing timestamp just over 300 seconds ago
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 5, 1)  # 301 seconds later (> 300)
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        
        # Mock datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert LAST_TOUCH_KEYNAME not in self.request.session
        mock_auth.logout.assert_called_once_with(self.request)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_process_request_one_second_before_timeout_does_not_logout(self, mock_auth, mock_datetime):
        """
        Test that request one second before timeout does not log out user.
        """
        # Set up existing timestamp 299 seconds ago (just under timeout)
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 4, 59)  # 299 seconds later
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
        mock_auth.logout.assert_not_called()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_process_request_exactly_timeout_does_not_logout(self, mock_auth, mock_datetime):
        """
        Test that request at exactly timeout period does NOT log out user (> not >=).
        """
        # Set up existing timestamp exactly 300 seconds ago
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 5, 0)  # Exactly 300 seconds later
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
        mock_auth.logout.assert_not_called()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_uses_default_save_frequency(self, mock_datetime):
        """
        Test that default save frequency (900 seconds) is used when not specified.
        """
        current_time = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] == current_time.isoformat()

    def test_middleware_inherits_from_middleware_mixin(self):
        """
        Test that SessionInactivityTimeout properly inherits from MiddlewareMixin.
        """
        from django.utils.deprecation import MiddlewareMixin
        assert issubclass(SessionInactivityTimeout, MiddlewareMixin)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_empty_session(self, mock_datetime):
        """
        Test that middleware works correctly with completely empty session.
        """
        # Clear the session but keep it as a proper session object
        self.request.session.flush()
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()
        assert self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] == mock_now.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=0)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_process_request_zero_timeout_disables_feature(self, mock_auth, mock_datetime):
        """
        Test that zero timeout disables the timeout feature entirely.
        In Python, 0 is falsy, so `if timeout_in_seconds:` is False.
        """
        # Set up existing timestamp
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 0, 10)  # 10 seconds later
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        
        # Mock all datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        # User should NOT be logged out because 0 timeout disables the feature
        mock_auth.logout.assert_not_called()
        # Original timestamp should remain unchanged
        assert self.request.session[LAST_TOUCH_KEYNAME] == last_touch.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_microsecond_precision_timestamps(self, mock_datetime):
        """
        Test that middleware handles timestamps with microsecond precision.
        """
        # Set up timestamp with microseconds
        last_touch = datetime(2025, 6, 16, 12, 0, 0, 123456)
        current_time = datetime(2025, 6, 16, 12, 2, 0, 654321)
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        
        response = self.middleware.process_request(self.request)
        
        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    def test_constants_are_properly_defined(self):
        """
        Test that the required constants are properly defined.
        """
        assert LAST_TOUCH_KEYNAME == 'SessionInactivityTimeout:last_touch_str'
        assert LAST_SESSION_SAVE_TIME_KEYNAME == 'SessionInactivityTimeout:last_session_save_time'

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=900)  # 15 minutes timeout
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_process_request_session_modified_flag_behavior(self, mock_datetime):
        """
        Test the session.modified flag behavior under different conditions.
        """
        current_time = datetime(2025, 6, 16, 12, 0, 0)
        
        # Mock datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # First request - should not set modified to False
        response = self.middleware.process_request(self.request)
        assert response is None
        # Default behavior for new session data
        
        # Second request within save frequency - should set modified to False
        with override_settings(SESSION_ACTIVITY_SAVE_DELAY_SECONDS=600):
            self.request.session[LAST_SESSION_SAVE_TIME_KEYNAME] = current_time.isoformat()
            response = self.middleware.process_request(self.request)
            assert response is None
            assert self.request.session.modified is False


class SessionInactivityTimeoutLoggingTestCase(TestCase):
    """
    Test cases specifically for logging behavior.
    """

    def setUp(self):
        """
        Set up test data.
        """
        super().setUp()
        self.user = UserFactory.create()
        self.middleware = SessionInactivityTimeout(get_response=lambda request: None)
        self.request = get_mock_request(self.user)
        
        # Create a proper session object with all necessary attributes
        from django.contrib.sessions.backends.db import SessionStore
        self.request.session = SessionStore()
        self.request.session.create()
        self.request.session.modified = False

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    def test_logging_first_login_message(self):
        """
        Test that first login message is logged appropriately.
        """
        with self.assertLogs('openedx.core.djangoapps.session_inactivity_timeout.middleware', level='DEBUG') as log:
            self.middleware.process_request(self.request)
        
        assert len(log.output) == 1
        assert "No previous activity timestamp found (first login)" in log.output[0]
        assert "DEBUG" in log.output[0]

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    def test_no_logging_for_normal_requests(self, mock_datetime):
        """
        Test that normal requests (not first login) don't generate log messages.
        """
        # Set up existing timestamp
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 2, 0)
        
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        
        # Process request - should not generate any logs
        response = self.middleware.process_request(self.request)
        assert response is None


class SessionInactivityTimeoutIntegrationTestCase(TestCase):
    """
    Integration test cases for SessionInactivityTimeout middleware.
    """

    def setUp(self):
        """
        Set up test data.
        """
        super().setUp()
        self.user = UserFactory.create()
        self.factory = RequestFactory()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    def test_integration_with_django_session_framework(self):
        """
        Test integration with Django's session framework.
        """
        from django.contrib.sessions.middleware import SessionMiddleware
        
        # Create a request
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Process through session middleware first
        session_middleware = SessionMiddleware(get_response=lambda request: None)
        session_middleware.process_request(request)
        
        # Process through our middleware
        timeout_middleware = SessionInactivityTimeout(get_response=lambda request: None)
        response = timeout_middleware.process_request(request)
        
        assert response is None
        assert LAST_TOUCH_KEYNAME in request.session
        assert LAST_SESSION_SAVE_TIME_KEYNAME in request.session

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=1)  # Very short timeout
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime')
    @patch('openedx.core.djangoapps.session_inactivity_timeout.middleware.auth')
    def test_integration_logout_behavior(self, mock_auth, mock_datetime):
        """
        Test integration of logout behavior with auth system.
        """
        from django.contrib.sessions.middleware import SessionMiddleware
        
        # Create a request
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Set up session
        session_middleware = SessionMiddleware(get_response=lambda request: None)
        session_middleware.process_request(request)
        
        # Set up existing timestamp (3 seconds ago, which exceeds 1-second timeout)
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = datetime(2025, 6, 16, 12, 0, 3)
        
        request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        
        # Mock datetime methods properly
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Process through our middleware
        timeout_middleware = SessionInactivityTimeout(get_response=lambda request: None)
        response = timeout_middleware.process_request(request)
        
        assert response is None
        assert LAST_TOUCH_KEYNAME not in request.session
        mock_auth.logout.assert_called_once_with(request)
