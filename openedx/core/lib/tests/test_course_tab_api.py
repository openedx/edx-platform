"""
Tests for the plugin API
"""

from django.test import TestCase
from nose.plugins.attrib import attr

from openedx.core.lib.api.plugins import PluginError
from openedx.core.lib.course_tabs import CourseTabPluginManager


@attr(shard=2)
class TestPluginApi(TestCase):
    """
    Unit tests for the plugin API
    """

    def test_get_plugin(self):
        """
        Verify that get_plugin works as expected.
        """
        tab_type = CourseTabPluginManager.get_plugin("instructor")
        self.assertEqual(tab_type.title, "Instructor")

        with self.assertRaises(PluginError):
            CourseTabPluginManager.get_plugin("no_such_type")
