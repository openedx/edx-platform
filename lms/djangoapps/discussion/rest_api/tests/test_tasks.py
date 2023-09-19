"""
Test cases for tasks.py
"""
from unittest import mock
from edx_toggles.toggles.testutils import override_waffle_flag
import ddt
import httpretty
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import StaffFactory, UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from lms.djangoapps.discussion.rest_api.tasks import send_thread_created_notification
from lms.djangoapps.discussion.rest_api.tests.utils import make_minimal_cs_thread
from openedx.core.djangoapps.course_groups.models import CohortMembership, CourseCohortsSettings
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.django_comment_common.models import (
    CourseDiscussionSettings,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_STUDENT,
)
from openedx.core.djangoapps.discussions.models import DiscussionTopicLink
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from .test_views import DiscussionAPIViewTestMixin


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
@override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
class TestNewThreadCreatedNotification(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """
    Test cases related to new_discussion_post and new_question_post notification types
    """
    def setUp(self):
        """
        Setup test case
        """
        super().setUp()

        # Creating a course
        self.course = CourseFactory.create()

        # Creating relative discussion and cohort settings
        CourseCohortsSettings.objects.create(course_id=str(self.course.id))
        CourseDiscussionSettings.objects.create(course_id=str(self.course.id), _divided_discussions='[]')
        self.first_cohort = self.second_cohort = None

        # Duplicating roles
        self.student_role = RoleFactory(name=FORUM_ROLE_STUDENT, course_id=self.course.id)
        self.moderator_role = RoleFactory(name=FORUM_ROLE_MODERATOR, course_id=self.course.id)
        self.ta_role = RoleFactory(name=FORUM_ROLE_COMMUNITY_TA, course_id=self.course.id)
        self.group_community_ta_role = RoleFactory(name=FORUM_ROLE_GROUP_MODERATOR, course_id=self.course.id)

        # Creating users for with roles
        self.author = StaffFactory(course_key=self.course.id, username='Author')
        self.staff = StaffFactory(course_key=self.course.id, username='Staff')

        self.moderator = UserFactory(username='Moderator')
        self.moderator_role.users.add(self.moderator)

        self.ta = UserFactory(username='TA')
        self.ta_role.users.add(self.ta)

        self.group_ta_cohort_1 = UserFactory(username='Group TA 1')
        self.group_ta_cohort_2 = UserFactory(username='Group TA 2')
        self.group_community_ta_role.users.add(self.group_ta_cohort_1)
        self.group_community_ta_role.users.add(self.group_ta_cohort_2)

        self.learner_cohort_1 = UserFactory(username='Learner 1')
        self.learner_cohort_2 = UserFactory(username='Learner 2')
        self.student_role.users.add(self.learner_cohort_1)
        self.student_role.users.add(self.learner_cohort_2)

        # Creating a topic
        self.topic_id = 'test_topic'
        usage_key = self.course.id.make_usage_key('vertical', self.topic_id)
        self.topic = DiscussionTopicLink(
            context_key=self.course.id,
            usage_key=usage_key,
            title=f"Discussion on {self.topic_id}",
            external_id=self.topic_id,
            provider_id="openedx",
            ordering=1,
            enabled_in_context=True,
        )
        self.notification_to_all_users = [
            self.learner_cohort_1, self.learner_cohort_2, self.staff,
            self.moderator, self.ta, self.group_ta_cohort_1, self.group_ta_cohort_2
        ]
        self.privileged_users = [
            self.staff, self.moderator, self.ta
        ]
        self.cohort_1_users = [self.learner_cohort_1, self.group_ta_cohort_1] + self.privileged_users
        self.cohort_2_users = [self.learner_cohort_2, self.group_ta_cohort_2] + self.privileged_users
        self.thread = self._create_thread()

    def _configure_cohorts(self):
        """
        Configure cohort for course and assign membership to users
        """
        course_key_str = str(self.course.id)
        cohort_settings = CourseCohortsSettings.objects.get(course_id=course_key_str)
        cohort_settings.is_cohorted = True
        cohort_settings.save()

        discussion_settings = CourseDiscussionSettings.objects.get(course_id=course_key_str)
        discussion_settings.always_divide_inline_discussions = True
        discussion_settings.save()

        self.first_cohort = CohortFactory(course_id=self.course.id, name="FirstCohort")
        self.second_cohort = CohortFactory(course_id=self.course.id, name="SecondCohort")

        CohortMembership.assign(cohort=self.first_cohort, user=self.learner_cohort_1)
        CohortMembership.assign(cohort=self.first_cohort, user=self.group_ta_cohort_1)
        CohortMembership.assign(cohort=self.second_cohort, user=self.learner_cohort_2)
        CohortMembership.assign(cohort=self.second_cohort, user=self.group_ta_cohort_2)

    def _assign_enrollments(self):
        """
        Enrolls all the user in the course
        """
        user_list = [self.author] + self.notification_to_all_users
        for user in user_list:
            CourseEnrollment.enroll(user, self.course.id)

    def _create_thread(self, thread_type="discussion", group_id=None):
        """
        Create a thread
        """
        thread = make_minimal_cs_thread({
            'id': 1,
            'course_id': str(self.course.id),
            "commentable_id": self.topic_id,
            "username": self.author.username,
            "user_id": str(self.author.id),
            "thread_type": thread_type,
            "group_id": group_id,
            "title": "Test Title",
        })
        self.register_get_thread_response(thread)
        return thread

    def assert_users_id_list(self, user_ids_1, user_ids_2):
        """
        Assert whether the user ids in two lists are same
        """
        assert len(user_ids_1) == len(user_ids_2)
        for user_id in user_ids_1:
            assert user_id in user_ids_2

    def test_basic(self):
        """
        Left empty intentionally. This test case is inherited from DiscussionAPIViewTestMixin
        """

    def test_not_authenticated(self):
        """
        Left empty intentionally. This test case is inherited from DiscussionAPIViewTestMixin
        """

    def test_no_notification_if_course_has_no_enrollments(self):
        """
        Tests no notification is send if course has no enrollments
        """
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)
        send_thread_created_notification(self.thread['id'], str(self.course.id), self.author.id)
        self.assertEqual(handler.call_count, 0)

    @ddt.data(
        ('new_question_post',),
        ('new_discussion_post',),
    )
    @ddt.unpack
    def test_notification_is_send_to_all_enrollments(self, notification_type):
        """
        Tests notification is send to all users if course is not cohorted
        """
        self._assign_enrollments()
        thread_type = (
            "discussion"
            if notification_type == "new_discussion_post"
            else ("question" if notification_type == "new_question_post" else "")
        )
        thread = self._create_thread(thread_type=thread_type)
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)
        send_thread_created_notification(thread['id'], str(self.course.id), self.author.id)
        self.assertEqual(handler.call_count, 1)
        assert notification_type == handler.call_args[1]['notification_data'].notification_type
        user_ids_list = [user.id for user in self.notification_to_all_users]
        self.assert_users_id_list(user_ids_list, handler.call_args[1]['notification_data'].user_ids)

    @ddt.data(
        ('cohort_1', 'new_question_post'),
        ('cohort_1', 'new_discussion_post'),
        ('cohort_2', 'new_question_post'),
        ('cohort_2', 'new_discussion_post'),
    )
    @ddt.unpack
    def test_notification_is_send_to_cohort_ids(self, cohort_text, notification_type):
        """
        Tests if notification is send only to privileged users and cohort members if the
        course is cohorted
        """
        self._assign_enrollments()
        self._configure_cohorts()
        cohort, audience = (
            (self.first_cohort, self.cohort_1_users)
            if cohort_text == "cohort_1"
            else ((self.second_cohort, self.cohort_2_users) if cohort_text == "cohort_2" else None)
        )

        thread_type = (
            "discussion"
            if notification_type == "new_discussion_post"
            else ("question" if notification_type == "new_question_post" else "")
        )

        cohort_id = cohort.id
        thread = self._create_thread(group_id=cohort_id, thread_type=thread_type)
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)
        send_thread_created_notification(thread['id'], str(self.course.id), self.author.id)
        assert notification_type == handler.call_args[1]['notification_data'].notification_type
        self.assertEqual(handler.call_count, 1)
        user_ids_list = [user.id for user in audience]
        self.assert_users_id_list(user_ids_list, handler.call_args[1]['notification_data'].user_ids)
