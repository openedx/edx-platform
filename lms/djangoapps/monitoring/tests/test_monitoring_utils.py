"""
Tests for the LMS monitoring middleware

Note: File named test_monitoring_utils.py instead of test_utils.py because of an error
in Jenkins with test collection and a conflict with another test_utils.py file.

"""
import ddt
import timeit
from django.test import override_settings
from mock import call, patch, Mock
from unittest import TestCase

from lms.djangoapps.monitoring.utils import (
    _process_code_owner_mappings,
    get_code_owner_from_module,
    is_code_owner_mappings_configured,
)


@ddt.ddt
class MonitoringUtilsTests(TestCase):
    """
    Tests for the LMS monitoring utility functions
    """
    @override_settings(CODE_OWNER_MAPPINGS=None)
    def test_is_config_loaded_with_no_config(self):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            self.assertFalse(is_code_owner_mappings_configured(), "Mappings should not be configured.")

    @override_settings(CODE_OWNER_MAPPINGS={'team-red': ['openedx.core.djangoapps.xblock']})
    def test_is_config_loaded_with_valid_dict(self):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            self.assertTrue(is_code_owner_mappings_configured(), "Mappings should be configured.")

    @override_settings(CODE_OWNER_MAPPINGS=['invalid_setting_as_list'])
    def test_is_config_loaded_with_invalid_dict(self):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            self.assertTrue(is_code_owner_mappings_configured(), "Although invalid, mappings should be configured.")

    @override_settings(CODE_OWNER_MAPPINGS={
        'team-red': [
            'openedx.core.djangoapps.xblock',
            'lms.djangoapps.grades',
        ],
        'team-blue': [
            'common.djangoapps.xblock_django',
        ],
    })
    @ddt.data(
        ('xbl', None),
        ('xblock_2', None),
        ('xblock', 'team-red'),
        ('openedx.core.djangoapps', None),
        ('openedx.core.djangoapps.xblock', 'team-red'),
        ('openedx.core.djangoapps.xblock.views', 'team-red'),
        ('grades', 'team-red'),
        ('lms.djangoapps.grades', 'team-red'),
        ('xblock_django', 'team-blue'),
        ('common.djangoapps.xblock_django', 'team-blue'),
    )
    @ddt.unpack
    def test_code_owner_mapping_hits_and_misses(self, module, expected_owner):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            actual_owner = get_code_owner_from_module(module)
            self.assertEqual(expected_owner, actual_owner)

    @override_settings(CODE_OWNER_MAPPINGS=['invalid_setting_as_list'])
    def test_load_config_with_invalid_dict(self):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            self.assertTrue(is_code_owner_mappings_configured(), "Although invalid, mappings should be configured.")
            with self.assertRaises(AssertionError):
                get_code_owner_from_module('xblock')

    def test_mapping_performance(self):
        code_owner_mappings = {
            'team-red': []
        }
        # create a long list of mappings that are nearly identical
        for n in range(1, 200):
            path = 'openedx.core.djangoapps.{}'.format(n)
            code_owner_mappings['team-red'].append(path)
        with override_settings(CODE_OWNER_MAPPINGS=code_owner_mappings):
            with patch(
                'lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()
            ):
                call_iterations = 100
                time = timeit.timeit(
                    # test a module name that matches nearly to the end, but doesn't actually match
                    lambda: get_code_owner_from_module('openedx.core.djangoapps.XXX.views'), number=call_iterations
                )
                average_time = time / call_iterations
                self.assertTrue(average_time < 0.0005, 'Mapping takes {}s which is too slow.'.format(average_time))
