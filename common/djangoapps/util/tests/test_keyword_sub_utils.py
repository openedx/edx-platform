"""
Tests for keyword_substitution.py
"""

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from ddt import ddt, file_data
from mock import patch


from util.date_utils import get_default_time_display
from util import keyword_substitution as Ks


@ddt
class KeywordSubTest(ModuleStoreTestCase):
    """ Tests for the keyword substitution feature """

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
        """
        Generates a mapping from keywords to functions for testing

        The keyword sub functions should not return %% encoded strings. This
        would lead to ugly and inconsistent behavior due to the way in which
        keyword subbing is handled.
        """

        def user_fullname_sub(user, course):  # pylint: disable=unused-argument
            """ Returns the user's name """
            return user.profile.name

        def course_display_name_sub(user, course):  # pylint: disable=unused-argument
            """ Returns the course name """
            return course.display_name

        return {
            '%%USER_FULLNAME%%': user_fullname_sub,
            '%%COURSE_DISPLAY_NAME%%': course_display_name_sub,
        }

    @file_data('fixtures/test_keyword_coursename_sub.json')
    def test_course_name_sub(self, test_info):
        """ Tests subbing course name in various scenarios """
        course_name = self.course.display_name
        result = Ks.substitute_keywords_with_data(test_info['test_string'], self.user.id, self.course.id)

        self.assertIn(course_name, result)
        self.assertEqual(result, test_info['expected'])

    @file_data('fixtures/test_keyword_anonid_sub.json')
    def test_anonymous_id_subs(self, test_info):
        """ Tests subbing anon user id in various scenarios """
        anon_id = '123456789'
        with patch.dict(Ks.KEYWORD_FUNCTION_MAP, {'%%USER_ID%%': lambda x, y: anon_id}):
            result = Ks.substitute_keywords_with_data(test_info['test_string'], self.user.id, self.course.id)

            self.assertIn(anon_id, result)
            self.assertEqual(result, test_info['expected'])

    def test_name_sub(self):
        test_string = "This is the test string. subthis:  %%USER_FULLNAME%% into user name"
        user_name = self.user.profile.name
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertNotIn('%%USER_FULLNAME%%', result)
        self.assertIn(user_name, result)

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

    @file_data('fixtures/test_keywordsub_multiple_tags.json')
    def test_sub_mutiltple_tags(self, test_info):
        """ Test that subbing works with multiple subtags """
        anon_id = '123456789'
        patched_dict = {
            '%%USER_ID%%': lambda x, y: anon_id,
            '%%USER_FULLNAME%%': lambda x, y: self.user.profile.name,
            '%%COURSE_DISPLAY_NAME': lambda x, y: self.course.display_name,
            '%%COURSE_END_DATE': lambda x, y: get_default_time_display(self.course.end)
        }

        with patch.dict(Ks.KEYWORD_FUNCTION_MAP, patched_dict):
            result = Ks.substitute_keywords_with_data(test_info['test_string'], self.user.id, self.course.id)
            self.assertEqual(result, test_info['expected'])

    def test_no_subbing_empty_subtable(self):
        """
        Test that no sub-ing occurs when the sub table is empty.
        """
        # Set the keyword sub mapping to be empty
        Ks.KEYWORD_FUNCTION_MAP = {}

        test_string = 'This user\'s name is %%USER_FULLNAME%%'
        result = Ks.substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertNotIn(self.user.profile.name, result)
        self.assertIn('%%USER_FULLNAME%%', result)

    def test_subbing_no_userid_or_courseid(self):
        """
        Tests that no subbing occurs if no user_id or no course_id is given.
        """
        test_string = 'This string should not be subbed here %%USER_ID%%'

        result = Ks.substitute_keywords_with_data(test_string, None, self.course.id)
        self.assertEqual(test_string, result)

        result = Ks.substitute_keywords_with_data(test_string, self.user.id, None)
        self.assertEqual(test_string, result)

    def test_subbing_no_user_or_course(self):
        """
        Tests that no subbing occurs if no user or no course is given
        """
        test_string = "This string should not be subbed here %%USER_ID%%"

        result = Ks.substitute_keywords(test_string, course=self.course, user=None)
        self.assertEqual(test_string, result)

        result = Ks.substitute_keywords(test_string, self.user, None)
        self.assertEqual(test_string, result)
