import unittest

import ddt
import mock
from opaque_keys.edx.keys import CourseKey
from io import StringIO

from lms.djangoapps.teams import csv
from course_modes.models import CourseMode
from lms.djangoapps.teams.models import CourseTeam
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from student.models import CourseEnrollment
from student.roles import CourseStaffRole
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from django.test import TestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.lib.teams_config import TeamsConfig
from student.tests.factories import UserFactory


class TeamMembershipCsvTests(SharedModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(TeamMembershipCsvTests, cls).setUpClass()
        teams_config = TeamsConfig({
            'team_sets': [
                {
                    'id': 'teamset_{}'.format(i),
                    'name': 'teamset_{}_name'.format(i),
                    'description': 'teamset_{}_desc'.format(i),
                }
                for i in [1, 2, 3,4]
            ]
        })
        cls.course = CourseFactory(teams_configuration=teams_config)
        cls.course_no_teamsets = CourseFactory() 

        team1_1 = CourseTeamFactory(course_id=cls.course.id, name='team_1_1', topic_id='teamset_1')
        team1_2 = CourseTeamFactory(course_id=cls.course.id, name='team_1_2', topic_id='teamset_1')
        team2_1 = CourseTeamFactory(course_id=cls.course.id, name='team_2_1', topic_id='teamset_2')
        team2_2 = CourseTeamFactory(course_id=cls.course.id, name='team_2_2', topic_id='teamset_2')
        team3_1 = CourseTeamFactory(course_id=cls.course.id, name='team_3_1', topic_id='teamset_3')
        team3_2 = CourseTeamFactory(course_id=cls.course.id, name='team_3_2', topic_id='teamset_3')
        # No teams in teamset 4 

        user1 = UserFactory.create(username='user1')
        user2 = UserFactory.create(username='user2')
        user3 = UserFactory.create(username='user3')
        user4 = UserFactory.create(username='user4')
        user5 = UserFactory.create(username='user5')

        CourseEnrollmentFactory.create(user=user1, course_id=cls.course.id, mode='audit')
        CourseEnrollmentFactory.create(user=user2, course_id=cls.course.id, mode='verified')
        CourseEnrollmentFactory.create(user=user3, course_id=cls.course.id, mode='honors')
        CourseEnrollmentFactory.create(user=user4, course_id=cls.course.id, mode='masters')
        CourseEnrollmentFactory.create(user=user5, course_id=cls.course.id, mode='masters')

        team1_1.add_user(user1)
        team2_2.add_user(user1)
        team3_1.add_user(user1)

        team1_1.add_user(user2)
        team2_2.add_user(user2)
        team3_1.add_user(user2)

        team2_1.add_user(user3)
        team3_2.add_user(user3)

        team1_1.add_user(user4)
        team3_2.add_user(user4)


    @classmethod
    def _make_team(cls, course_key, teamsets_and_teams, user_config):
        """
        Creates course, teamsets, teams, users.
        Enrolls users in course and assigns them to the specified teams
        Returns (course, teams, users)
        where 
            - course is course,
            - teams is dict mapping team name to CourseTeam
            - users is dict mapping username to User

        Parameters:
            course_key = course key
            teamssets_and_teams = {
                'teamset_1': ['team_1_1', 'team_1_2'],
                'teamset_2': ['team_2_1'],
            }
            user_team_membership = {
                'username1': {
                    'mode': 'masters',
                    'teams': ['team_1_1', 'team_2_1']
                }
                ...
            }
        """


    def setUp(self):
        super(TeamMembershipCsvTests, self).setUp()
        self.buf = StringIO()

    def test_get_headers(self):
        headers = csv.get_team_membership_csv_headers(self.course)
        self.assertEqual(
            headers,
            ['user', 'mode', 'teamset_1', 'teamset_2', 'teamset_3', 'teamset_4']
        )

    def test_get_headers_no_teamsets(self):
        headers = csv.get_team_membership_csv_headers(self.course_no_teamsets)
        self.assertEqual(
            headers,
            ['user', 'mode']
        )

    def test_lookup_team_membership_data(self):
        with self.assertNumQueries(3):
            data = csv._lookup_team_membership_data(self.course)
        self.assertEqual(len(data), 5)
        self.assert_teamset_membership(data[0], 'user1', 'audit',    'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[1], 'user2', 'verified', 'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[2], 'user3', 'honors',     None,      'team_2_1', 'team_3_2')
        self.assert_teamset_membership(data[3], 'user4', 'masters',  'team_1_1',  None,      'team_3_2')
        self.assert_teamset_membership(data[4], 'user5', 'masters',   None,       None,       None)

    def assert_teamset_membership(
        self,
        user_row,
        expected_username,
        expected_mode,
        expected_teamset_1_team,
        expected_teamset_2_team,
        expected_teamset_3_team
    ):
        self.assertEqual(user_row['user'], expected_username)
        self.assertEqual(user_row['mode'], expected_mode)
        self.assertEqual(user_row.get('teamset_1'), expected_teamset_1_team)
        self.assertEqual(user_row.get('teamset_2'), expected_teamset_2_team)
        self.assertEqual(user_row.get('teamset_3'), expected_teamset_3_team)

    def test_load_team_membership_csv(self):
        expected_csv_output = ('user,mode,teamset_1,teamset_2,teamset_3,teamset_4\n'
                               'user1,audit,team_1_1,team_2_2,team_3_1,\n'
                               'user2,verified,team_1_1,team_2_2,team_3_1,\n'
                               'user3,honors,,team_2_1,team_3_2,\n'
                               'user4,masters,team_1_1,,team_3_2,\n'
                               'user5,masters,,,,\n')
        csv.load_team_membership_csv(self.course, self.buf)
        self.assertEqual(expected_csv_output, self.buf.getvalue())
