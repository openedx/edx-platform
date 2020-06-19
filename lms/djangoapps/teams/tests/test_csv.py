""" Tests for the functionality in csv """

from csv import DictReader
from io import StringIO

from django.contrib.auth.models import User

from lms.djangoapps.teams import csv
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.lib.teams_config import TeamsConfig


class TeamMembershipCsvTests(SharedModuleStoreTestCase):
    """ Tests for functionality related to the team membership csv report """
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
                for i in [1, 2, 3, 4]
            ]
        })
        cls.course = CourseFactory(teams_configuration=teams_config)
        cls.course_no_teamsets = CourseFactory()

        team1_1 = CourseTeamFactory(course_id=cls.course.id, name='team_1_1', topic_id='teamset_1')
        CourseTeamFactory(course_id=cls.course.id, name='team_1_2', topic_id='teamset_1')
        team2_1 = CourseTeamFactory(course_id=cls.course.id, name='team_2_1', topic_id='teamset_2')
        team2_2 = CourseTeamFactory(course_id=cls.course.id, name='team_2_2', topic_id='teamset_2')
        team3_1 = CourseTeamFactory(course_id=cls.course.id, name='team_3_1', topic_id='teamset_3')
        # protected team
        team3_2 = CourseTeamFactory(
            course_id=cls.course.id,
            name='team_3_2',
            topic_id='teamset_3',
            organization_protected=True
        )
        #  No teams in teamset 4

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
        team3_1.add_user(user3)

        team3_2.add_user(user4)

    def setUp(self):
        super(TeamMembershipCsvTests, self).setUp()
        self.buf = StringIO()

    def test_get_headers(self):
        # pylint: disable=protected-access
        headers = csv._get_team_membership_csv_headers(self.course)
        self.assertEqual(
            headers,
            ['user', 'mode', 'teamset_1', 'teamset_2', 'teamset_3', 'teamset_4']
        )

    def test_get_headers_no_teamsets(self):
        # pylint: disable=protected-access
        headers = csv._get_team_membership_csv_headers(self.course_no_teamsets)
        self.assertEqual(
            headers,
            ['user', 'mode']
        )

    def test_lookup_team_membership_data(self):
        with self.assertNumQueries(3):
            # pylint: disable=protected-access
            data = csv._lookup_team_membership_data(self.course)
        self.assertEqual(len(data), 5)
        self.assert_teamset_membership(data[0], 'user1', 'audit', 'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[1], 'user2', 'verified', 'team_1_1', 'team_2_2', 'team_3_1')
        self.assert_teamset_membership(data[2], 'user3', 'honors', None, 'team_2_1', 'team_3_1')
        self.assert_teamset_membership(data[3], 'user4', 'masters', None, None, 'team_3_2')
        self.assert_teamset_membership(data[4], 'user5', 'masters', None, None, None)

    def assert_teamset_membership(
        self,
        user_row,
        expected_username,
        expected_mode,
        expected_teamset_1_team,
        expected_teamset_2_team,
        expected_teamset_3_team
    ):
        """
        Assert that user_row has the expected
            -username
            -mode
            -team name for teamset_(123)
        """
        self.assertEqual(user_row['user'], expected_username)
        self.assertEqual(user_row['mode'], expected_mode)
        self.assertEqual(user_row.get('teamset_1'), expected_teamset_1_team)
        self.assertEqual(user_row.get('teamset_2'), expected_teamset_2_team)
        self.assertEqual(user_row.get('teamset_3'), expected_teamset_3_team)

    def test_load_team_membership_csv(self):
        expected_csv_output = ('user,mode,teamset_1,teamset_2,teamset_3,teamset_4\r\n'
                               'user1,audit,team_1_1,team_2_2,team_3_1,\r\n'
                               'user2,verified,team_1_1,team_2_2,team_3_1,\r\n'
                               'user3,honors,,team_2_1,team_3_1,\r\n'
                               'user4,masters,,,team_3_2,\r\n'
                               'user5,masters,,,,\r\n')
        csv.load_team_membership_csv(self.course, self.buf)
        self.assertEqual(expected_csv_output, self.buf.getvalue())


# pylint: disable=no-member
class TeamMembershipImportManagerTests(SharedModuleStoreTestCase):
    """ Tests for TeamMembershipImportManager """
    @classmethod
    def setUpClass(cls):
        super(TeamMembershipImportManagerTests, cls).setUpClass()
        teams_config = TeamsConfig({
            'team_sets': [{
                'id': 'teamset_1',
                'name': 'teamset_name',
                'description': 'teamset_desc',
                'max_team_size': 3,
            }]
        })
        cls.course = CourseFactory(teams_configuration=teams_config)
        cls.second_course = CourseFactory(teams_configuration=teams_config)
        cls.import_manager = None

    def setUp(self):
        # initialize import manager
        super(TeamMembershipImportManagerTests, self).setUp()
        self.import_manager = csv.TeamMembershipImportManager(self.course)
        self.import_manager.teamset_ids = {ts.teamset_id for ts in self.course.teamsets}

    def tearDown(self):
        """ Clean up users, teams, and memberships created during tests """
        super(TeamMembershipImportManagerTests, self).tearDown()
        CourseTeamMembership.objects.all().delete()
        CourseTeam.objects.all().delete()
        User.objects.all().delete()

    def test_add_user_to_new_protected_team(self):
        """Adding a masters learner to a new team should create a team with organization protected status"""
        masters_learner = UserFactory.create(username='masters_learner')
        CourseEnrollmentFactory.create(user=masters_learner, course_id=self.course.id, mode='masters')
        row = {
            'mode': 'masters',
            'teamset_1': 'new_protected_team',
            'user': masters_learner
        }

        self.import_manager.add_user_to_team(row)
        self.assertTrue(CourseTeam.objects.get(team_id__startswith='new_protected_team').organization_protected)

    def test_add_user_to_new_unprotected_team(self):
        """Adding a non-masters learner to a new team should create a team with no organization protected status"""
        audit_learner = UserFactory.create(username='audit_learner')
        CourseEnrollmentFactory.create(user=audit_learner, course_id=self.course.id, mode='audit')
        row = {
            'mode': 'audit',
            'teamset_1': 'new_unprotected_team',
            'user': audit_learner
        }

        self.import_manager.add_user_to_team(row)
        self.assertFalse(CourseTeam.objects.get(team_id__startswith='new_unprotected_team').organization_protected)

    def test_team_removals_are_scoped_correctly(self):
        """ Team memberships should not search across topics in different courses """
        # Given a learner enrolled in similarly named teamsets across 2 courses
        audit_learner = UserFactory.create(username='audit_learner')

        CourseEnrollmentFactory.create(user=audit_learner, course_id=self.course.id, mode='audit')
        course_1_team = CourseTeamFactory(course_id=self.course.id, name='cross_course_test', topic_id='teamset_1')
        course_1_team.add_user(audit_learner)

        CourseEnrollmentFactory.create(user=audit_learner, course_id=self.second_course.id, mode='audit')
        course_2_team = CourseTeamFactory(
            course_id=self.second_course.id,
            name='cross_course_test',
            topic_id='teamset_1'
        )
        course_2_team.add_user(audit_learner)

        self.assertTrue(CourseTeamMembership.is_user_on_team(audit_learner, course_1_team))

        # When I try to remove them from the team
        row = {
            'mode': 'audit',
            'teamset_1': None,
            'user': audit_learner
        }
        self.import_manager.remove_user_from_team_for_reassignment(row)

        # They are successfully removed from the team
        self.assertFalse(CourseTeamMembership.is_user_on_team(audit_learner, course_1_team))

    def test_exceed_max_size(self):
        # Given a bunch of students enrolled in a course
        users = []
        for i in range(5):
            user = UserFactory.create(username='max_size_{id}'.format(id=i))
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id, mode='audit')
            users.append(user)

        # When a team is already near capaciy
        for i in range(2):
            user = users[i]
            row = {'user': user, 'teamset_1': 'team_1', 'mode': 'audit'}
            self.import_manager.add_user_to_team(row)

        # ... and I try to add members in excess of capacity
        csv_data = self._csv_reader_from_array([
            ['user','mode', 'teamset_1'],
            ['max_size_2', 'audit', 'team_1'],
            ['max_size_3', 'audit', 'team_1']
        ])

        result = self.import_manager.set_team_memberships(csv_data)

        # Then membership size is exceeded and the import fails with a "team is full" error
        self.assertFalse(result)
        self.assertEqual(self.import_manager.validation_errors[0], 'Team team_1 is full.')

    def test_remove_from_team(self):
        # Given a user already in a course and on a team
        user = UserFactory.create(username='learner_1')
        mode = 'audit'
        CourseEnrollmentFactory.create(user=user, course_id=self.course.id, mode=mode)
        team = CourseTeamFactory(course_id=self.course.id, name='team_1', topic_id='teamset_1')
        team.add_user(user)
        self.assertTrue(CourseTeamMembership.is_user_on_team(user, team))

        # When I try to remove them from the team
        csv_data = self._csv_reader_from_array([
            ['user','mode', 'teamset_1'],
            [user.username, mode, ''],
        ])
        result = self.import_manager.set_team_memberships(csv_data)

        # Then they are removed from the team
        self.assertFalse(CourseTeamMembership.is_user_on_team(user, team))

    def test_switch_memberships(self):
        # Given a bunch of students enrolled in a course
        users = []
        for i in range(5):
            user = UserFactory.create(username='learner_{id}'.format(id=i))
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id, mode='audit')
            users.append(user)

        # When a team is already at/near capaciy
        for i in range(3):
            user = users[i]
            row = {'user': user, 'teamset_1': 'team_1', 'mode': 'audit'}
            self.import_manager.add_user_to_team(row)

        # ... and I try to switch membership (add/remove)
        csv_data = self._csv_reader_from_array([
            ['user','mode', 'teamset_1'],
            ['learner_4', 'audit', 'team_1'],
            ['learner_0', 'audit', 'team_2'],
        ])

        result = self.import_manager.set_team_memberships(csv_data)

        # Then membership size is calculated correctly, import finishes w/out error
        self.assertTrue(result)
        # ... and the users are assigned to the correct teams
        team_1 = CourseTeam.objects.get(course_id=self.course.id, topic_id='teamset_1', name='team_1')
        team_2 = CourseTeam.objects.get(course_id=self.course.id, topic_id='teamset_1', name='team_2')
        self.assertTrue(CourseTeamMembership.is_user_on_team(users[4], team_1))
        self.assertTrue(CourseTeamMembership.is_user_on_team(users[0], team_2))

    def test_create_new_team_from_import(self):
        # Given a user in a course
        user = UserFactory.create(username='learner_1')
        mode = 'audit'
        CourseEnrollmentFactory.create(user=user, course_id=self.course.id, mode=mode)

        # When I add them to a team that does not exist
        self.assertEquals(CourseTeam.objects.all().count(), 0)
        csv_data = self._csv_reader_from_array([
            ['user','mode', 'teamset_1'],
            [user.username, mode, 'new_exciting_team'],
        ])
        result = self.import_manager.set_team_memberships(csv_data)

        # Then a new team is created
        self.assertEqual(CourseTeam.objects.all().count(), 1)

        # ... and the user is assigned to the team
        new_team = CourseTeam.objects.get(topic_id='teamset_1', name='new_exciting_team')
        self.assertTrue(CourseTeamMembership.is_user_on_team(user, new_team))

    def _csv_reader_from_array(self, rows):
        """
        Given a 2D array, treat each element as a cell of a CSV file and construct a reader

        Example:
            [['header1', 'header2'], ['r1:c1', 'r1:c2'], ['r2:c2', 'r3:c3'] ... ]
        """
        return DictReader((','.join(row) for row in rows))