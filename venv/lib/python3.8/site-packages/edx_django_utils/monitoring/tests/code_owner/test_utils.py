"""
Tests for the code_owner monitoring middleware
"""
import timeit
from unittest import TestCase
from unittest.mock import call, patch

import ddt
from django.test import override_settings

from edx_django_utils.monitoring import (
    get_code_owner_from_module,
    set_code_owner_attribute,
    set_code_owner_attribute_from_module
)
from edx_django_utils.monitoring.internal.code_owner.utils import clear_cached_mappings


@set_code_owner_attribute
def decorated_function(pass_through):
    """
    For testing the set_code_owner_attribute decorator.
    """
    return pass_through


@ddt.ddt
class MonitoringUtilsTests(TestCase):
    """
    Tests for the code_owner monitoring utility functions
    """
    def setUp(self):
        super().setUp()
        clear_cached_mappings()

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
        actual_owner = get_code_owner_from_module(module)
        self.assertEqual(expected_owner, actual_owner)

    @override_settings(CODE_OWNER_MAPPINGS=['invalid_setting_as_list'])
    @patch('edx_django_utils.monitoring.internal.code_owner.utils.log')
    def test_code_owner_mapping_with_invalid_dict(self, mock_logger):
        with self.assertRaises(TypeError):
            get_code_owner_from_module('xblock')

        mock_logger.exception.assert_called_with(
            'Error processing CODE_OWNER_MAPPINGS. list indices must be integers or slices, not str',
        )

    def test_code_owner_mapping_with_no_settings(self):
        self.assertIsNone(get_code_owner_from_module('xblock'))

    def test_code_owner_mapping_with_no_module(self):
        self.assertIsNone(get_code_owner_from_module(None))

    def test_mapping_performance(self):
        code_owner_mappings = {
            'team-red': []
        }
        # create a long list of mappings that are nearly identical
        for n in range(1, 200):
            path = f'openedx.core.djangoapps.{n}'
            code_owner_mappings['team-red'].append(path)
        with override_settings(CODE_OWNER_MAPPINGS=code_owner_mappings):
            call_iterations = 100
            time = timeit.timeit(
                # test a module name that matches nearly to the end, but doesn't actually match
                lambda: get_code_owner_from_module('openedx.core.djangoapps.XXX.views'), number=call_iterations
            )
            average_time = time / call_iterations
            self.assertLess(average_time, 0.0005, f'Mapping takes {average_time}s which is too slow.')

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['edx_django_utils.monitoring.tests.code_owner.test_utils']},
        CODE_OWNER_THEMES={'team': ['team-red']},
    )
    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_set_code_owner_attribute_success(self, mock_set_custom_attribute):
        self.assertEqual(decorated_function('test'), 'test')
        self._assert_set_custom_attribute(
            mock_set_custom_attribute, code_owner='team-red', module=__name__, check_theme_and_squad=True
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['edx_django_utils.monitoring.tests.code_owner.test_utils']},
        CODE_OWNER_THEMES='invalid-setting',
    )
    def test_set_code_owner_attribute_with_invalid_setting(self):
        with self.assertRaises(TypeError):
            decorated_function('test')

    @override_settings(CODE_OWNER_MAPPINGS={
        'team-red': ['*']
    })
    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_set_code_owner_attribute_catch_all(self, mock_set_custom_attribute):
        self.assertEqual(decorated_function('test'), 'test')
        self._assert_set_custom_attribute(mock_set_custom_attribute, code_owner='team-red', module=__name__)

    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_set_code_owner_attribute_no_mappings(self, mock_set_custom_attribute):
        self.assertEqual(decorated_function('test'), 'test')
        self._assert_set_custom_attribute(mock_set_custom_attribute, code_owner=None, module=__name__)

    @override_settings(CODE_OWNER_MAPPINGS={
        'team-red': ['edx_django_utils.monitoring.tests.code_owner.test_utils']
    })
    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_set_code_owner_attribute_from_module_success(self, mock_set_custom_attribute):
        set_code_owner_attribute_from_module(__name__)
        self._assert_set_custom_attribute(mock_set_custom_attribute, code_owner='team-red', module=__name__)

    def _assert_set_custom_attribute(self, mock_set_custom_attribute, code_owner, module, check_theme_and_squad=False):
        """
        Helper to assert that the proper set_custom_metric calls were made.
        """
        call_list = []
        if code_owner:
            call_list.append(call('code_owner', code_owner))
            if check_theme_and_squad:
                call_list.append(call('code_owner_theme', code_owner.split('-')[0]))
                call_list.append(call('code_owner_squad', code_owner.split('-')[1]))
        call_list.append(call('code_owner_module', module))
        mock_set_custom_attribute.assert_has_calls(call_list, any_order=True)
