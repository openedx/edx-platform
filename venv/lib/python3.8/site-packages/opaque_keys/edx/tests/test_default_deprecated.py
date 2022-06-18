"""
Test that old keys deserialize just by importing opaque keys
"""
from unittest import TestCase
from opaque_keys.edx.keys import CourseKey, LearningContextKey, UsageKey


class TestDefault(TestCase):
    """
    Check that clients which merely import CourseKey can deserialize the expected keys, etc
    """
    def test_course_key(self):
        """
        Test CourseKey
        """
        key = CourseKey.from_string('org.id/course_id/run')
        self.assertEqual(key.org, 'org.id')

        key = CourseKey.from_string('course-v1:org.id+course_id+run')
        self.assertEqual(key.org, 'org.id')

    def test_learning_context_key(self):
        """
        Test CourseKey
        """
        key = LearningContextKey.from_string('org.id/course_id/run')
        self.assertEqual(key.org, 'org.id')
        self.assertIsInstance(key, CourseKey)

        key = LearningContextKey.from_string('course-v1:org.id+course_id+run')
        self.assertEqual(key.org, 'org.id')
        self.assertIsInstance(key, CourseKey)

    def test_usage_key(self):
        """
        Test UsageKey
        """
        key = UsageKey.from_string('i4x://org.id/course_id/category/block_id')
        self.assertEqual(key.block_id, 'block_id')

        key = UsageKey.from_string('block-v1:org.id+course_id+run+type@category+block@block_id')
        self.assertEqual(key.block_id, 'block_id')
