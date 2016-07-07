"""Tests covering time zone utilities."""
from freezegun import freeze_time
from student.tests.factories import UserFactory
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.lib.time_zone_utils import (
    get_formatted_time_zone, get_time_zone_abbr, get_time_zone_offset, get_user_time_zone
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

    def test_get_user_time_zone(self):
        """
        Test to ensure get_user_time_zone() returns the correct time zone
        or UTC if user has not specified time zone.
        """
        # User time zone should be UTC when no time zone has been chosen
        user_tz = get_user_time_zone(self.user)
        self.assertEqual(user_tz, utc)

        # User time zone should change when user specifies time zone
        set_user_preference(self.user, 'time_zone', 'Asia/Tokyo')
        user_tz = get_user_time_zone(self.user)
        self.assertEqual(user_tz, timezone('Asia/Tokyo'))

    def _formatted_time_zone_helper(self, time_zone_string):
        """
        Helper function to return all info from get_formatted_time_zone()
        """
        time_zone = timezone(time_zone_string)
        tz_str = get_formatted_time_zone(time_zone)
        tz_abbr = get_time_zone_abbr(time_zone)
        tz_offset = get_time_zone_offset(time_zone)

        return {'str': tz_str, 'abbr': tz_abbr, 'offset': tz_offset}

    def _assert_time_zone_info_equal(self, formatted_tz_info, expected_name, expected_abbr, expected_offset):
        """
        Asserts that all formatted_tz_info is equal to the expected inputs
        """
        self.assertEqual(formatted_tz_info['str'], '{name} ({abbr}, UTC{offset})'.format(name=expected_name,
                                                                                         abbr=expected_abbr,
                                                                                         offset=expected_offset))
        self.assertEqual(formatted_tz_info['abbr'], expected_abbr)
        self.assertEqual(formatted_tz_info['offset'], expected_offset)

    @freeze_time("2015-02-09")
    def test_formatted_time_zone_without_dst(self):
        """
        Test to ensure get_formatted_time_zone() returns full formatted string when no kwargs specified
        and returns just abbreviation or offset when specified
        """
        tz_info = self._formatted_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')

    @freeze_time("2015-04-02")
    def test_formatted_time_zone_with_dst(self):
        """
        Test to ensure get_formatted_time_zone() returns modified abbreviations and
        offsets during daylight savings time.
        """
        tz_info = self._formatted_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    @freeze_time("2015-11-01 08:59:00")
    def test_formatted_time_zone_ambiguous_before(self):
        """
        Test to ensure get_formatted_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) before the change
        """
        tz_info = self._formatted_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PDT', '-0700')

    @freeze_time("2015-11-01 09:00:00")
    def test_formatted_time_zone_ambiguous_after(self):
        """
        Test to ensure get_formatted_time_zone() returns correct abbreviations and offsets
        during ambiguous time periods (e.g. when DST is about to start/end) after the change
        """
        tz_info = self._formatted_time_zone_helper('America/Los_Angeles')
        self._assert_time_zone_info_equal(tz_info, 'America/Los Angeles', 'PST', '-0800')
