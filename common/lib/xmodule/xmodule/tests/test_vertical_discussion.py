"""
Tests discussion functions used in sequence and vertical xmodules.
"""
# pylint: disable=no-member

import unittest

from .test_course_module import DummySystem as DummyImportSystem

ORG = 'test_org'
COURSE = 'test_course'


class DiscussionTest(unittest.TestCase):
    """
    Discussion Tests

    Terminology

    Course: Course
    Chapter: Section/Chapter
    Subsection: Subsection/Sequential
    Unit: Vertical/Unit
    Block: Block e.g ORA, DnD, HTML, Video, Discussion
    """

    def setUp(self):
        super(DiscussionTest, self).setUp()
        self.system = DummyImportSystem(load_error_modules=True)
        self.course = self.get_dummy_course()
        self.patch_self_with_course_elements(self.course)

    def get_dummy_course(self):
        """
        Create and return a dummy course
        """
        # TODO: Add a vertical with some children in it e.g HTML Block, ORA Block, DnD Block etc.
        # It won't work if there is a child block in it.
        course_xml = """
        <course course="{course}" org="{org}" not_a_pointer="true"
        static_asset_path="xml_test_course" url_name="0" name="101">
            <chapter not_a_pointer="true" url_name="1">
                <sequential not_a_pointer="true" url_name="5"/>
                <sequential not_a_pointer="true" url_name="6"/>
            </chapter>
            <chapter not_a_pointer="true" url_name="2"/>
            <chapter not_a_pointer="true" url_name="3">
                <sequential not_a_pointer="true" url_name="7">
                    <vertical not_a_pointer="true" url_name="9"/>
                    <vertical not_a_pointer="true" url_name="10"/>
                    <vertical not_a_pointer="true" url_name="11"/>
                </sequential>
            </chapter>
            <chapter not_a_pointer="true" url_name="4">
                <sequential not_a_pointer="true" url_name="8">
                    <vertical not_a_pointer="true" url_name="12" display_name="test"/>
                </sequential>
            </chapter>
        </course>""".format(org=ORG, course=COURSE)
        return self.system.process_xml(course_xml)

    def patch_self_with_course_elements(self, element_root, indexes=None):
        """
        It recursively adds chapters, section, verticals, blocks to self for easier access starting from element_root
        """
        indexes = indexes or []  # if indexes is False/None/"empty iterable" it would default to empty list i.e []
        for element_i, element in [(str(i), element) for i, element in enumerate(element_root.get_children(), 1)]:
            setattr(self, "_".join([element.xml_element_name(), *indexes, element_i]), element)
            self.patch_self_with_course_elements(element, indexes + [element_i])

    def test_verticals_disable_initially(self):
        """
        Tests that when a vertical is created then by default discussion is disabled.
        """

        self.assertFalse(self.vertical_3_1_1.discussion_enabled)
        self.assertFalse(self.vertical_3_1_2.discussion_enabled)
        self.assertFalse(self.vertical_3_1_3.discussion_enabled)
        self.assertFalse(self.vertical_4_1_1.discussion_enabled)

    def test_verticals_disable_get_sequence_return_disable(self):
        """
        Tests that when all the verticals of a sequential have discussions disabled then sequential of those verticals
        also have discussion disable. If a sequential has no vertical then its enable by default.
        """

        # The following sequentials don't have any vertical
        self.assertEqual(self.sequential_1_1.get_discussion_toggle_status(), "enabled")
        self.assertEqual(self.sequential_1_2.get_discussion_toggle_status(), "enabled")

        # The following sequentials have verticals
        self.assertEqual(self.sequential_3_1.get_discussion_toggle_status(), "disabled")
        self.assertEqual(self.sequential_4_1.get_discussion_toggle_status(), "disabled")

    def test_verticals_disable_get_chapter_return_disable(self):
        """
        Tests that when all the sequentials of a chapter have discussions disable then chapter of those verticals
        also have discussion disable. If a chapter has no vertical then its enable by default.
        """
        # Chapter 1 have no vertical so its sequentials would report discussion_toggle_status for its children
        # as enabled so discussion toggle status for the Chapter itself would be enabled.
        # and Chapter 2 don't have any sections so its discussion_toggle_status would also be enabled
        self.assertEqual(self.chapter_1.get_discussion_toggle_status(), "enabled")
        self.assertEqual(self.chapter_2.get_discussion_toggle_status(), "enabled")

        self.assertEqual(self.chapter_3.get_discussion_toggle_status(), "disabled")
        self.assertEqual(self.chapter_4.get_discussion_toggle_status(), "disabled")

    def test_not_all_verticals_enable_get_sequence_return_disable(self):
        """
        Tests that when not all the verticals part of a sequence have discussions enable then sequence of those
        verticals have discussion "partially_enabled".
        """

        self.vertical_3_1_1.discussion_enabled = True
        self.vertical_3_1_2.discussion_enabled = True

        self.assertEqual(self.sequential_3_1.get_discussion_toggle_status(), "partially_enabled")

    def test_verticals_enable_get_sequence_and_chapter_return_enable(self):
        """
        Tests that when all the verticals part of a sequence have discussions enable then sequence of those verticals
        have discussion enable and then chapters are also enabled.
        """

        self.vertical_3_1_1.discussion_enabled = True
        self.vertical_3_1_2.discussion_enabled = True
        self.vertical_3_1_3.discussion_enabled = True
        self.vertical_4_1_1.discussion_enabled = True

        self.assertEqual(self.sequential_3_1.get_discussion_toggle_status(), "enabled")
        self.assertEqual(self.sequential_4_1.get_discussion_toggle_status(), "enabled")

        # Chapter 2 have no children (e.g no sequential so no vertical) so it is by default True
        self.assertEqual(self.chapter_2.get_discussion_toggle_status(), "enabled")

        # Chapter 3 and 4 have discussion_enabled flag set to true as all their children
        # have discussion_enabled flag as True
        self.assertEqual(self.chapter_3.get_discussion_toggle_status(), "enabled")
        self.assertEqual(self.chapter_4.get_discussion_toggle_status(), "enabled")

        # Chapter 1 have two sequentials whose discussion_enabled flag is True as they
        # don't have any verticals so this makes Chapter 1 discussion_enabled flag as True
        self.assertEqual(self.chapter_1.get_discussion_toggle_status(), "enabled")

    def test_sequence_enable_get_verticals_enable(self):
        """
        Tests that when a sequence discussion is enable then discussion of all the verticals of that sequence is also
        enable.
        """

        self.sequential_3_1.set_discussion_toggle(True)

        self.assertTrue(self.vertical_3_1_1.discussion_enabled)
        self.assertTrue(self.vertical_3_1_2.discussion_enabled)
        self.assertTrue(self.vertical_3_1_3.discussion_enabled)
        self.assertEqual(self.sequential_3_1.get_discussion_toggle_status(), "enabled")

    def test_chapter_enable_get_verticals_and_sequence_enable(self):
        """
        Tests that when a chapter discussion is enable then discussion of all the verticals and sequence of that
        chapter is also enable.
        """

        self.chapter_3.set_discussion_toggle(True)

        self.assertTrue(self.vertical_3_1_1.discussion_enabled)
        self.assertTrue(self.vertical_3_1_2.discussion_enabled)
        self.assertTrue(self.vertical_3_1_3.discussion_enabled)

    def test_course_level_discussion_disable_cannot_be_overriden(self):
        """
        Tests that when we disable the discussion toggle at course level then the enable_discussion toggle have
        no effect down the hierarchy
        """
        self.course.set_discussion_toggle(False)

        self.chapter_3.set_discussion_toggle(True)
        self.vertical_3_1_1.discussion_enabled = True
        self.vertical_3_1_2.discussion_enabled = True
        self.vertical_3_1_3.discussion_enabled = True

        # The following blocks would be enabled as all the toggle methods just recursively
        # set the children discussion_enabled boolean.
        self.assertEqual(self.chapter_3.get_discussion_toggle_status(), "enabled")
        self.assertTrue(self.vertical_3_1_1.discussion_enabled)
        self.assertTrue(self.vertical_3_1_2.discussion_enabled)
        self.assertTrue(self.vertical_3_1_3.discussion_enabled)

    def test_course_level_discussion_disable_already_enabled_discussion_in_children(self):
        self.chapter_3.set_discussion_toggle(True)

        self.assertEqual(self.chapter_3.get_discussion_toggle_status(), "enabled")
        self.assertTrue(self.vertical_3_1_1.discussion_enabled)
        self.assertTrue(self.vertical_3_1_2.discussion_enabled)
        self.assertTrue(self.vertical_3_1_3.discussion_enabled)

        self.course.set_discussion_toggle(False)

        self.assertEqual(self.chapter_3.get_discussion_toggle_status(), "disabled")
        self.assertFalse(self.vertical_3_1_1.discussion_enabled)
        self.assertFalse(self.vertical_3_1_2.discussion_enabled)
        self.assertFalse(self.vertical_3_1_3.discussion_enabled)
