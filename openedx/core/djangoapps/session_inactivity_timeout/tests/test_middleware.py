"""
Unit tests for SessionInactivityTimeout middleware.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import ddt
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase, override_settings

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import get_mock_request

from openedx.core.djangoapps.session_inactivity_timeout.middleware import (
    SessionInactivityTimeout,
    LAST_TOUCH_KEYNAME,
)


@ddt.ddt
class SessionInactivityTimeoutTestCase(TestCase):
    """
    Test case for SessionInactivityTimeout middleware
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.middleware = SessionInactivityTimeout(get_response=lambda request: None)
        self.request = get_mock_request(self.user)

        self.request.session = SessionStore()
        self.request.session.create()
        self.request.session.modified = False

    def test_process_request_unauthenticated_user_does_nothing(self):
        self.request.user = AnonymousUser()
        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none
        assert response is None
        assert LAST_TOUCH_KEYNAME not in self.request.session

    @ddt.data(None, 0)
    def test_process_request_timeout_disabled_does_nothing(self, timeout_value):
        with override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=timeout_value):
            response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        assert LAST_TOUCH_KEYNAME not in self.request.session

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch(
        "openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils"
    )
    def test_process_request_first_visit_sets_timestamp(
        self, mock_monitoring, mock_datetime
    ):
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        with self.assertLogs(
            "openedx.core.djangoapps.session_inactivity_timeout.middleware",
            level="DEBUG",
        ) as log:
            response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()

        # Verify monitoring calls
        mock_monitoring.set_custom_attribute.assert_any_call(
            "session_inactivity.first_login", True
        )
        mock_monitoring.set_custom_attribute.assert_any_call(
            "session_inactivity.activity_seen", mock_now.isoformat()
        )
        mock_monitoring.set_custom_attribute.assert_any_call(
            "session_inactivity.last_touch_status", "last-touch-exceeded"
        )

    @ddt.data(
        # (timeout_seconds, minutes_elapsed, should_logout)
        (300, 4, False),
        (300, 6, True),
        (300, 5, False),
        (600, 9, False),
        (600, 11, True),
    )
    @ddt.unpack
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.auth")
    def test_process_request_timeout_behavior(
        self, timeout_seconds, minutes_elapsed, should_logout, mock_auth, mock_datetime
    ):
        with override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=timeout_seconds):
            last_touch = datetime(2025, 6, 16, 12, 0, 0)
            current_time = last_touch + timedelta(minutes=minutes_elapsed)
            self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
            mock_datetime.utcnow.return_value = current_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

            assert response is None

            if should_logout:
                assert LAST_TOUCH_KEYNAME not in self.request.session
                mock_auth.logout.assert_called_once_with(self.request)
            else:
                # User should not be logged out, but timestamp may or may not be updated
                # depending on save delay logic (900 seconds default)
                mock_auth.logout.assert_not_called()
                # The session should contain either the old or new timestamp
                assert LAST_TOUCH_KEYNAME in self.request.session

    @ddt.data(
        # (save_delay_seconds, minutes_elapsed, should_save)
        (900, 10, False),
        (900, 20, True),
        (600, 8, False),
        (600, 12, True),
    )
    @ddt.unpack
    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=3600)  # 1 hour timeout
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch(
        "openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils"
    )
    def test_process_request_save_delay_behavior(
        self,
        save_delay_seconds,
        minutes_elapsed,
        should_save,
        mock_monitoring,
        mock_datetime,
    ):
        with override_settings(SESSION_ACTIVITY_SAVE_DELAY_SECONDS=save_delay_seconds):
            last_touch = datetime(2025, 6, 16, 12, 0, 0)
            current_time = last_touch + timedelta(minutes=minutes_elapsed)
            self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
            mock_datetime.utcnow.return_value = current_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

            assert response is None

            if should_save:
                # Session should be saved with new timestamp
                assert (
                    self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
                )
                mock_monitoring.set_custom_attribute.assert_any_call(
                    "session_inactivity.last_touch_status", "last-touch-exceeded"
                )
            else:
                # Session should not be saved, timestamp remains the same
                assert (
                    self.request.session[LAST_TOUCH_KEYNAME] == last_touch.isoformat()
                )
                mock_monitoring.set_custom_attribute.assert_any_call(
                    "session_inactivity.last_touch_status", "last-touch-not-exceeded"
                )

    @ddt.data(
        "invalid-timestamp",
        12345,  # Not a string
        "2025-13-01T12:00:00",  # Invalid month
    )
    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    def test_process_request_invalid_timestamp_handles_gracefully(
        self, invalid_timestamp, mock_datetime
    ):
        self.request.session[LAST_TOUCH_KEYNAME] = invalid_timestamp
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        with self.assertRaises((ValueError, TypeError)):
            self.middleware.process_request(self.request)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch(
        "openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils"
    )
    def test_process_request_empty_string_timestamp_as_first_login(
        self, mock_monitoring, mock_datetime
    ):
        self.request.session[LAST_TOUCH_KEYNAME] = ""
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        # Empty string is falsy, so it should be treated as first login
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()
        mock_monitoring.set_custom_attribute.assert_any_call(
            "session_inactivity.first_login", True
        )

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    def test_process_request_uses_default_save_frequency(self, mock_datetime):
        current_time = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time

        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    def test_process_request_empty_session(self, mock_datetime):
        # Clear the session but keep it as a proper session object
        self.request.session.flush()
        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()

    @ddt.data(
        # Test boundary conditions more precisely
        (300, 299, False),
        (300, 300, False),
        (300, 301, True),
    )
    @ddt.unpack
    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.auth")
    def test_process_request_timeout_boundary_conditions(
        self, timeout_seconds, seconds_elapsed, should_logout, mock_auth, mock_datetime
    ):
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = last_touch + timedelta(seconds=seconds_elapsed)
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None

        if should_logout:
            assert LAST_TOUCH_KEYNAME not in self.request.session
            mock_auth.logout.assert_called_once_with(self.request)
        else:
            mock_auth.logout.assert_not_called()
            assert LAST_TOUCH_KEYNAME in self.request.session
