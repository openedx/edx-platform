"""Tests covering time zone utilities."""


from datetime import datetime

import ddt
from pytz import timezone as pytz_timezone, UTC as pytz_UTC, common_timezones
from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from zoneinfo import ZoneInfo, available_timezones as zoneinfo_available_timezones
from openedx.core.lib.time_zone_utils import (
    get_display_time_zone,
    get_time_zone_abbr,
    get_time_zone_offset,
    get_utc_timezone,
    get_available_timezones
)
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class TestTimeZoneUtils(TestCase):
    """
    Tests the time zone utilities
    """
    def setUp(self):
        """
        Sets up user for testing with time zone utils.
        """
        super().setUp()

        self.user = UserFactory.build()
        self.user.save()

    def _display_time_zone_helper(self, time_zone_string, date_time=None):
        """
        Helper function to return all info from individual functions with explicit datetime
        """
        time_zone = ZoneInfo(time_zone_string)
        tz_abbr = get_time_zone_abbr(time_zone, date_time)
        tz_offset = get_time_zone_offset(time_zone, date_time)

        return {'abbr': tz_abbr, 'offset': tz_offset}

    def _assert_time_zone_info_equal(self, display_tz_info, expected_abbr, expected_offset):
        """
        Asserts that display_tz_info is equal to the expected inputs
        """
        assert display_tz_info['abbr'] == expected_abbr
        assert display_tz_info['offset'] == expected_offset

    # Tests for toggle-based timezone selection
    @ddt.data(
        (True, ZoneInfo),  # ZoneInfo enabled
        (False, 'pytz.UTC'),  # ZoneInfo disabled
    )
    @ddt.unpack
    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_utc_timezone(self, toggle_enabled, expected_type, mock_toggle):
        """Test get_utc_timezone returns correct timezone object based on toggle"""
        mock_toggle.is_enabled.return_value = toggle_enabled

        utc_tz = get_utc_timezone()

        if toggle_enabled:
            self.assertIsInstance(utc_tz, ZoneInfo)
            self.assertEqual(str(utc_tz), 'UTC')
        else:
            self.assertEqual(utc_tz, pytz_UTC)

    @ddt.data(
        (True, 'zoneinfo'),  # ZoneInfo enabled
        (False, 'pytz'),     # ZoneInfo disabled
    )
    @ddt.unpack
    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_available_timezones(self, toggle_enabled, expected_source, mock_toggle):
        """
        Test get_available_timezones returns correct timezone list based on toggle.

        Note: When using zoneinfo, this returns available_timezones() which is a superset
        of pytz.common_timezones (599 vs 433 timezones). This is an intentional change
        to provide access to all available timezones, not just the "common" ones.
        We verify that all legacy common_timezones are still available to ensure
        backward compatibility.
        """
        mock_toggle.is_enabled.return_value = toggle_enabled

        timezones = get_available_timezones()
        if toggle_enabled:
            self.assertEqual(timezones, zoneinfo_available_timezones())

            timezone_strings = set(timezones)
            common_timezone_strings = set(common_timezones)

            missing_timezones = common_timezone_strings - timezone_strings
            self.assertEqual(
                missing_timezones,
                set(),
                f"These common timezones are missing from zoneinfo: {missing_timezones}"
            )

            self.assertGreater(
                len(timezone_strings),
                len(common_timezone_strings),
                "zoneinfo should provide more timezones than pytz.common_timezones"
            )
        else:
            self.assertEqual(timezones, common_timezones)

    @ddt.data(
        (True, 'zoneinfo'),  # ZoneInfo enabled
        (False, 'pytz'),     # ZoneInfo disabled
    )
    @ddt.unpack
    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_display_time_zone_with_toggle(self, toggle_enabled, expected_source, mock_toggle):
        """Test get_display_time_zone works correctly with both implementations"""
        mock_toggle.is_enabled.return_value = toggle_enabled

        with freeze_time("2015-02-09"):
            result = get_display_time_zone('America/Los_Angeles')
            expected = 'America/Los Angeles (PST, UTC-0800)'
            self.assertEqual(result, expected)

    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_mixed_timezone_types_work(self, mock_toggle):
        """Test that mixing pytz and ZoneInfo timezone types works correctly"""
        # Test with ZoneInfo datetime and pytz timezone
        mock_toggle.is_enabled.return_value = True
        zoneinfo_dt = datetime.now(get_utc_timezone())
        pytz_tz = pytz_timezone('America/New_York')
        result1 = get_time_zone_abbr(pytz_tz, zoneinfo_dt)
        self.assertIsNotNone(result1)  # Should not raise an exception

        # Test with pytz datetime and ZoneInfo timezone
        mock_toggle.is_enabled.return_value = False
        pytz_dt = datetime.now(get_utc_timezone())
        zoneinfo_tz = ZoneInfo('America/New_York')
        result2 = get_time_zone_abbr(zoneinfo_tz, pytz_dt)
        self.assertIsNotNone(result2)  # Should not raise an exception

    def test_display_time_zone_without_dst(self):
        """
        Test to ensure get_time_zone_abbr() and get_time_zone_offset() return correct values
        when not in daylight savings time
        """
        with patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ') as mock_toggle:
            mock_toggle.is_enabled.return_value = True
            test_dt = datetime(2015, 2, 9, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
            tz_info = self._display_time_zone_helper('America/Los_Angeles', test_dt)
            self._assert_time_zone_info_equal(tz_info, 'PST', '-0800')

    def test_display_time_zone_with_dst(self):
        """
        Test to ensure get_time_zone_abbr() and get_time_zone_offset() return modified
        abbreviations and offsets during daylight savings time.
        """
        with patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ') as mock_toggle:
            mock_toggle.is_enabled.return_value = True
            test_dt = datetime(2015, 4, 2, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
            tz_info = self._display_time_zone_helper('America/Los_Angeles', test_dt)
            self._assert_time_zone_info_equal(tz_info, 'PDT', '-0700')

    def test_display_time_zone_ambiguous_before(self):
        """
        Test to ensure get_time_zone_abbr() and get_time_zone_offset() return correct
        abbreviations and offsets during ambiguous time periods (e.g. when DST is about
        to start/end) before the change
        """
        with patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ') as mock_toggle:
            mock_toggle.is_enabled.return_value = True
            # UTC 08:59 = 01:59 PDT (before DST ends at 02:00)
            test_dt = datetime(2015, 11, 1, 8, 59, 0, tzinfo=ZoneInfo('UTC'))
            tz_info = self._display_time_zone_helper('America/Los_Angeles', test_dt)
            self._assert_time_zone_info_equal(tz_info, 'PDT', '-0700')

    def test_display_time_zone_ambiguous_after(self):
        """
        Test to ensure get_time_zone_abbr() and get_time_zone_offset() return correct
        abbreviations and offsets during ambiguous time periods (e.g. when DST is about
        to start/end) after the change
        """
        with patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ') as mock_toggle:
            mock_toggle.is_enabled.return_value = True
            # UTC 09:00 = 01:00 PST (after DST ends, clocks fall back)
            test_dt = datetime(2015, 11, 1, 9, 0, 0, tzinfo=ZoneInfo('UTC'))
            tz_info = self._display_time_zone_helper('America/Los_Angeles', test_dt)
            self._assert_time_zone_info_equal(tz_info, 'PST', '-0800')
