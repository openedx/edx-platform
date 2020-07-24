from django.test import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey

from ..data import ExternalDiscussionData
from ..external_discussions import (
    create_external_discussion_mapping,
    get_external_discussion_context,
    remove_external_discussion_mapping
)
from ...models import ExternalDiscussionsIdMapping


class ExternalDiscussionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+ExternalDiscussion+T1")
        cls.usage_key = cls.course_key.make_usage_key("sequential", "external_discussion")
        cls.external_discussion_id = "custom_external_discussion_id"
        cls.discussion_mapping = ExternalDiscussionsIdMapping.objects.create(
            context_key=cls.course_key,
            usage_key=cls.usage_key,
            external_discussion_id=cls.external_discussion_id
        )
        cls.expected_discussion_data = ExternalDiscussionData(
            context_key=cls.course_key,
            usage_key=cls.usage_key,
            external_discussion_id=cls.external_discussion_id
        )

    def test_create_external_discussion_mapping(self):
        course_key = CourseKey.from_string("course-v1:Test+NewDiscussion+T1")
        usage_key = course_key.make_usage_key("sequential", "new_external_discussion")
        external_discussion_id = "new_external_discussion_id"

        expected_discussion_data = ExternalDiscussionData(
            context_key=course_key,
            usage_key=usage_key,
            external_discussion_id=external_discussion_id
        )

        num_mappings_before = ExternalDiscussionsIdMapping.objects.all().count()

        external_discussion_data = create_external_discussion_mapping(
            course_key,
            usage_key,
            external_discussion_id
        )

        num_mappings_after = ExternalDiscussionsIdMapping.objects.all().count()

        self.assertEqual(expected_discussion_data, external_discussion_data)
        self.assertEqual(num_mappings_before + 1, num_mappings_after)

    def test_create_external_discussion_mapping_duplicate(self):
        with self.assertRaises(ValueError) as context_manager:
            external_discussion_data = create_external_discussion_mapping(
                self.course_key,
                self.usage_key,
                self.external_discussion_id
            )
            assert str(course_key) in context_manager.exception.message
            assert str(usage_key) in context_manager.exception.message

    def test_get_external_discussion_context(self):
        external_discussion_data = get_external_discussion_context(self.course_key, self.usage_key)

        self.assertEqual(self.expected_discussion_data, external_discussion_data)

    def test_get_external_discussion_context_invalid_input(self):
        invalid_course_key = CourseKey.from_string("course-v1:invalid+key+T1")
        invalid_usage_key = invalid_course_key.make_usage_key("sequential", "non_existent")

        external_discussion_data = get_external_discussion_context(
            invalid_course_key,
            invalid_usage_key
        )
        self.assertIsNone(external_discussion_data)

    def test_remove_external_discussion_mapping(self):
        course_key = CourseKey.from_string("course-v1:Test+RemoveDiscussion+T1")
        usage_key = course_key.make_usage_key("sequential", "remove_external_discussion")
        external_discussion_id = "remove_external_discussion_id"

        # Create the object we will be removing manually
        ExternalDiscussionsIdMapping.objects.create(
            context_key=course_key,
            usage_key=usage_key,
            external_discussion_id=external_discussion_id
        )

        # Create the ExternalDiscussionData we will use to delete it from the db
        discussion_data = ExternalDiscussionData(
            context_key=course_key,
            usage_key=usage_key,
            external_discussion_id=external_discussion_id
        )

        num_mappings_before = ExternalDiscussionsIdMapping.objects.all().count()

        result = remove_external_discussion_mapping(discussion_data)

        num_mappings_after = ExternalDiscussionsIdMapping.objects.all().count()

        self.assertTrue(result)
        self.assertEqual(num_mappings_before - 1, num_mappings_after)

    def test_remove_external_discussion_mapping_not_exists_returns_false(self):
        course_key = CourseKey.from_string("course-v1:Test+NotExistsDiscussion+T1")
        usage_key = course_key.make_usage_key("sequential", "not_exists_external_discussion")
        external_discussion_id = "not_exists_external_discussion_id"

        # Create the ExternalDiscussionData we will use to delete it from the db
        discussion_data = ExternalDiscussionData(
            context_key=course_key,
            usage_key=usage_key,
            external_discussion_id=external_discussion_id
        )

        num_mappings_before = ExternalDiscussionsIdMapping.objects.all().count()

        result = remove_external_discussion_mapping(discussion_data)

        num_mappings_after = ExternalDiscussionsIdMapping.objects.all().count()

        self.assertFalse(result)
        self.assertEqual(num_mappings_before, num_mappings_after)
