"""
Unit tests for missing badges assignment
"""
import factory
from django.db.models import signals
from django.test import TestCase
from mock import patch
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from nodebb.constants import TEAM_PLAYER_ENTRY_INDEX
from openedx.features.badging.constants import BADGE_ID_KEY, TEAM_PLAYER
from openedx.features.badging.models import UserBadge
from openedx.features.teams.tests.factories import TeamGroupChatFactory
from student.tests.factories import UserFactory

from .factories import BadgeFactory, UserBadgeFactory


class MissingBadgeTestCase(TestCase):
    """
    Unit test the missing badge assignment
    """

    def setUp(self):
        super(MissingBadgeTestCase, self).setUp()
        self.team_badge = BadgeFactory(type=TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX])
        self.course_key = CourseKey.from_string('abc/course/123')
        self.test_chat_room_id = 200

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_assign_missing_team_badges(self):
        old_user = UserFactory()
        new_user = UserFactory()
        course_team = CourseTeamFactory(course_id=self.course_key, team_id='team1')
        team_group_chat = TeamGroupChatFactory(team=course_team, room_id=self.test_chat_room_id)

        # Add first user to team in course
        CourseTeamMembershipFactory(user=old_user, team=course_team)

        # Assigning badge to user in team
        UserBadgeFactory(user=old_user, badge=self.team_badge, community_id=team_group_chat.room_id)

        assigned_user_badges = UserBadge.objects.filter(
            user_id=old_user.id
        ).values(BADGE_ID_KEY)

        # Add second user to team in course
        CourseTeamMembershipFactory(user=new_user, team=course_team)

        # Assigning missing badges to second user
        UserBadge.assign_missing_team_badges(new_user.id, course_team.id)

        assigned_user2_badges = UserBadge.objects.filter(
            user_id=new_user.id
        ).values(BADGE_ID_KEY)

        self.assertEqual(len(assigned_user_badges), len(assigned_user2_badges))

    def test_assign_missing_team_badges_with_invalid_params(self):
        with self.assertRaises(Exception):
            UserBadge.assign_missing_team_badges(None, None)

    @patch('openedx.features.badging.models.UserBadge.objects.get_or_create')
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_assign_missing_team_badges_distinct_earned_badges(self, mock_get_or_create):
        old_user = UserFactory()
        old_user_2 = UserFactory()
        new_user = UserFactory()
        course_team = CourseTeamFactory(course_id=self.course_key, team_id='team1')
        team_group_chat = TeamGroupChatFactory(team=course_team, room_id=self.test_chat_room_id)

        # Add two users to team in course
        CourseTeamMembershipFactory(user=old_user, team=course_team)
        CourseTeamMembershipFactory(user=old_user_2, team=course_team)

        # Assigning badge to users in team
        UserBadgeFactory(user=old_user, badge=self.team_badge, community_id=team_group_chat.room_id)
        UserBadgeFactory(user=old_user_2, badge=self.team_badge, community_id=team_group_chat.room_id)

        # Adding third user to team in course
        CourseTeamMembershipFactory(user=new_user, team=course_team)

        # Assigning missing badges to third user
        UserBadge.assign_missing_team_badges(new_user.id, course_team.id)

        # The mocked function should only be called once
        self.assertEqual(mock_get_or_create.call_count, 1)
