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
from unittest.mock import call

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

    @ddt.data(
        None,  # No timestamp key in session
        "",    # Empty string timestamp
    )
    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=300)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch(
        "openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils"
    )
    def test_process_request_first_visit_sets_timestamp(
        self, timestamp_value, mock_monitoring, mock_datetime
    ):
        if timestamp_value is not None:
            self.request.session[LAST_TOUCH_KEYNAME] = timestamp_value
        # else: leave the session without the timestamp key (None case)

        mock_now = datetime(2025, 6, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        with self.assertLogs(
            "openedx.core.djangoapps.session_inactivity_timeout.middleware",
            level="DEBUG",
        ) as log:
            response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None
        assert self.request.session[LAST_TOUCH_KEYNAME] == mock_now.isoformat()

        mock_monitoring.set_custom_attribute.assert_has_calls([
            call("session_inactivity.first_login", True),
            call("session_inactivity.activity_seen", mock_now.isoformat()),
            call("session_inactivity.proceed_with_period_save", True),
        ], any_order=True)

    @ddt.data(
        # (timeout_seconds, save_delay_seconds, seconds_elapsed, should_logout)
        # Test timeout behavior
        (300, 900, 240, False),   # 4 minutes, no timeout
        (300, 900, 300, False),   # 5 minutes, no timeout
        (300, 900, 360, True),    # 6 minutes, timeout occurs
        (600, 900, 540, False),   # 9 minutes, no timeout
        (600, 900, 660, True),    # 11 minutes, timeout occurs
        # Test save delay behavior (with long timeout to avoid logout)
        (3600, 900, 600, False),  # 10 min < 15 min save delay, no save
        (3600, 900, 1200, False),  # 20 min > 15 min save delay, save occurs
        (3600, 600, 480, False),  # 8 min < 10 min save delay, no save
        (3600, 600, 720, False),  # 12 min > 10 min save delay, save occurs
    )
    @ddt.unpack
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.auth")
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils")
    def test_process_request_timeout_and_save_behavior(
        self, timeout_seconds, save_delay_seconds, seconds_elapsed, should_logout,
        mock_monitoring, mock_auth, mock_datetime
    ):
        with override_settings(
            SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=timeout_seconds,
            SESSION_ACTIVITY_SAVE_DELAY_SECONDS=save_delay_seconds
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

                should_save = seconds_elapsed > save_delay_seconds

                if should_save:
                    assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
                    mock_monitoring.set_custom_attribute.assert_has_calls([
                        call("session_inactivity.activity_seen", current_time.isoformat()),
                        call("session_inactivity.proceed_with_period_save", True),
                    ], any_order=True)
                else:
                    # Session should not be saved, timestamp remains the same
                    assert self.request.session[LAST_TOUCH_KEYNAME] == last_touch.isoformat()
                    mock_monitoring.set_custom_attribute.assert_any_call(
                        "session_inactivity.proceed_with_period_save", False
                    )

    @ddt.data(
        # (seconds_elapsed, should_save) - testing around default 900 second save delay
        (800, False),   # 13.3 min < 15 min default, no save
        (900, False),   # exactly 15 min default, no save (not exceeded)
        (1000, True),   # 16.7 min > 15 min default, save occurs
    )
    @ddt.unpack
    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=3600)
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.datetime")
    @patch("openedx.core.djangoapps.session_inactivity_timeout.middleware.monitoring_utils")
    def test_process_request_uses_default_save_frequency(
        self, seconds_elapsed, should_save, mock_monitoring, mock_datetime
    ):
        # Don't set SESSION_ACTIVITY_SAVE_DELAY_SECONDS to test default behavior
        last_touch = datetime(2025, 6, 16, 12, 0, 0)
        current_time = last_touch + timedelta(seconds=seconds_elapsed)
        self.request.session[LAST_TOUCH_KEYNAME] = last_touch.isoformat()
        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat = datetime.fromisoformat

        response = self.middleware.process_request(self.request)  # lint-amnesty, pylint: disable=assignment-from-none

        assert response is None

        if should_save:
            # Session should be saved with new timestamp
            assert self.request.session[LAST_TOUCH_KEYNAME] == current_time.isoformat()
            mock_monitoring.set_custom_attribute.assert_any_call(
                "session_inactivity.proceed_with_period_save", True
            )
        else:
            # Session should not be saved, timestamp remains the same
            assert self.request.session[LAST_TOUCH_KEYNAME] == last_touch.isoformat()
            mock_monitoring.set_custom_attribute.assert_any_call(
                "session_inactivity.proceed_with_period_save", False
            )

    @ddt.data(
        # (timeout_seconds, seconds_elapsed, should_logout)
        # Test boundary conditions more precisely
        (300, 299, False),  # 299 sec < 300 sec timeout, no logout
        (300, 300, False),  # exactly 300 sec timeout, no logout (not exceeded)
        (300, 301, True),   # 301 sec > 300 sec timeout, logout occurs
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
