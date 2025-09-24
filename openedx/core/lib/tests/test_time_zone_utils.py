"""Tests covering time zone utilities."""


import ddt
from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from zoneinfo import ZoneInfo
from openedx.core.lib.time_zone_utils import (
    get_display_time_zone,
    get_time_zone_abbr,
    get_time_zone_offset,
    get_utc_timezone,
    get_common_timezones
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

    def _display_time_zone_helper(self, time_zone_string):
        """
        Helper function to return all info from get_display_time_zone()
        """
        tz_str = get_display_time_zone(time_zone_string)
        time_zone = ZoneInfo(time_zone_string)
        tz_abbr = get_time_zone_abbr(time_zone)
        tz_offset = get_time_zone_offset(time_zone)

        return {'str': tz_str, 'abbr': tz_abbr, 'offset': tz_offset}

    def _assert_time_zone_info_equal(self, display_tz_info, expected_name, expected_abbr, expected_offset):
        """
        Asserts that all display_tz_info is equal to the expected inputs
        """
        assert display_tz_info['str'] == '{name} ({abbr}, UTC{offset})'.format(
            name=expected_name, abbr=expected_abbr, offset=expected_offset
        )
        assert display_tz_info['abbr'] == expected_abbr
        assert display_tz_info['offset'] == expected_offset

    # New tests for newly added functions
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
            from pytz import UTC
            self.assertEqual(utc_tz, UTC)

    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_utc_timezone_fallback_on_exception(self, mock_toggle):
        """Test get_utc_timezone falls back to pytz UTC when toggle check fails"""
        mock_toggle.is_enabled.side_effect = Exception("Toggle check failed")

        utc_tz = get_utc_timezone()

        # Should fallback to pytz UTC
        from pytz import UTC
        self.assertEqual(utc_tz, UTC)

    @ddt.data(
        (True, 'zoneinfo'),  # ZoneInfo enabled
        (False, 'pytz'),     # ZoneInfo disabled
    )
    @ddt.unpack
    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_common_timezones(self, toggle_enabled, expected_source, mock_toggle):
        """Test get_common_timezones returns correct timezone list based on toggle"""
        mock_toggle.is_enabled.return_value = toggle_enabled

        timezones = get_common_timezones()

        if toggle_enabled:
            from zoneinfo import available_timezones
            self.assertEqual(timezones, available_timezones())
        else:
            from pytz import common_timezones
            self.assertEqual(timezones, common_timezones)

    @patch('openedx.core.lib.time_zone_utils.ENABLE_ZONEINFO_TZ')
    def test_get_common_timezones_fallback_on_exception(self, mock_toggle):
        """Test get_common_timezones falls back to pytz when toggle check fails"""
        mock_toggle.is_enabled.side_effect = Exception("Toggle check failed")

        timezones = get_common_timezones()

        from pytz import common_timezones
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
    def test_get_display_time_zone_fallback_on_exception(self, mock_toggle):
        """Test get_display_time_zone falls back to pytz when toggle check fails"""
        mock_toggle.is_enabled.side_effect = Exception("Toggle check failed")

        with freeze_time("2015-02-09"):
            result = get_display_time_zone('America/Los_Angeles')
            expected = 'America/Los Angeles (PST, UTC-0800)'
            self.assertEqual(result, expected)

    def test_display_time_zone_without_dst(self):
        """
        Test to ensure get_display_time_zone() returns full display string when no kwargs specified
        and returns just abbreviation or offset when specified
        """
        with freeze_time("2015-02-09"):
            tz_info = self._display_time_zone_helper('America/Los_Angeles')
            self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')

    def test_display_time_zone_with_dst(self):
        """
        Test to ensure get_display_time_zone() returns modified abbreviations and
        offsets during daylight savings time.
        """
        with freeze_time("2015-04-02"):
            tz_info = self._display_time_zone_helper('America/Los_Angeles')
            self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    def test_display_time_zone_ambiguous_before(self):
        """
        Test to ensure get_display_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) before the change
        """
        with freeze_time("2015-11-01 08:59:00"):
            tz_info = self._display_time_zone_helper('America/Los_Angeles')
            self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    def test_display_time_zone_ambiguous_after(self):
        """
        Test to ensure get_display_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) after the change
        """
        with freeze_time("2024-11-04 09:00:00"):
            tz_info = self._display_time_zone_helper('America/Los_Angeles')
            self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')
