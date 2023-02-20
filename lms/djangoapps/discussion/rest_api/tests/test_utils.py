"""
Tests for Discussion REST API utils.
"""

from datetime import datetime, timedelta

from pytz import UTC
import unittest
from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from lms.djangoapps.discussion.rest_api.utils import (
    discussion_open_for_user,
    get_course_ta_users_list,
    get_course_staff_users_list,
    get_moderator_users_list,
    get_archived_topics, remove_empty_sequentials
)


class DiscussionAPIUtilsTestCase(ModuleStoreTestCase):
    """
    Base test-case class for utils for Discussion REST API.
    """
    CREATE_USER = False

    def setUp(self):
        super().setUp()     # lint-amnesty, pylint: disable=super-with-arguments

        self.course = CourseFactory.create()
        self.course.discussion_blackouts = [datetime.now(UTC) - timedelta(days=3),
                                            datetime.now(UTC) + timedelta(days=3)]
        self.student_role = RoleFactory(name='Student', course_id=self.course.id)
        self.moderator_role = RoleFactory(name='Moderator', course_id=self.course.id)
        self.community_ta_role = RoleFactory(name='Community TA', course_id=self.course.id)
        self.group_community_ta_role = RoleFactory(name='Group Moderator', course_id=self.course.id)

        self.student = UserFactory(username='student', email='student@edx.org')
        self.student_enrollment = CourseEnrollmentFactory(user=self.student)
        self.student_role.users.add(self.student)

        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)
        self.moderator_role.users.add(self.moderator)

        self.community_ta = UserFactory(username='community_ta1', email='community_ta1@edx.org')
        self.community_ta_role.users.add(self.community_ta)

        self.group_community_ta = UserFactory(username='group_community_ta1', email='group_community_ta1@edx.org')
        self.group_community_ta_role.users.add(self.group_community_ta)

        self.course_staff_user = UserFactory(username='course_staff_user1', email='course_staff_user1@edx.org')
        self.course_instructor_user = UserFactory(username='course_instructor_user1',
                                                  email='course_instructor_user1@edx.org')
        CourseStaffRole(course_key=self.course.id).add_users(self.course_staff_user)
        CourseInstructorRole(course_key=self.course.id).add_users(self.course_instructor_user)

    def test_discussion_open_for_user(self):
        self.assertFalse(discussion_open_for_user(self.course, self.student))
        self.assertTrue(discussion_open_for_user(self.course, self.moderator))
        self.assertTrue(discussion_open_for_user(self.course, self.community_ta))

    def test_course_staff_users_list(self):
        assert len(get_course_staff_users_list(self.course.id)) == 2

    def test_course_moderator_users_list(self):
        assert len(get_moderator_users_list(self.course.id)) == 1

    def test_course_ta_users_list(self):
        ta_user_list = get_course_ta_users_list(self.course.id)
        assert len(ta_user_list) == 2

    def test_get_archived_topics(self):
        # Define some example inputs
        filtered_topic_ids = ['t1', 't2', 't3', 't4']
        topics = [
            {'id': 't1', 'usage_key': 'u1', 'title': 'Topic 1'},
            {'id': 't2', 'usage_key': None, 'title': 'Topic 2'},
            {'id': 't3', 'usage_key': 'u3', 'title': 'Topic 3'},
            {'id': 't4', 'usage_key': 'u4', 'title': 'Topic 4'},
            {'id': 't5', 'usage_key': None, 'title': 'Topic 5'},
        ]
        expected_output = [
            {'id': 't1', 'usage_key': 'u1', 'title': 'Topic 1'},
            {'id': 't3', 'usage_key': 'u3', 'title': 'Topic 3'},
            {'id': 't4', 'usage_key': 'u4', 'title': 'Topic 4'},
        ]

        # Call the function with the example inputs
        output = get_archived_topics(filtered_topic_ids, topics)

        # Assert that the output matches the expected output
        assert output == expected_output


class TestRemoveEmptySequentials(unittest.TestCase):
    """
    Test for the remove_empty_sequentials function
    """
    def test_empty_data(self):
        # Test that the function can handle an empty list
        data = []
        result = remove_empty_sequentials(data)
        self.assertEqual(result, [])

    def test_no_empty_sequentials(self):
        # Test that the function does not remove any sequentials if they all have children
        data = [
            {"type": "sequential", "children": [{"type": "vertical"}]},
            {"type": "chapter", "children": [
                {"type": "sequential", "children": [{"type": "vertical"}]}
            ]}
        ]
        result = remove_empty_sequentials(data)
        self.assertEqual(result, data)

    def test_remove_empty_sequentials(self):
        # Test that the function removes empty sequentials
        data = [
            {"type": "sequential", "children": []},
            {"type": "chapter", "children": [
                {"type": "sequential", "children": [{"type": "vertical3"}]},
                {"type": "sequential", "children": []},
                {"type": "sequential", "children": []},
                {"type": "sequential", "children": [{"type": "vertical4"}]}
            ]},
            {"type": "chapter", "children": [
                {"type": "sequential", "children": [{"type": "vertical1"}]},
                {"type": "sequential", "children": []},
                {"children": [{"type": "vertical2"}]}
            ]},
            {"type": "chapter", "children": [
                {"type": "sequential", "children": []},
                {"type": "sequential", "children": []},
            ]
            }
        ]
        expected_output = [
            {"type": "chapter", "children": [
                {"type": "sequential", "children": [{"type": "vertical3"}]},
                {"type": "sequential", "children": [{"type": "vertical4"}]}
            ]},
            {"type": "chapter", "children": [
                {"type": "sequential", "children": [{"type": "vertical1"}]},
                {"children": [{"type": "vertical2"}]}
            ]}
        ]
        result = remove_empty_sequentials(data)
        self.assertEqual(result, expected_output)
