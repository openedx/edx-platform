"""Tests covering time zone utilities."""
from freezegun import freeze_time
from student.tests.factories import UserFactory
from openedx.core.lib.time_zone_utils import (
    get_display_time_zone,
    get_time_zone_abbr,
    get_time_zone_offset,
)
from pytz import timezone, utc
from unittest import TestCase


class TestTimeZoneUtils(TestCase):
    """
    Tests the time zone utilities
    """
    def setUp(self):
        """
        Sets up user for testing with time zone utils.
        """
        super(TestTimeZoneUtils, self).setUp()

        self.user = UserFactory.build()
        self.user.save()

    def _display_time_zone_helper(self, time_zone_string):
        """
        Helper function to return all info from get_display_time_zone()
        """
        tz_str = get_display_time_zone(time_zone_string)
        time_zone = timezone(time_zone_string)
        tz_abbr = get_time_zone_abbr(time_zone)
        tz_offset = get_time_zone_offset(time_zone)

        return {'str': tz_str, 'abbr': tz_abbr, 'offset': tz_offset}

    def _assert_time_zone_info_equal(self, display_tz_info, expected_name, expected_abbr, expected_offset):
        """
        Asserts that all display_tz_info is equal to the expected inputs
        """
        self.assertEqual(display_tz_info['str'], '{name} ({abbr}, UTC{offset})'.format(name=expected_name,
                                                                                       abbr=expected_abbr,
                                                                                       offset=expected_offset))
        self.assertEqual(display_tz_info['abbr'], expected_abbr)
        self.assertEqual(display_tz_info['offset'], expected_offset)

    @freeze_time("2015-02-09")
    def test_display_time_zone_without_dst(self):
        """
        Test to ensure get_display_time_zone() returns full display string when no kwargs specified
        and returns just abbreviation or offset when specified
        """
        tz_info = self._display_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')

    @freeze_time("2015-04-02")
    def test_display_time_zone_with_dst(self):
        """
        Test to ensure get_display_time_zone() returns modified abbreviations and
        offsets during daylight savings time.
        """
        tz_info = self._display_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    @freeze_time("2015-11-01 08:59:00")
    def test_display_time_zone_ambiguous_before(self):
        """
        Test to ensure get_display_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) before the change
        """
        tz_info = self._display_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    @freeze_time("2015-11-01 09:00:00")
    def test_display_time_zone_ambiguous_after(self):
        """
        Test to ensure get_display_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) after the change
        """
        tz_info = self._display_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')
