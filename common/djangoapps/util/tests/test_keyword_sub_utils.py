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
        super(KeywordSubTest, self).setUp(create_user=False)
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

        self.context = {
            'user_id': self.user.id,
            'course_title': self.course.display_name,
            'name': self.user.profile.name,
            'course_end_date': get_default_time_display(self.course.end),
        }

    @file_data('fixtures/test_keyword_coursename_sub.json')
    def test_course_name_sub(self, test_info):
        """ Tests subbing course name in various scenarios """
        course_name = self.course.display_name
        result = Ks.substitute_keywords_with_data(
            test_info['test_string'], self.context,
        )

        self.assertIn(course_name, result)
        self.assertEqual(result, test_info['expected'])

    def test_anonymous_id_sub(self):
        """
        Test that anonymous_id is subbed
        """
        test_string = "Turn %%USER_ID%% into anonymous id"
        anonymous_id = Ks.anonymous_id_from_user_id(self.user.id)
        result = Ks.substitute_keywords_with_data(
            test_string, self.context,
        )
        self.assertNotIn('%%USER_ID%%', result)
        self.assertIn(anonymous_id, result)

    def test_name_sub(self):
        """
        Test that the user's full name is correctly subbed
        """
        test_string = "This is the test string. subthis: %%USER_FULLNAME%% into user name"
        user_name = self.user.profile.name
        result = Ks.substitute_keywords_with_data(
            test_string, self.context,
        )

        self.assertNotIn('%%USER_FULLNAME%%', result)
        self.assertIn(user_name, result)

    def test_illegal_subtag(self):
        """
        Test that sub-ing doesn't ocurr with illegal tags
        """
        test_string = "%%user_id%%"
        result = Ks.substitute_keywords_with_data(
            test_string, self.context,
        )

        self.assertEquals(test_string, result)

    def test_should_not_sub(self):
        """
        Test that sub-ing doesn't work without subtags
        """
        test_string = "this string has no subtags"
        result = Ks.substitute_keywords_with_data(
            test_string, self.context,
        )

        self.assertEquals(test_string, result)

    @file_data('fixtures/test_keywordsub_multiple_tags.json')
    def test_sub_multiple_tags(self, test_info):
        """ Test that subbing works with multiple subtags """
        anon_id = '123456789'

        with patch('util.keyword_substitution.anonymous_id_from_user_id', lambda user_id: anon_id):
            result = Ks.substitute_keywords_with_data(
                test_info['test_string'], self.context,
            )
            self.assertEqual(result, test_info['expected'])

    def test_subbing_no_userid_or_courseid(self):
        """
        Tests that no subbing occurs if no user_id or no course_id is given.
        """
        test_string = 'This string should not be subbed here %%USER_ID%%'

        no_course_context = dict(
            (key, value) for key, value in self.context.iteritems() if key != 'course_title'
        )
        result = Ks.substitute_keywords_with_data(test_string, no_course_context)
        self.assertEqual(test_string, result)

        no_user_id_context = dict(
            (key, value) for key, value in self.context.iteritems() if key != 'user_id'
        )
        result = Ks.substitute_keywords_with_data(test_string, no_user_id_context)
        self.assertEqual(test_string, result)
