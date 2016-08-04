""" Tests of specific tabs. """

from mock import patch, Mock
from nose.plugins.attrib import attr
from unittest import TestCase

import xmodule.tabs as xmodule_tabs

from openedx.core.lib.course_tabs import CourseTabPluginManager


@attr(shard=2)
class CourseTabPluginManagerTestCase(TestCase):
    """Test cases for CourseTabPluginManager class"""

    @patch('openedx.core.lib.course_tabs.CourseTabPluginManager.get_available_plugins')
    def test_get_tab_types(self, get_available_plugins):
        """
        Verify that get_course_view_types sorts appropriately
        """
        def create_mock_plugin(tab_type, priority):
            """ Create a mock plugin with the specified name and priority. """
            mock_plugin = Mock()
            mock_plugin.type = tab_type
            mock_plugin.priority = priority
            return mock_plugin
        mock_plugins = {
            "Last": create_mock_plugin(tab_type="Last", priority=None),
            "Duplicate1": create_mock_plugin(tab_type="Duplicate", priority=None),
            "Duplicate2": create_mock_plugin(tab_type="Duplicate", priority=None),
            "First": create_mock_plugin(tab_type="First", priority=1),
            "Second": create_mock_plugin(tab_type="Second", priority=1),
            "Third": create_mock_plugin(tab_type="Third", priority=3),
        }
        get_available_plugins.return_value = mock_plugins
        self.assertEqual(
            [plugin.type for plugin in CourseTabPluginManager.get_tab_types()],
            ["First", "Second", "Third", "Duplicate", "Duplicate", "Last"]
        )


@attr(shard=2)
class KeyCheckerTestCase(TestCase):
    """Test cases for KeyChecker class"""

    def setUp(self):
        super(KeyCheckerTestCase, self).setUp()

        self.valid_keys = ['a', 'b']
        self.invalid_keys = ['a', 'v', 'g']
        self.dict_value = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertTrue(xmodule_tabs.key_checker(self.valid_keys)(self.dict_value, raise_error=False))
        self.assertFalse(xmodule_tabs.key_checker(self.invalid_keys)(self.dict_value, raise_error=False))
        with self.assertRaises(xmodule_tabs.InvalidTabsException):
            xmodule_tabs.key_checker(self.invalid_keys)(self.dict_value)


@attr(shard=2)
class NeedNameTestCase(TestCase):
    """Test cases for NeedName validator"""

    def setUp(self):
        super(NeedNameTestCase, self).setUp()

        self.valid_dict1 = {'a': 1, 'name': 2}
        self.valid_dict2 = {'name': 1}
        self.valid_dict3 = {'a': 1, 'name': 2, 'b': 3}
        self.invalid_dict = {'a': 1, 'b': 2}

    def test_need_name(self):
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict1))
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict2))
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict3))
        with self.assertRaises(xmodule_tabs.InvalidTabsException):
            xmodule_tabs.need_name(self.invalid_dict)
