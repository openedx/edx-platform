"""
Tests that policy json files import correctly when loading XML
"""

from nose.tools import assert_equals, assert_raises  # pylint: disable=no-name-in-module

from xmodule.tests.xml.factories import CourseFactory
from xmodule.tests.xml import XModuleXmlImportTest


class TestPolicy(XModuleXmlImportTest):
    """
    Tests that policy json files import correctly when loading xml
    """
    def test_no_attribute_mapping(self):
        # Policy files are json, and thus the values aren't passed through 'deserialize_field'
        # Therefor, the string 'null' is passed unchanged to the Float field, which will trigger
        # a ValueError
        with assert_raises(ValueError):
            course = self.process_xml(CourseFactory.build(policy={'days_early_for_beta': 'null'}))

            # Trigger the exception by looking at the imported data
            course.days_early_for_beta  # pylint: disable=pointless-statement

    def test_course_policy(self):
        course = self.process_xml(CourseFactory.build(policy={'days_early_for_beta': None}))
        assert_equals(None, course.days_early_for_beta)

        course = self.process_xml(CourseFactory.build(policy={'days_early_for_beta': 9}))
        assert_equals(9, course.days_early_for_beta)
