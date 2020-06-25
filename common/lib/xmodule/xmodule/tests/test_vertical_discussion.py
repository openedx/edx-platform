"""
Tests discussion functions used in sequence and vertical xmodules.
"""
# pylint: disable=no-member


import ddt
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml


@ddt.ddt
class DiscussionTest(XModuleXmlImportTest):
    """
    Class for tests related to Discussion.
    """

    def setUp(self):
        super(DiscussionTest, self).setUp()
        # construct module
        course = xml.CourseFactory.build()

        chapter_1 = xml.ChapterFactory.build(parent=course)  # has 2 child sequences
        xml.ChapterFactory.build(parent=course)  # has 0 child sequences
        chapter_3 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence
        chapter_4 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence

        xml.SequenceFactory.build(parent=chapter_1)
        xml.SequenceFactory.build(parent=chapter_1)
        sequence_3_1 = xml.SequenceFactory.build(parent=chapter_3)  # has 3 verticals
        sequence_4_1 = xml.SequenceFactory.build(parent=chapter_4)  # has 1 verticals

        for _ in range(3):
            xml.VerticalFactory.build(parent=sequence_3_1)

        vertical_4_1_1 = xml.VerticalFactory.build(parent=sequence_4_1)  # has 2 htmls

        xml.HtmlFactory(parent=vertical_4_1_1)
        xml.HtmlFactory(parent=vertical_4_1_1)

        self.course = self.process_xml(course)

        for chapter_index in range(len(self.course.get_children())):
            chapter = self.course.get_children()[chapter_index]
            setattr(self, 'chapter_{}'.format(chapter_index + 1), chapter)

            for sequence_index in range(len(chapter.get_children())):
                sequence = chapter.get_children()[sequence_index]
                setattr(self, 'sequence_{}_{}'.format(chapter_index + 1, sequence_index + 1), sequence)

                for vertical_index in range(len(sequence.get_children())):
                    vertical = sequence.get_children()[vertical_index]
                    setattr(
                        self, 'vertical_{}_{}_{}'.format(chapter_index + 1,
                        sequence_index + 1, vertical_index + 1), vertical
                    )

    def test_verticals_disable_initially(self):
        """
        Tests that when a vertical is created then by default discussion is disable.
        """

        self.assertFalse(self.vertical_3_1_1.get_discussion_status())
        self.assertFalse(self.vertical_3_1_2.get_discussion_status())
        self.assertFalse(self.vertical_3_1_3.get_discussion_status())
        self.assertFalse(self.vertical_4_1_1.get_discussion_status())

    def test_verticals_disable_get_sequence_return_disable(self):
        """
        Tests that when all the verticals part of a sequence have discussions disable
        then sequence of those verticals also have discussion disable.
        If a sequence has no vertical then its enable by default.
        """
        self.assertTrue(self.sequence_1_1.get_discussion_status())
        self.assertTrue(self.sequence_1_2.get_discussion_status())
        self.assertFalse(self.sequence_3_1.get_discussion_status())
        self.assertFalse(self.sequence_4_1.get_discussion_status())

    def test_verticals_disable_get_chapter_return_disable(self):
        """
        Tests that when all the verticals part of a chapter have discussions disable
        then chapter of those verticals also have discussion disable.
        If a chapter has no vertical then its enable by default.
        """

        self.assertTrue(self.chapter_1.get_discussion_status())
        self.assertTrue(self.chapter_2.get_discussion_status())
        self.assertFalse(self.chapter_3.get_discussion_status())
        self.assertFalse(self.chapter_4.get_discussion_status())

    def test_not_all_verticals_enable_get_sequence_return_disable(self):
        """
        Tests that when not all the verticals part of a sequence have discussions enable
        then sequence of those verticals have discussion disable.
        """
        self.vertical_3_1_1.set_discussion_status(True)
        self.vertical_3_1_2.set_discussion_status(True)

        self.assertFalse(self.sequence_3_1.get_discussion_status())

    def test_verticals_enable_get_sequence_return_enable(self):
        """
        Tests that when all the verticals part of a sequence have discussions enable
        then sequence of those verticals have discussion enable.
        """
        self.vertical_3_1_1.set_discussion_status(True)
        self.vertical_3_1_2.set_discussion_status(True)
        self.vertical_3_1_3.set_discussion_status(True)
        self.vertical_4_1_1.set_discussion_status(True)

        self.assertTrue(self.sequence_3_1.get_discussion_status())
        self.assertTrue(self.sequence_4_1.get_discussion_status())

    def test_verticals_enable_get_chapter_return_enable(self):
        """
        Tests that when all the verticals part of a chapter have discussions enable
        then chapter of those verticals have discussion enable.
        """
        self.vertical_3_1_1.set_discussion_status(True)
        self.vertical_3_1_2.set_discussion_status(True)
        self.vertical_3_1_3.set_discussion_status(True)
        self.vertical_4_1_1.set_discussion_status(True)

        self.assertTrue(self.chapter_3.get_discussion_status())
        self.assertTrue(self.chapter_4.get_discussion_status())

    def test_sequence_enable_get_verticals_enable(self):
        """
        Tests that when a sequence discussion is enable then discussion
        of all the verticals of that sequence is also enable.
        """

        self.sequence_3_1.set_discussion_status(True)

        self.assertTrue(self.vertical_3_1_1.get_discussion_status())
        self.assertTrue(self.vertical_3_1_2.get_discussion_status())
        self.assertTrue(self.vertical_3_1_3.get_discussion_status())
        self.assertTrue(self.sequence_3_1.get_discussion_status())

    def test_chapter_enable_get_verticals_and_sequence_enable(self):
        """
        Tests that when a chapter discussion is enable then discussion
        of all the verticals and sequence of that chapter is also enable.
        """

        self.chapter_3.set_discussion_status(True)

        self.assertTrue(self.vertical_3_1_1.get_discussion_status())
        self.assertTrue(self.vertical_3_1_2.get_discussion_status())
        self.assertTrue(self.vertical_3_1_3.get_discussion_status())
