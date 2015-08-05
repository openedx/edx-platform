# -*- coding: utf-8 -*-
"""Tests for the teams API at the HTTP request level."""
import ddt

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory

from .factories import CourseTeamFactory, CourseTeamMembershipFactory
from ..models import CourseTeamMembership

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

        self.team1 = CourseTeamFactory(course_id=COURSE_KEY1, team_id='team1')
        self.team2 = CourseTeamFactory(course_id=COURSE_KEY2, team_id='team2')

        self.team_membership11 = CourseTeamMembershipFactory(user=self.user1, team=self.team1)
        self.team_membership12 = CourseTeamMembershipFactory(user=self.user2, team=self.team1)
        self.team_membership21 = CourseTeamMembershipFactory(user=self.user1, team=self.team2)

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
