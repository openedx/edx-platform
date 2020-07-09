import json

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_url
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestDiscussionEnabledAPI(CourseTestCase):
    def setUp(self):
        super(TestDiscussionEnabledAPI, self).setUp()
        self.course = self.get_dummy_course()
        self.course.save()

    def get_dummy_course(self):
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

    def get_discussion_enabled_status(self, xblock, client=None):
        client = client if client is not None else self.client
        url = reverse_url("toggle_discussion_enabled", 'key_string', xblock.location)
        resp = client.get(url, HTTP_ACCEPT="application/json")
        content = json.loads(resp.content.decode("utf-8"))
        discussion_enabled = content["discussion_enabled"]
        return discussion_enabled

    def set_discussion_enabled_status(self, xblock, value, client=None):
        client = client if client is not None else self.client
        xblock_location = xblock.id if xblock.category == "course" else xblock.location

        url = reverse_url("toggle_discussion_enabled", 'key_string', xblock_location)
        resp = client.post(
            url,
            HTTP_ACCEPT="application/json",
            data=json.dumps({"value": value}),
            content_type="application/json",
        )
        return resp

    def test_verticals_disable_initially(self):
        """
        Tests that when a vertical is created then by default discussion is disabled.
        """

        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_4_1_1))

    def test_verticals_disable_get_sequence_return_disable(self):
        """
        Tests that when all the verticals of a sequential have discussions disabled then sequential of those verticals
        also have discussion disable. If a sequential has no vertical then its enable by default.
        """

        # The following sequentials don't have any vertical
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_1_1), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_1_2), "enabled")

        # The following sequentials have verticals
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_4_1), "disabled")

    def test_verticals_disable_get_chapter_return_disable(self):
        """
        Tests that when all the sequentials of a chapter have discussions disable then chapter of those verticals
        also have discussion disable. If a chapter has no vertical then its enable by default.
        """
        # Chapter 1 have no vertical so its sequentials would report discussion_toggle_status for its children
        # as enabled so discussion toggle status for the Chapter itself would be enabled.
        # and Chapter 2 don't have any sections so its discussion_toggle_status would also be enabled
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_1), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_2), "enabled")

        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "disabled")
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_4), "disabled")

    def test_not_all_verticals_enable_get_sequence_return_disable(self):
        """
        Tests that when not all the verticals part of a sequence have discussions enable then sequence of those
        verticals have discussion "partially_enabled".
        """
        self.set_discussion_enabled_status(self.vertical_3_1_1, True)
        self.set_discussion_enabled_status(self.vertical_3_1_2, True)

        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "partially_enabled")

    def test_verticals_enable_get_sequence_and_chapter_return_enable(self):
        """
        Tests that when all the verticals part of a sequence have discussions enable then sequence of those verticals
        have discussion enable and then chapters are also enabled.
        """
        self.set_discussion_enabled_status(self.vertical_3_1_1, True)
        self.set_discussion_enabled_status(self.vertical_3_1_2, True)
        self.set_discussion_enabled_status(self.vertical_3_1_3, True)
        self.set_discussion_enabled_status(self.vertical_4_1_1, True)

        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.sequential_4_1), "enabled")

        # Chapter 2 have no children (e.g no sequential so no vertical) so it is by default True
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_2), "enabled")

        # Chapter 3 and 4 have discussion_enabled flag set to true as all their children
        # have discussion_enabled flag as True
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "enabled")
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_4), "enabled")

        # Chapter 1 have two sequentials whose discussion_enabled flag is True as they
        # don't have any verticals so this makes Chapter 1 discussion_enabled flag as True
        self.assertEqual(self.get_discussion_enabled_status(self.chapter_1), "enabled")

    def test_sequence_enable_get_verticals_enable(self):
        """
        Tests that when a sequence discussion is enable then discussion of all the verticals of that sequence is also
        enable.
        """
        self.set_discussion_enabled_status(self.sequential_3_1, True)

        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.assertEqual(self.get_discussion_enabled_status(self.sequential_3_1), "enabled")

    def test_chapter_enable_get_verticals_and_sequence_enable(self):
        """
        Tests that when a chapter discussion is enable then discussion of all the verticals and sequence of that
        chapter is also enable.
        """
        self.set_discussion_enabled_status(self.chapter_3, True)

        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.set_discussion_enabled_status(self.course, False)

        self.assertEqual(self.get_discussion_enabled_status(self.chapter_3), "disabled")
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))

    def test_non_course_author_cannot_get_or_set_discussion_flag(self):
        client, _ = self.create_non_staff_authed_user_client()
        with self.assertRaises(json.JSONDecodeError):
            self.get_discussion_enabled_status(self.course, client=client)

        resp = self.set_discussion_enabled_status(self.course, False, client=client)
        self.assertEqual(resp.status_code, 403)
