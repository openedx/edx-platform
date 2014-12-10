"""
Test that inherited fields work correctly when parsing XML
"""
from nose.tools import assert_equals, assert_in  # pylint: disable=no-name-in-module

from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml.factories import CourseFactory, SequenceFactory, ProblemFactory, XmlImportFactory


class TestInheritedFieldParsing(XModuleXmlImportTest):
    """
    Test that inherited fields work correctly when parsing XML

    """
    def test_null_string(self):
        # Test that the string inherited fields are passed through 'deserialize_field',
        # which converts the string "null" to the python value None
        root = CourseFactory.build(days_early_for_beta="null")
        sequence = SequenceFactory.build(parent=root)
        ProblemFactory.build(parent=sequence)

        course = self.process_xml(root)
        assert_equals(None, course.days_early_for_beta)

        sequence = course.get_children()[0]
        assert_equals(None, sequence.days_early_for_beta)

        problem = sequence.get_children()[0]
        assert_equals(None, problem.days_early_for_beta)

    def test_video_attr(self):
        """
        Test that video's definition_from_xml handles unknown attrs w/o choking
        """
        # Fixes LMS-11491
        root = CourseFactory.build()
        sequence = SequenceFactory.build(parent=root)
        video = XmlImportFactory(
            parent=sequence,
            tag='video',
            attribs={
                'parent_url': 'foo', 'garbage': 'asdlk',
                'download_video': 'true',
            }
        )
        video_block = self.process_xml(video)
        assert_in('garbage', video_block.xml_attributes)
