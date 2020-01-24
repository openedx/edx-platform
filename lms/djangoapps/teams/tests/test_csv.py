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
        cls.user_config = {
            'user1': {
                'mode': 'audit',
                'teams': ['team_1_1', 'team_2_2', 'team_3_1']
            },
            'user2': {
                'mode': 'verified',
                'teams': ['team_1_1', 'team_2_2', 'team_3_1']
            },
            'user3': {
                'mode': 'audit',
                'teams': ['team_2_1', 'team_3_2']
            },
            'user4': {
                'mode': 'masters',
                'teams': ['team_1_1', 'team_3_2']
            },
            'user5': {
                'mode': 'masters',
                'teams': []
            },
        }

        cls.course, cls.teams, cls.users = cls._make_team(
            CourseKey.from_string('edx/history/1'),
            {
                'teamset_1': ['team_1_1', 'team_1_2'],
                'teamset_2': ['team_2_1', 'team_2_2'],
                'teamset_3': ['team_3_1', 'team_3_2'],
                'teamset_4': [],
            },
            cls.user_config,
        )

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
        import pdb; pdb.set_trace()
        teams_config = TeamsConfig({
            'teamsets': [
                {
                    'id': teamset,
                    'name': teamset + '_name',
                    'description': teamset + '_desc',
                }
                for teamset in teamsets_and_teams
            ]
        })
        course = CourseFactory(teams_configuration=teams_config)
        teams = {}
        for teamset_id in teamsets_and_teams:
            for team_name in teamsets_and_teams[teamset_id]:
                team = CourseTeamFactory(
                    course_id=course.id,
                    name=team_name,
                    topic_id=teamset_id,
                )
                teams[team_name] = team

        users = {}
        for username in user_config:
            user = UserFactory.create(username=username)
            CourseEnrollmentFactory.create(
                user=user,
                course_id=course.id,
                mode=user_config[username]['mode']
            )
            for team_name in user_config[username]['teams']:
                teams[team_name].add_user(user)
            users[username] = user

        return course, teams, users


    def setUp(self):
        super(TeamMembershipCsvTests, self).setUp()
        self.buf = StringIO()

    def test_get_headers(self):
        headers = csv.get_team_membership_csv_headers(self.course)
        self.assertEqual(
            headers,
            ['user', 'mode', 'teamset_1', 'teamset_2', 'teamset_3']
        )

    def test_get_headers_no_teamsets(self):
        course, _, _ = self._make_team(
            CourseKey.from_string('edx/history/2'),
            {},
            {'another_user_1': [], 'another_user_2': [], 'another_user_3': []},
        )
        headers = csv.get_team_membership_csv_headers(self.course)
        self.assertEqual(
            headers,
            ['user', 'mode']
        )

    def test_lookup_team_membership_data(self):
        data = csv._lookup_team_membership_data(self.course)
        self.assertEqual(len(data), 5)
        self.assert_teamset_membership(data[0], 'user1', 'audit',    'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[1], 'user2', 'verified', 'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[2], 'user3', 'audit',     None,      'team_2_1', 'team_3_2')
        self.assert_teamset_membership(data[3], 'user4', 'verified', 'team_1_1',  None,      'team_3_2')
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
        self.assertEqual(len(user_row), 5)

    def test_load_team_membership_csv(self):
        csv_text = csv.load_team_membership_csv(self.course, self.buf)
        print(csv_text)
        self.fail()

