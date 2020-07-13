"""
Test API functionality responsible for set/get of discussion_enabled flag for course and other xblocks
"""
import json

from opaque_keys.edx.keys import CourseKey

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_usage_url
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestDiscussionEnabledAPI(CourseTestCase):
    """
    Test API functionality responsible for set/get of discussion_enabled flag for course and other xblocks
    """
    def setUp(self):
        super(TestDiscussionEnabledAPI, self).setUp()
        self.course = self.get_dummy_course()
        self.course.save()
        self.course_usage_key = CourseKey.from_string(str(self.course.id)).make_usage_key("course", self.course.id.run)

        self.non_staff_authed_user_client, _ = self.create_non_staff_authed_user_client()

    def get_dummy_course(self):
        """
        Create and return a dummy course
        """
        ORG, NUMBER, NAME, RUN = "ABKUni", "CS101", "Introduction to CS", "2020_T2"
        self.course = CourseFactory(
            org=ORG,
            number=NUMBER,
            name=NAME,
            run=RUN,
            modulestore=self.store
        )
        self.chapter_1 = ItemFactory(
            parent_location=self.course.location,
            category="chapter",
            display_name="Chapter 1",
            modulestore=self.store
        )
        self.chapter_2 = ItemFactory(
            parent_location=self.course.location,
            category="chapter",
            display_name="Chapter 2",
            modulestore=self.store
        )
        self.chapter_3 = ItemFactory(
            parent_location=self.course.location,
            category="chapter",
            display_name="Chapter 3",
            modulestore=self.store
        )
        self.chapter_4 = ItemFactory(
            parent_location=self.course.location,
            category="chapter",
            display_name="Chapter 4",
            modulestore=self.store
        )

        self.sequential_1_1 = ItemFactory(
            parent_location=self.chapter_1.location,
            category="sequential",
            display_name="Sequential 1.1",
            modulestore=self.store
        )
        self.sequential_1_2 = ItemFactory(
            parent_location=self.chapter_1.location,
            category="sequential",
            display_name="Sequential 1.2",
            modulestore=self.store
        )
        self.sequential_3_1 = ItemFactory(
            parent_location=self.chapter_3.location,
            category="sequential",
            display_name="Sequential 3.1",
            modulestore=self.store
        )
        self.sequential_4_1 = ItemFactory(
            parent_location=self.chapter_4.location,
            category="sequential",
            display_name="Sequential 4.1",
            modulestore=self.store
        )

        self.vertical_3_1_1 = ItemFactory(
            parent_location=self.sequential_3_1.location,
            category="vertical",
            display_name="Vertical 3.1.1",
            modulestore=self.store
        )
        self.vertical_3_1_2 = ItemFactory(
            parent_location=self.sequential_3_1.location,
            category="vertical",
            display_name="Vertical 3.1.2",
            modulestore=self.store
        )
        self.vertical_3_1_3 = ItemFactory(
            parent_location=self.sequential_3_1.location,
            category="vertical",
            display_name="Vertical 3.1.3",
            modulestore=self.store
        )
        self.vertical_4_1_1 = ItemFactory(
            parent_location=self.sequential_4_1.location,
            category="vertical",
            display_name="Vertical 4.1.1",
            modulestore=self.store
        )
        return self.course

    def _get_discussion_enabled_status(self, usage_key, client=None):
        """
        Issue a GET request to fetch value of discussion_enabled flag of xblock represented by param:usage_key
        """
        client = client if client is not None else self.client
        url = reverse_usage_url("xblock_handler", usage_key)
        resp = client.get(url, HTTP_ACCEPT="application/json")
        content = json.loads(resp.content.decode("utf-8"))

        if usage_key.category == "vertical":
            discussion_enabled = content.get("metadata", {}).get("discussion_enabled", None)
        else:
            discussion_enabled = content.get("discussion_enabled", None)
        return discussion_enabled

    def get_discussion_enabled_status(self, xblock, client=None):
        """
        Issue a GET request to fetch value of discussion_enabled flag of param:xblock's
        """
        return self._get_discussion_enabled_status(xblock.location, client=client)

    def set_discussion_enabled_status(self, xblock, value, client=None):
        """
        Issue a POST request to update value of discussion_enabled flag of param:xblock's
        """
        client = client if client is not None else self.client
        xblock_location = xblock.id if xblock.category == "course" else xblock.location

        url = reverse_usage_url("xblock_handler", xblock_location)
        resp = client.post(
            url,
            HTTP_ACCEPT="application/json",
            data=json.dumps({"fields": {"discussion_enabled": value}}),
            content_type="application/json",
        )
        return resp

    def test_discussion_enabled_is_false_initially(self):
        """
        Tests discussion_enabled flag is False initially for vertical
        """
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_4_1_1))

    def test_discussion_enabled_status_is_disabled_initially(self):
        """
        Tests discussion_enabled status is disabled initially for chapter/sequentials
        """
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "disabled")

        self.assertEqual(self.get_discussion_enabled_status(self.chapter_4), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_4_1), "disabled")

    def test_discussion_enabled_status_is_disabled_for_empty_sequentials(self):
        """
        If a sequential does not have any vertical or then its discussion_enabled status is disabled by default.
        If a chapter's sequentials are empty than its's discussion_enabled status is disabled.
        """

        # Chapter 1 have no vertical so its sequentials would report discussion_toggle_status for its children
        # as disabled so discussion toggle status for the Chapter itself would be disabled.
        # and Chapter 2 don't have any sections so its discussion_toggle_status would also be disabled
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_1), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_2), "disabled")

        # The following sequentials do not have any vertical
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_1_1), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_1_2), "disabled")

    def test_setting_few_vertical_discussion_status_true_make_sequential_partially_enabled(self):
        """
        Tests that when not all the verticals of a sequential have discussions_enabled as True then thier sequential
        discussion_enabled status "partially_enabled".
        """
        self.set_discussion_enabled_status(self.vertical_3_1_1, True)
        self.set_discussion_enabled_status(self.vertical_3_1_2, True)

        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "partially_enabled")

    def test_setting_all_vertical_discussion_status_true_make_sequential_enabled(self):
        """
        Tests that when all the verticals part of a sequence have discussions enable then sequential/chapter of those
        verticals have discussion_enabled as enabled.
        """
        self.set_discussion_enabled_status(self.vertical_3_1_1, True)
        self.set_discussion_enabled_status(self.vertical_3_1_2, True)
        self.set_discussion_enabled_status(self.vertical_3_1_3, True)
        self.set_discussion_enabled_status(self.vertical_4_1_1, True)

        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_4_1), "enabled")

        # Chapter 3 and 4 have discussion_enabled flag set to true as all their children
        # have discussion_enabled flag as True
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_4), "enabled")

    def test_updating_sequential_enabled_discussion_cascade_to_verticals(self):
        """
        Tests that when a sequential's discussion_enabled flag is updated then discussion_enabled flag of all its
        children verticals is also updated to the new value.
        """
        self.set_discussion_enabled_status(self.sequential_3_1, True)
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "enabled")
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.set_discussion_enabled_status(self.sequential_3_1, False)
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "disabled")
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))

    def test_updating_chapter_enabled_discussion_cascade_to_verticals(self):
        """
        Tests that when a chapter's discussion_enabled flag is updated then discussion_enabled flag of all its
        children sequential/verticals is also updated to the new value.
        """
        self.set_discussion_enabled_status(self.chapter_3, True)
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "enabled")
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.set_discussion_enabled_status(self.chapter_3, False)
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "disabled")
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))

    def test_non_course_author_cannot_get_or_set_discussion_flag(self):
        """
        Test non course author cannot get/set discussion flag
        """
        with self.assertRaises(json.JSONDecodeError):
            self.assertEqual(
                self._get_discussion_enabled_status(self.course_usage_key, self.non_staff_authed_user_client),
                "disabled"
            )

    def test_setting_all_block_discussion_enabled_flag_cascade_upto_course(self):
        """
        Test that setting all blocks discussion_enabled flag cascade up to the root block i.e course
        """
        self.assertEqual(self._get_discussion_enabled_status(self.course_usage_key), "disabled")

        self.set_discussion_enabled_status(self.sequential_4_1, True)
        self.set_discussion_enabled_status(self.sequential_3_1, True)

        self.assertEqual(self._get_discussion_enabled_status(self.course_usage_key), "enabled")

        self.set_discussion_enabled_status(self.chapter_1, False)
        self.set_discussion_enabled_status(self.chapter_2, False)
        self.set_discussion_enabled_status(self.chapter_3, False)
        self.set_discussion_enabled_status(self.chapter_4, False)

        self.assertEqual(self._get_discussion_enabled_status(self.course_usage_key), "disabled")
