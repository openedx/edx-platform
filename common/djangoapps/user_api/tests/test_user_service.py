"""
Test the user service
"""
from django.test import TestCase

from student.tests.factories import UserFactory
from user_api import user_service
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class TestUserService(TestCase):
    """
    Test the user service
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = SlashSeparatedCourseKey('test_org', 'test_course_number', 'test_run')
        self.test_key = 'test_key'

    def test_get_set_course_tag(self):
        # get a tag that doesn't exist
        tag = user_service.get_course_tag(self.user, self.course_id, self.test_key)
        self.assertIsNone(tag)

        # test setting a new key
        test_value = 'value'
        user_service.set_course_tag(self.user, self.course_id, self.test_key, test_value)
        tag = user_service.get_course_tag(self.user, self.course_id, self.test_key)
        self.assertEqual(tag, test_value)

        #test overwriting an existing key
        test_value = 'value2'
        user_service.set_course_tag(self.user, self.course_id, self.test_key, test_value)
        tag = user_service.get_course_tag(self.user, self.course_id, self.test_key)
        self.assertEqual(tag, test_value)
