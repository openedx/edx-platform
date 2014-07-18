"""
Tests for keyword_substitution.py
"""

from django.test import TestCase
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory

from student.models import anonymous_id_for_user
from util.date_utils import get_default_time_display
from util import keyword_substitution as Ks

class KeywordSubTest(TestCase):

    def setUp(self):
        self.user = UserFactory.create(
            email="testuser@edx.org",
            username="testuser",
            profile__name="Test User"
        )
        self.course = CourseFactory.create(
            org='edx',
            course='999',
            display_name='test_course'
        )

        # Mimic monkeypatching done in startup.py
        Ks.KEYWORD_FUNCTION_MAP = self.get_keyword_function_map()

    def get_keyword_function_map(self):
        def user_id_sub(user, course):
            # Don't include course_id for compatibility 
            return anonymous_id_for_user(user, None)

        def user_fullname_sub(user, course=None):
            return user.profile.name

        def course_display_name_sub(user, course):
            return course.display_name

        def course_end_date_sub(user, course):
            return get_default_time_display(course.end)

        return {
            '%%USER_ID%%': user_id_sub,
            '%%USER_FULLNAME%%': user_fullname_sub,
            '%%COURSE_DISPLAY_NAME%%': course_display_name_sub,
            '%%COURSE_END_DATE%%': course_end_date_sub
        }

    def test_course_name_sub(self):
        test_string = 'Course Display Name: %%COURSE_DISPLAY_NAME%%'
        course_name = self.course.display_name
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertIn(course_name, result)
        self.assertNotIn('%%COURSE_DISPLAY_NAME%%', result)

    def test_anonymous_id_sub(self):
        test_string = "This is the test string. sub this: %%USER_ID%% into anon_id"
        anon_id = anonymous_id_for_user(self.user, None)
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertIn("this: " + anon_id + " into", result)
        self.assertNotIn("%%USER_ID%%", result)

    def test_name_sub(self):
        test_string = "This is the test string. subthis:  %%USER_FULLNAME%% into user name"
        user_name = self.user.profile.name
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertNotIn('%%USER_FULLNAME', result)
        self.assertIn(user_name, result)

    def test_anonymous_id_sub_html(self):
        """
        Test that sub-ing works in html tags as well
        """
        test_string = "<some tag>%%USER_ID%%</some tag>"
        anon_id = anonymous_id_for_user(self.user, None)
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(result, "<some tag>" + anon_id + "</some tag>")

    def test_illegal_subtag(self):
        """
        Test that sub-ing doesn't ocurr with illegal tags
        """
        test_string = "%%user_id%%"
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(test_string, result)

    def test_should_not_sub(self):
        """
        Test that sub-ing doesn't work without subtags
        """
        test_string = "this string has no subtags"
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(test_string, result)
