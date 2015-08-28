# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""Tests for the teams API at the HTTP request level."""
import ddt

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from opaque_keys.edx.keys import CourseKey
from student.tests.factories import CourseEnrollmentFactory, UserFactory

from .factories import CourseTeamFactory
from ..models import CourseTeam, CourseTeamMembership

COURSE_KEY1 = CourseKey.from_string('edx/history/1')
COURSE_KEY2 = CourseKey.from_string('edx/history/2')


@ddt.ddt
class TeamMembershipTest(SharedModuleStoreTestCase):
    """Tests for the TeamMembership model."""

    def setUp(self):
        """
        Set up tests.
        """
        super(TeamMembershipTest, self).setUp()

        self.user1 = UserFactory.create(username='user1')
        self.user2 = UserFactory.create(username='user2')
        self.user3 = UserFactory.create(username='user3')

        for user in (self.user1, self.user2, self.user3):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY1)
        CourseEnrollmentFactory.create(user=self.user1, course_id=COURSE_KEY2)

        self.team1 = CourseTeamFactory(course_id=COURSE_KEY1, team_id='team1')
        self.team2 = CourseTeamFactory(course_id=COURSE_KEY2, team_id='team2')

        self.team_membership11 = self.team1.add_user(self.user1)
        self.team_membership12 = self.team1.add_user(self.user2)
        self.team_membership21 = self.team2.add_user(self.user1)

    def test_membership_last_activity_set(self):
        current_last_activity = self.team_membership11.last_activity_at
        # Assert that the first save in the setUp sets a value.
        self.assertIsNotNone(current_last_activity)

        self.team_membership11.save()

        # Verify that we only change the last activity_at when it doesn't
        # already exist.
        self.assertEqual(self.team_membership11.last_activity_at, current_last_activity)

    def test_team_size_delete_membership(self):
        """Test that the team size field is correctly updated when deleting a
        team membership.
        """
        self.assertEqual(self.team1.team_size, 2)
        self.team_membership11.delete()
        team = CourseTeam.objects.get(id=self.team1.id)
        self.assertEqual(team.team_size, 1)

    def test_team_size_create_membership(self):
        """Test that the team size field is correctly updated when creating a
        team membership.
        """
        self.assertEqual(self.team1.team_size, 2)
        self.team1.add_user(self.user3)
        team = CourseTeam.objects.get(id=self.team1.id)
        self.assertEqual(team.team_size, 3)

    @ddt.data(
        (None, None, None, 3),
        ('user1', None, None, 2),
        ('user1', [COURSE_KEY1], None, 1),
        ('user1', None, 'team1', 1),
        ('user2', None, None, 1),
    )
    @ddt.unpack
    def test_get_memberships(self, username, course_ids, team_id, expected_count):
        self.assertEqual(
            CourseTeamMembership.get_memberships(username=username, course_ids=course_ids, team_id=team_id).count(),
            expected_count
        )

    @ddt.data(
        ('user1', COURSE_KEY1, True),
        ('user2', COURSE_KEY1, True),
        ('user2', COURSE_KEY2, False),
    )
    @ddt.unpack
    def test_user_in_team_for_course(self, username, course_id, expected_value):
        user = getattr(self, username)
        self.assertEqual(
            CourseTeamMembership.user_in_team_for_course(user, course_id),
            expected_value
        )
