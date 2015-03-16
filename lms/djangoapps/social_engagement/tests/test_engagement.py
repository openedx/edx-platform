"""
Tests for the social_engagment subsystem

paver test_system -s lms --test_id=lms/djangoapps/social_engagements/tests/test_engagement.py
"""

from django.conf import settings
from django.db import IntegrityError

from mock import MagicMock, patch
from datetime import datetime, timedelta
import pytz

from django.test import TestCase
from django.test.utils import override_settings


from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.factories import CourseFactory

from social_engagement.models import StudentSocialEngagementScore, StudentSocialEngagementScoreHistory

from social_engagement.engagement import update_user_engagement_score
from social_engagement.engagement import update_course_engagement_scores
from social_engagement.engagement import update_all_courses_engagement_scores

from edx_notifications.startup import initialize as initialize_notifications
from edx_notifications.lib.consumer import get_notifications_count_for_user


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch.dict(settings.FEATURES, {'ENABLE_NOTIFICATIONS': True})
@patch.dict(settings.FEATURES, {'ENABLE_SOCIAL_ENGAGEMENT': True})
class StudentEngagementTests(TestCase):
    """ Test suite for CourseModuleCompletion """

    def setUp(self):
        self.user = UserFactory()
        self.user2 = UserFactory()

        self._create_course()

        initialize_notifications()

    def _create_course(self, start=None, end=None):
        self.course = CourseFactory.create(
            start=start,
            end=end
        )

        CourseEnrollment.enroll(self.user, self.course.id)
        CourseEnrollment.enroll(self.user2, self.course.id)

    def test_no_engagment_records(self):
        """
        Verify that we get None back
        """

        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user.id))
        self.assertIsNone(StudentSocialEngagementScore.get_user_engagement_score(self.course.id, self.user2.id))

        # no entries, means a rank of 0!
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            0
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            0
        )

        self.assertFalse(
            StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        )

    def test_save_first_engagement_score(self):
        """
        Basic write operation
        """

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)

        StudentSocialEngagementScore.save_user_engagement_score(self.course.id, self.user.id, 10)

        # read it back
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            10
        )

        # confirm there is an entry in the History table
        self.assertEqual(
            StudentSocialEngagementScoreHistory.objects.filter(
                course_id=self.course.id,
                user__id=self.user.id
            ).count(),
            1
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            1
        )

        # look at the leaderboard
        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        self.assertIsNotNone(leaderboard)
        self.assertEqual(len(leaderboard), 1)

        self.assertEqual(leaderboard[0]['user__id'], self.user.id)
        self.assertEqual(leaderboard[0]['score'], 10)

        # confirm there is a notification was generated
        self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

    def test_update_engagement_score(self):
        """
        Basic update operation
        """

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)

        StudentSocialEngagementScore.save_user_engagement_score(self.course.id, self.user.id, 10)

        # then update
        StudentSocialEngagementScore.save_user_engagement_score(self.course.id, self.user.id, 20)

        # read it back
        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['score'],
            20
        )

        # confirm there are two entries in the History table
        self.assertEqual(
            StudentSocialEngagementScoreHistory.objects.filter(
                course_id=self.course.id,
                user__id=self.user.id
            ).count(),
            2
        )

        self.assertEqual(
            StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )['position'],
            1
        )

        # look at the leaderboard
        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        self.assertIsNotNone(leaderboard)
        self.assertEqual(len(leaderboard), 1)

        self.assertEqual(leaderboard[0]['user__id'], self.user.id)
        self.assertEqual(leaderboard[0]['score'], 20)

        # confirm there is a just a single notification was generated
        self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

    def test_score_integrity(self):
        """
        Make sure we can't have duplicate course_id/user_id pais
        """

        StudentSocialEngagementScore.save_user_engagement_score(self.course.id, self.user.id, 10)

        again = StudentSocialEngagementScore(course_id=self.course.id, user_id=self.user.id, score=20)

        with self.assertRaises(IntegrityError):
            again.save()

    def test_update_user_engagement_score(self):
        """
        Run the engagement calculation for a user in a course
        """

        self.assertEqual(get_notifications_count_for_user(self.user.id), 0)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            update_user_engagement_score(self.course.id, self.user.id)

            leaderboard_position = StudentSocialEngagementScore.get_user_leaderboard_position(
                self.course.id,
                self.user.id
            )

            self.assertEqual(
                leaderboard_position['score'],
                24
            )

            self.assertEqual(
                leaderboard_position['position'],
                1
            )

            self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

    def test_multiple_users(self):
        """
        See if it works with more than one enrollee
        """

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

            update_user_engagement_score(self.course.id, self.user.id)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 2,
                'num_comments': 2,
                'num_replies': 2,
                'num_upvotes': 2,
                'num_thread_followers': 2,
                'num_comments_generated': 2,
            }

            update_user_engagement_score(self.course.id, self.user2.id)

        leaderboard_position = StudentSocialEngagementScore.get_user_leaderboard_position(
            self.course.id,
            self.user.id
        )

        self.assertEqual(
            leaderboard_position['score'],
            24
        )

        # user should be in place #2
        self.assertEqual(
            leaderboard_position['position'],
            2
        )

        self.assertEqual(get_notifications_count_for_user(self.user.id), 1)

        leaderboard_position = StudentSocialEngagementScore.get_user_leaderboard_position(
            self.course.id,
            self.user2.id
        )

        self.assertEqual(
            leaderboard_position['score'],
            48
        )

        # user2 should be in place #1
        self.assertEqual(
            leaderboard_position['position'],
            1
        )

        self.assertEqual(get_notifications_count_for_user(self.user2.id), 1)

    def test_calc_course(self):
        """
        Verifies that we can calculate the whole course enrollments
        """

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            # update whole course and re-calc
            update_course_engagement_scores(self.course.id)

        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)

        self.assertEqual(len(leaderboard), 2)

    def test_all_courses(self):
        """
        Verifies that we can calculate over all courses
        """

        course2 = CourseFactory.create(org='foo', course='bar', run='baz')

        CourseEnrollment.enroll(self.user, course2.id)

        self.assertEqual(CourseEnrollment.objects.filter(course_id=course2.id).count(), 1)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            # update whole course and re-calc
            update_all_courses_engagement_scores()

        leaderboard = StudentSocialEngagementScore.generate_leaderboard(self.course.id)
        self.assertEqual(len(leaderboard), 2)

        leaderboard = StudentSocialEngagementScore.generate_leaderboard(course2.id)
        self.assertEqual(len(leaderboard), 1)

    def test_closed_course(self):
        """
        Make sure we can force update closed course
        """

        course2 = CourseFactory.create(
            org='foo',
            course='bar',
            run='baz',
            end=datetime.now(pytz.UTC)-timedelta(days=1)
        )

        CourseEnrollment.enroll(self.user, course2.id)
        CourseEnrollment.enroll(self.user2, course2.id)

        with patch('social_engagement.engagement._get_user_social_stats') as mock_func:
            mock_func.return_value = {
                'num_threads': 1,
                'num_comments': 1,
                'num_replies': 1,
                'num_upvotes': 1,
                'num_thread_followers': 1,
                'num_comments_generated': 1,
            }

            # update whole course and re-calc
            update_all_courses_engagement_scores()

            # shouldn't be anything in there because course is closed
            leaderboard = StudentSocialEngagementScore.generate_leaderboard(course2.id)
            self.assertEqual(len(leaderboard), 0)

            # update whole course and re-calc
            update_all_courses_engagement_scores(compute_if_closed_course=True)

            # shouldn't be anything in there because course is closed
            leaderboard = StudentSocialEngagementScore.generate_leaderboard(course2.id)
            self.assertEqual(len(leaderboard), 2)
