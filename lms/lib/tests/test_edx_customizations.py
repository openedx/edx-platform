"""
Tests for the edX specific customizations of the LMS
"""
import ddt
import timeit
from unittest import TestCase

from lms.lib.edx_customizations import newrelic_single_app_name_suffix_handler


@ddt.ddt
class EdxCustomizationsTests(TestCase):
    """
    Tests for the edX specific customizations for the LMS
    """

    @ddt.data(
        ('/api-admin/api/v1/api_access_request', 'bom-squad'),
        ('/api-admin/api/v1/api_access_request/', 'bom-squad'),
        ('/api-admin/api/v1/other/', None),
    )
    @ddt.unpack
    def test_newrelic_single_app_name_suffix_handler(self, request_path, expected_suffix):
        """
        Tests the mappings from request_path to suffix.
        """
        actual_suffix = newrelic_single_app_name_suffix_handler(request_path)
        self.assertEqual(expected_suffix, actual_suffix)

    def test_unmapped_mapping_handler_speed(self):
        """
        Tests the performance of a path that is unmapped.

        Note: This time is unaccounted for in NewRelic, so we need this to be fast.
            Exactly how fast is another question, so the assertion is flexible.
        """
        unmapped_path = '/api-admin/api/v1/api_access_requests'  # Note: 's' at end makes it unmapped
        self.assertIsNone(newrelic_single_app_name_suffix_handler(unmapped_path))
        time = timeit.timeit(lambda: newrelic_single_app_name_suffix_handler(unmapped_path), number=1000)
        self.assertTrue(time < 0.005, 'Mapping is too slow for 1000 transactions.')
