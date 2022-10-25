"""
Test that inherited fields work correctly when parsing XML
"""


from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml.factories import CourseFactory, ProblemFactory, SequenceFactory, XmlImportFactory


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
        assert course.days_early_for_beta is None

        sequence = course.get_children()[0]
        assert sequence.days_early_for_beta is None

        problem = sequence.get_children()[0]
        assert problem.days_early_for_beta is None

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
        assert 'garbage' in video_block.xml_attributes
