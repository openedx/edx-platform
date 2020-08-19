"""
Tests for ondemand email preferences utils
"""
from datetime import datetime

from django.test import TestCase

from openedx.features.ondemand_email_preferences.utils import get_next_date


class OnDemandEmailPreferencesUtils(TestCase):
    def test_get_next_date(self):
        """
        Test 'get_next_date' by adding some date with number of days, passed as parameters to the function.
        """
        expected_output = '2020-02-22'
        sample_date = datetime.strptime('2020-02-20', '%Y-%m-%d').date()
        actual_output = get_next_date(sample_date, 2)
        self.assertEqual(expected_output, actual_output)
