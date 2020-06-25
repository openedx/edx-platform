"""
Test API functionality responsible for setting/getting discussion_enabled flag for course and is_discussable flag
for other xblocks
"""
import json

from opaque_keys.edx.keys import CourseKey

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_usage_url
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestDiscussionEnabledAPI(CourseTestCase):
    """
    Test API functionality responsible for setting/getting discussion_enabled flag for course and is_discussable flag
    for other xblocks
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
            discussion_enabled = content.get("is_discussable", None)
        elif usage_key.category == "course":
            discussion_enabled = content.get("discussion_enabled", None)
        else:
            discussion_enabled = None

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
        if xblock.category == "course":
            field_name = "discussion_enabled"
            xblock_location = xblock.id
        else:
            field_name = "is_discussable"
            xblock_location = xblock.location

        url = reverse_usage_url("xblock_handler", xblock_location)
        resp = client.post(
            url,
            HTTP_ACCEPT="application/json",
            data=json.dumps({"metadata": {field_name: value}}),
            content_type="application/json",
        )
        return resp

    def test_is_discussable_false_initially(self):
        """
        Tests is_discussable flag is False initially for vertical
        """
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_4_1_1))

    def test_updating_sequential_enabled_discussion_cascade_to_verticals(self):
        """
        Tests that when a sequential's discussion_enabled flag is updated then discussion_enabled flag of all its
        children verticals is also updated to the new value.
        """
        self.set_discussion_enabled_status(self.sequential_3_1, True)
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.set_discussion_enabled_status(self.sequential_3_1, False)
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertFalse(self.get_discussion_enabled_status(self.vertical_3_1_3))

    def test_updating_chapter_enabled_discussion_cascade_to_verticals(self):
        """
        Tests that when a chapter's discussion_enabled flag is updated then discussion_enabled flag of all its
        children verticals is also updated to the new value.
        """
        self.set_discussion_enabled_status(self.chapter_3, True)
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_1))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_2))
        self.assertTrue(self.get_discussion_enabled_status(self.vertical_3_1_3))

        self.set_discussion_enabled_status(self.chapter_3, False)
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
