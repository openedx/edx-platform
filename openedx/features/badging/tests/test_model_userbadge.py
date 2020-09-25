"""
Unit tests for UserBadge model
"""
import factory
import mock
from django.db.models import signals
from django.db.utils import IntegrityError
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX, TEAM_PLAYER_ENTRY_INDEX
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from openedx.features.badging.constants import CONVERSATIONALIST, TEAM_PLAYER
from openedx.features.badging.models import UserBadge
from openedx.features.teams.tests.factories import TeamGroupChatFactory
from student.tests.factories import UserFactory

from .. import constants as badge_constants
from .factories import BadgeFactory, UserBadgeFactory


class UserBadgeModelTestCases(TestCase):
    """
    Unit tests for UserBadge model
    """

    def setUp(self):
        super(UserBadgeModelTestCases, self).setUp()
        self.type_conversationalist = CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]
        self.type_team = TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]
        self.team_badge = BadgeFactory(type=self.type_team)
        self.user = UserFactory()

    def test_model_user_badge(self):
        """Save UserBadge model with expected arguments"""
        course_key = CourseKey.from_string('abc/123/course')

        user_badge_factory = UserBadgeFactory(course_id=course_key)

        user_badge_query = UserBadge.objects.get(course_id=course_key)
        self.assertEqual(user_badge_query.badge, user_badge_factory.badge)
        self.assertEqual(user_badge_query.community_id, 1)
        self.assertEqual(user_badge_query.course_id, course_key)
        self.assertEqual(user_badge_query.user, user_badge_factory.user)

    def test_model_user_badge_by_saving_duplicate_badge(self):
        """
        Trying to save a duplicate UserBadge object with expected arguments
        Raises IntegrityError upon trying to save the second object with
        the same arguments
        """
        UserBadgeFactory(user=self.user, badge=self.team_badge)

        with self.assertRaises(IntegrityError):
            UserBadgeFactory(user=self.user, badge=self.team_badge)

    def test_model_user_badge_with_community_id_none(self):
        """
        Trying to save UserBadge object with community_id as None
        """
        with self.assertRaises(IntegrityError):
            UserBadgeFactory(community_id=None)

    def test_assign_badge_wrong_badge_id(self):
        """
        Trying to save a UserBadge object with badge id that does not exist
        """
        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=mock.ANY, badge_id=-1, community_id=mock.ANY)

        self.assertEqual(str(error.exception), badge_constants.BADGE_NOT_FOUND_ERROR.format(badge_id=-1))

    @mock.patch('openedx.features.badging.models.get_course_id_by_community_id')
    def test_assign_badge_conversationalist_with_invalid_community_id(self, mock_get_community_id):
        """
        Assign conversationalist badge for community which do not exist
        """
        mock_get_community_id.return_value = CourseKeyField.Empty
        badge = BadgeFactory(type=self.type_conversationalist)

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=1, badge_id=badge.id, community_id=999)

        self.assertEqual(
            str(error.exception),
            badge_constants.INVALID_COMMUNITY_ERROR.format(badge_id=badge.id, community_id=999)
        )

    def test_assign_badge_team_with_invalid_community_id_and_no_team_group_chat(self):
        """
        Assign team badge for team group chat which do not exist
        """
        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=self.user.id, badge_id=self.team_badge.id, community_id=999)

        self.assertEqual(
            str(error.exception),
            badge_constants.INVALID_TEAM_ERROR.format(badge_id=self.team_badge.id, community_id=999)
        )

    def test_assign_badge_unknown_badge_type(self):
        """
        Assign badge for type which does not exists
        """
        badge = BadgeFactory(type='custom_type')

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=self.user.id, badge_id=badge.id, community_id=999)

        self.assertEqual(
            str(error.exception),
            badge_constants.BADGE_TYPE_ERROR.format(badge_id=badge.id, badge_type='custom_type')
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_assign_badge_for_team_with_invalid_course_id(self):
        """
        Assign team badge with invalid course id, and assert that corresponding error is raised
        """
        course_team = CourseTeamFactory()
        team_group_chat = TeamGroupChatFactory(team=course_team, room_id=100)

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=self.user.id, badge_id=self.team_badge.id,
                                   community_id=team_group_chat.room_id)

        self.assertEqual(
            str(error.exception),
            badge_constants.UNKNOWN_COURSE_ERROR.format(badge_id=self.team_badge.id,
                                                        community_id=team_group_chat.room_id)
        )

    @mock.patch('openedx.features.badging.models.task_user_badge_notify')
    @mock.patch('openedx.features.badging.models.get_course_id_by_community_id')
    def test_assign_badge_conversationalist_to_user_successfully(self, mock_course_id_by_community_id,
                                                                 mock_task_user_badge_notify):
        """
        Assign UserBadge for conversationalist badge successfully, and assert that email and notification
        handler called
        """
        course_key = CourseKey.from_string('abc/xyz/123')
        mock_course_id_by_community_id.return_value = course_key
        badge = BadgeFactory(type=self.type_conversationalist)
        user = self.user

        assigned = UserBadge.assign_badge(user_id=user.id, badge_id=badge.id, community_id=100)

        user_badge = UserBadge.objects.get(user_id=user.id, badge_id=badge.id)
        self.assertEqual(user_badge.badge, badge)
        self.assertEqual(user_badge.community_id, 100)
        self.assertEqual(user_badge.course_id, course_key)
        self.assertEqual(user_badge.user, user)
        self.assertTrue(assigned)
        mock_task_user_badge_notify.assert_has_calls([
            mock.call(user, course_key, badge.name)
        ])


