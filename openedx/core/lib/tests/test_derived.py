"""
Tests for derived.py
"""


import sys
from unittest import TestCase
from openedx.core.lib.derived import derived, derived_collection_entry, derive_settings, clear_for_tests


class TestDerivedSettings(TestCase):
    """
    Test settings that are derived from other settings.
    """
    def setUp(self):
        super(TestDerivedSettings, self).setUp()
        clear_for_tests()
        self.module = sys.modules[__name__]
        self.module.SIMPLE_VALUE = 'paneer'
        self.module.DERIVED_VALUE = lambda settings: 'mutter ' + settings.SIMPLE_VALUE
        self.module.ANOTHER_DERIVED_VALUE = lambda settings: settings.DERIVED_VALUE + ' with naan'
        self.module.UNREGISTERED_DERIVED_VALUE = lambda settings: settings.SIMPLE_VALUE + ' is cheese'
        derived('DERIVED_VALUE', 'ANOTHER_DERIVED_VALUE')
        self.module.DICT_VALUE = {}
        self.module.DICT_VALUE['test_key'] = lambda settings: settings.DERIVED_VALUE * 3
        derived_collection_entry('DICT_VALUE', 'test_key')
        self.module.DICT_VALUE['list_key'] = ['not derived', lambda settings: settings.DERIVED_VALUE]
        derived_collection_entry('DICT_VALUE', 'list_key', 1)

    def test_derived_settings_are_derived(self):
        derive_settings(__name__)
        self.assertEqual(self.module.DERIVED_VALUE, 'mutter paneer')
        self.assertEqual(self.module.ANOTHER_DERIVED_VALUE, 'mutter paneer with naan')

    def test_unregistered_derived_settings(self):
        derive_settings(__name__)
        self.assertTrue(callable(self.module.UNREGISTERED_DERIVED_VALUE))

    def test_derived_settings_overridden(self):
        self.module.DERIVED_VALUE = 'aloo gobi'
        derive_settings(__name__)
        self.assertEqual(self.module.DERIVED_VALUE, 'aloo gobi')
        self.assertEqual(self.module.ANOTHER_DERIVED_VALUE, 'aloo gobi with naan')

    def test_derived_dict_settings(self):
        derive_settings(__name__)
        self.assertEqual(self.module.DICT_VALUE['test_key'], 'mutter paneermutter paneermutter paneer')

    def test_derived_nested_settings(self):
        derive_settings(__name__)
        self.assertEqual(self.module.DICT_VALUE['list_key'][1], 'mutter paneer')
