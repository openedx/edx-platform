"""
Tests for Discussion REST API utils.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

from httpretty import httpretty
from pytz import UTC
import unittest
from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
from lms.djangoapps.discussion.django_comment_client.tests.utils import ForumsEnableMixin
from lms.djangoapps.discussion.rest_api.tests.utils import CommentsServiceMockMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from lms.djangoapps.discussion.rest_api.utils import (
    discussion_open_for_user,
    get_course_ta_users_list,
    get_course_staff_users_list,
    get_moderator_users_list,
    get_archived_topics, remove_empty_sequentials, send_response_notifications
)
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED


class DiscussionAPIUtilsTestCase(ModuleStoreTestCase):
    """
    Base test-case class for utils for Discussion REST API.
    """
    CREATE_USER = False

    def setUp(self):
        super().setUp()  # lint-amnesty, pylint: disable=super-with-arguments

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


class TestSendResponseNotifications(ForumsEnableMixin, CommentsServiceMockMixin, ModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        httpretty.reset()
        httpretty.enable()

        self.user_1 = UserFactory.create()
        self.user_2 = UserFactory.create()
        self.user_3 = UserFactory.create()
        self.thread = ThreadMock(thread_id=1, creator=self.user_1, title='test thread')
        self.thread_2 = ThreadMock(thread_id=2, creator=self.user_2, title='test thread 2')
        self.course = CourseFactory.create()

    def test_send_notification_to_thread_creator(self):
        """
        Test that the notification is sent to the thread creator
        """
        handler = Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        # Post the form or do what it takes to send the signal

        send_response_notifications(self.thread, self.course, self.user_2, parent_id=None)
        self.assertEqual(handler.call_count, 1)
        args = handler.call_args[1]['notification_data']
        self.assertEqual(args.user_ids, [self.user_1.id])
        self.assertEqual(args.notification_type, 'new_response')
        expected_context = {
            'course_id': str(self.course.id),
            'replier_name': self.user_2.username,
            'post_title': 'test thread'
        }
        self.assertDictEqual(args.context, expected_context)
        self.assertEqual(args.content_url, 'http://example.com/1')
        self.assertEqual(args.app_name, 'discussion')

    def test_send_notification_to_parent_threads(self):
        """
        Test that the notification signal is sent to the parent response creator and
        parent thread creator, it checks signal is sent with correct arguments for both
        types of notifications.
        """
        handler = Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        self.register_get_comment_response({
            'id': self.thread_2.id,
            'thread_id': self.thread.id,
            'user_id': self.thread_2.user_id
        })

        send_response_notifications(self.thread, self.course, self.user_3, parent_id=self.thread_2.id)
        # check if 2 call are made to the handler i.e. one for the response creator and one for the thread creator
        self.assertEqual(handler.call_count, 2)

        # check if the notification is sent to the thread creator
        args_comment = handler.call_args_list[0][1]['notification_data']
        args_comment_on_response = handler.call_args_list[1][1]['notification_data']
        self.assertEqual(args_comment.user_ids, [self.user_1.id])
        self.assertEqual(args_comment.notification_type, 'new_comment')
        expected_context = {
            'course_id': str(self.course.id),
            'replier_name': self.user_3.username,
            'post_title': self.thread.title,
            'author_name': 'dummy'
        }
        self.assertDictEqual(args_comment.context, expected_context)
        self.assertEqual(args_comment.content_url, 'http://example.com/1')
        self.assertEqual(args_comment.app_name, 'discussion')

        # check if the notification is sent to the parent response creator
        self.assertEqual(args_comment_on_response.user_ids, [self.user_2.id])
        self.assertEqual(args_comment_on_response.notification_type, 'new_comment_on_response')
        expected_context = {
            'course_id': str(self.course.id),
            'replier_name': self.user_3.username,
            'post_title': self.thread.title,
        }
        self.assertDictEqual(args_comment_on_response.context, expected_context)
        self.assertEqual(args_comment_on_response.content_url, 'http://example.com/1')
        self.assertEqual(args_comment_on_response.app_name, 'discussion')

    def test_no_signal_on_creators_own_thread(self):
        """
        Makes sure that no signal is emitted if user creates response on
        their own thread.
        """
        handler = Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)
        send_response_notifications(self.thread, self.course, self.user_1, parent_id=None)
        self.assertEqual(handler.call_count, 0)