class AssignBadgeToTeamTestCases(TestCase):
    """
    Unit tests for badge assignment to team
    """

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        super(AssignBadgeToTeamTestCases, self).setUp()
        self.team_badge = BadgeFactory(type=TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX])

        self.user_1 = UserFactory()
        self.user_2 = UserFactory()

        self.course_key = CourseKey.from_string(u'test/course/123')
        self.course_team = CourseTeamFactory(course_id=self.course_key, team_id='team1')

        # Add two users to team, in course
        CourseTeamMembershipFactory(user=self.user_1, team=self.course_team)
        CourseTeamMembershipFactory(user=self.user_2, team=self.course_team)
        self.team_group_chat = TeamGroupChatFactory(team=self.course_team, room_id=200)

    @mock.patch('openedx.features.badging.models.task_user_badge_notify')
    def test_assign_badge_to_team_successfully(self, mock_task_user_badge_notify):
        """
        Assign team badge to all team members successfully and assert that
        email and notification task called for each member
        """
        assigned_to_all = UserBadge.assign_badge(
            user_id=self.user_1.id,
            badge_id=self.team_badge.id,
            community_id=self.team_group_chat.room_id
        )

        assigned_user_badges = UserBadge.objects.filter(
            badge_id=self.team_badge.id,
            course_id=self.course_key,
            community_id=self.team_group_chat.room_id
        )
        self.assertEqual(len(assigned_user_badges), 2)
        self.assertTrue(assigned_to_all)
        mock_task_user_badge_notify.assert_has_calls([
            mock.call(self.user_1, self.course_key, self.team_badge.name),
            mock.call(self.user_2, self.course_key, self.team_badge.name),
        ], any_order=True)

    @mock.patch('openedx.features.badging.models.task_user_badge_notify')
    def test_assign_badge_when_one_team_member_already_have_badge(self, mock_task_user_badge_notify):
        """
        Assign team badge to all team members successfully, except one member who has already earned
        team badge. Assert that email and notification task called for only those members who earned
        badge for the first time
        """
        UserBadgeFactory(
            user=self.user_1, course_id=self.course_key,
            community_id=self.team_group_chat.room_id,
            badge=self.team_badge
        )

        assigned_to_all = UserBadge.assign_badge(
            user_id=self.user_1.id,
            badge_id=self.team_badge.id,
            community_id=self.team_group_chat.room_id
        )

        assigned_user_badges = UserBadge.objects.filter(
            badge_id=self.team_badge.id,
            course_id=self.course_key,
            community_id=self.team_group_chat.room_id
        )
        self.assertEqual(len(assigned_user_badges), 2)
        self.assertFalse(assigned_to_all)
        mock_task_user_badge_notify.assert_has_calls([
            mock.call(self.user_2, self.course_key, self.team_badge.name),
        ])
