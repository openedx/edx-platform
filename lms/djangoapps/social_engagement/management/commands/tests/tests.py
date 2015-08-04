"""
Tests for the social_engagment subsystem

paver test_system -s lms --test_id=lms/djangoapps/social_engagements/tests/test_engagement.py
"""

from django.conf import settings

from mock import MagicMock, patch

from django.test.utils import override_settings

from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config

from social_engagement.models import StudentSocialEngagementScore, StudentSocialEngagementScoreHistory
from social_engagement.engagement import update_user_engagement_score
from social_engagement.engagement import update_course_engagement_scores
from social_engagement.engagement import update_all_courses_engagement_scores

from edx_notifications.startup import initialize as initialize_notifications
from edx_notifications.lib.consumer import get_notifications_count_for_user

from social_engagement.management.commands.generate_engagement_entries import Command

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@patch.dict(settings.FEATURES, {'ENABLE_NOTIFICATIONS': True})
@patch.dict(settings.FEATURES, {'ENABLE_SOCIAL_ENGAGEMENT': True})
class StudentEngagementTests(ModuleStoreTestCase):
    """ Test suite for CourseModuleCompletion """

    def setUp(self):
        super(StudentEngagementTests, self).setUp()
        self.user = UserFactory()
        self.user2 = UserFactory()

        self._create_course()

        initialize_notifications()

    def _create_course(self, start=None, end=None):
        self.course = CourseFactory.create(
            start=start,
            end=end
        )

        self.course2 = CourseFactory.create(
            org='foo',
            course='bar',
            run='baz',
            start=start,
            end=end
        )

        CourseEnrollment.enroll(self.user, self.course.id)
        CourseEnrollment.enroll(self.user2, self.course.id)

        CourseEnrollment.enroll(self.user, self.course2.id)

    def test_management_command(self):
        """
        Verify that we get None back
        """

        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user.id))
        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user2.id))

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
        self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            Command().handle()

            # shouldn't be anything in there because course is closed
            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
            self.assertEqual(len(leaderboard), 2)

            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course2.id)
            self.assertEqual(len(leaderboard), 1)

            self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
            self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

    def test_management_command_course(self):
        """
        Verify that we get None back
        """

        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user.id))
        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user2.id))

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
        self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            Command().handle(course_ids=[self.course.id])

            # shouldn't be anything in there because course is closed
            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
            self.assertEqual(len(leaderboard), 2)

            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course2.id)
            self.assertEqual(len(leaderboard), 0)

            self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
            self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

    def test_management_command_user(self):
        """
        Verify that we get None back
        """

        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user.id))
        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user2.id))

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
        self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            Command().handle(course_ids=[self.course.id], user_ids=[self.user.id])

            # shouldn't be anything in there because course is closed
            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
            self.assertEqual(len(leaderboard), 1)
            self.assertEqual(leaderboard[0]['user__id'], self.user.id)

            leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course2.id)
            self.assertEqual(len(leaderboard), 0)

            self.assertEqual(get_notifications_count_for_user(self.user.id), 0)
            self.assertEqual(get_notifications_count_for_user(self.user2.id), 0)

