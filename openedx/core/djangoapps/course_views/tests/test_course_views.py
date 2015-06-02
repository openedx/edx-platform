""" Tests of specific tabs. """

from mock import patch, Mock
from unittest import TestCase

import xmodule.tabs as xmodule_tabs

from openedx.core.djangoapps.course_views.course_views import CourseViewTypeManager


class CourseViewTypeManagerTestCase(TestCase):
    """Test cases for CourseViewTypeManager class"""

    @patch('openedx.core.djangoapps.course_views.course_views.CourseViewTypeManager.get_available_plugins')
    def test_get_course_view_types(self, get_available_plugins):
        """
        Verify that get_course_view_types sorts appropriately
        """
        def create_mock_plugin(name, priority):
            """ Create a mock plugin with the specified name and priority. """
            mock_plugin = Mock()
            mock_plugin.name = name
            mock_plugin.priority = priority
            return mock_plugin
        mock_plugins = {
            "Last": create_mock_plugin(name="Last", priority=None),
            "Duplicate1": create_mock_plugin(name="Duplicate", priority=None),
            "Duplicate2": create_mock_plugin(name="Duplicate", priority=None),
            "First": create_mock_plugin(name="First", priority=1),
            "Second": create_mock_plugin(name="Second", priority=1),
            "Third": create_mock_plugin(name="Third", priority=3),
        }
        get_available_plugins.return_value = mock_plugins
        self.assertEqual(
            [plugin.name for plugin in CourseViewTypeManager.get_course_view_types()],
            ["First", "Second", "Third", "Duplicate", "Duplicate", "Last"]
        )


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
