import factory
import mock

from django.db.models import signals
from django.db.utils import IntegrityError
from unittest import TestCase

from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from nodebb.constants import (
    TEAM_PLAYER_ENTRY_INDEX,
    CONVERSATIONALIST_ENTRY_INDEX
)
from opaque_keys.edx.keys import CourseKey
from openedx.features.teams.tests.factories import TeamGroupChatFactory
from openedx.features.badging.constants import CONVERSATIONALIST, TEAM_PLAYER
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from openedx.features.badging.models import UserBadge
from student.tests.factories import UserFactory

from .. import constants as badge_constants
from .factories import BadgeFactory, UserBadgeFactory


class UserBadgeModelTestCases(TestCase):

    def setUp(self):
        self.type_conversationalist = CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]
        self.type_team = TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]
        self.team_badge = BadgeFactory(type=self.type_team)

    def test_model_userbadge(self):
        """
        Trying to save a UserBadge model with expected arguments
        """
        course_key = CourseKey.from_string('abc/123/course')
        userbadge_factory = UserBadgeFactory(course_id=course_key)
        userbadge_query = UserBadge.objects.get(course_id=course_key)

        self.assertEqual(userbadge_query.badge, userbadge_factory.badge)
        self.assertEqual(userbadge_query.community_id, 1)
        self.assertEqual(userbadge_query.course_id, course_key)
        self.assertEqual(userbadge_query.user, userbadge_factory.user)

    def test_save_duplicate_badge(self):
        """
        Trying to save a duplicate UserBadge object with expected arguments
        Raises IntegrityError upon trying to save the second object with
        the same arguments
        """
        user = UserFactory.create()

        UserBadgeFactory(user=user, badge=self.team_badge)

        with self.assertRaises(IntegrityError):
            UserBadgeFactory(user=user, badge=self.team_badge)

    def test_community_id_None(self):
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
    def test_assign_conversationalist_badge_with_invalid_community_id(self, mock_get_community_id):
        """
        Assign conversationalist badge for community which do not exist
        """
        mock_get_community_id.return_value = CourseKeyField.Empty
        badge = BadgeFactory(type=self.type_conversationalist)

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=1, badge_id=badge.id, community_id=-1)

        self.assertEqual(
            str(error.exception),
            badge_constants.INVALID_COMMUNITY_ERROR.format(badge_id=badge.id, community_id=-1)
        )

    def test_assign_team_badge_with_invalid_community_id_and_no_team_group_chat(self):
        """
        Assign team badge for team group chat which do not exist
        """
        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=1, badge_id=self.team_badge.id, community_id=-1)

        self.assertEqual(
            str(error.exception),
            badge_constants.INVALID_TEAM_ERROR.format(badge_id=self.team_badge.id, community_id=-1)
        )

    def test_unknown_badge_type(self):
        """
        Assign badge for type which does not exists
        """
        badge = BadgeFactory(type='custom_type')

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=1, badge_id=badge.id, community_id=-1)

        self.assertEqual(
            str(error.exception),
            badge_constants.BADGE_TYPE_ERROR.format(badge_id=badge.id, badge_type='custom_type')
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_assign_team_badge_invalid_course_id(self):
        """
        Assign team badge with invalid course id
        """
        course_team = CourseTeamFactory()
        team_group_chat = TeamGroupChatFactory(team=course_team, room_id=100)

        with self.assertRaises(Exception) as error:
            UserBadge.assign_badge(user_id=UserFactory(), badge_id=self.team_badge.id,
                                   community_id=team_group_chat.room_id)

        self.assertEqual(
            str(error.exception),
            badge_constants.UNKNOWN_COURSE_ERROR.format(badge_id=self.team_badge.id,
                                                        community_id=team_group_chat.room_id)
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_assign_team_badge_successfully(self):
        """
        Trying to save a UserBadge object assigning a team badge successfully
        """
        user = UserFactory()
        course_key = CourseKey.from_string('test/course/123')

        course_team = CourseTeamFactory(course_id=course_key, team_id='team1')

        # Add two users to team, in course
        CourseTeamMembershipFactory(user=user, team=course_team)
        CourseTeamMembershipFactory(user=UserFactory(), team=course_team)

        team_group_chat = TeamGroupChatFactory(team=course_team, room_id=200)

        UserBadge.assign_badge(user_id=user.id, badge_id=self.team_badge.id, community_id=team_group_chat.room_id)

        assigned_user_badges = UserBadge.objects.filter(
            badge_id=self.team_badge.id,
            course_id=course_key,
            community_id=team_group_chat.room_id
        )

        self.assertEqual(len(assigned_user_badges), 2)

    @mock.patch('openedx.features.badging.models.get_course_id_by_community_id')
    def test_assign_conversationalist_badge_successfully(self, mock_course_id_by_community_id):
        """
        Trying to save a UserBadge object assigning a conversationalist badge successfully
        """
        course_key = CourseKey.from_string('abc/xyz/123')
        mock_course_id_by_community_id.return_value = course_key

        badge = BadgeFactory(type=self.type_conversationalist)
        user = UserFactory()

        UserBadge.assign_badge(user_id=user.id, badge_id=badge.id, community_id=1)

        user_badge = UserBadge.objects.get(user_id=user.id, badge_id=badge.id)

        self.assertEqual(user_badge.badge, badge)
        self.assertEqual(user_badge.community_id, 1)
        self.assertEqual(user_badge.course_id, course_key)
        self.assertEqual(user_badge.user, user)
