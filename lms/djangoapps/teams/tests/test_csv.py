""" Tests for the functionality in csv """
from csv import DictWriter, DictReader
from io import BytesIO, StringIO, TextIOWrapper

from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory, ProgramCourseEnrollmentFactory
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
            }]
        })
        cls.course = CourseFactory(teams_configuration=teams_config)
        cls.second_course = CourseFactory(teams_configuration=teams_config)

        # initialize import manager
        cls.import_manager = csv.TeamMembershipImportManager(cls.course)
        cls.import_manager.teamset_ids = {ts.teamset_id for ts in cls.course.teamsets}

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


class ExternalKeyCsvTests(SharedModuleStoreTestCase):
    """ Tests for functionality related to external_user_keys"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.teamset_id = 'teamset_id'
        teams_config = TeamsConfig({
            'team_sets': [
                {
                    'id': cls.teamset_id,
                    'name': 'teamset_name',
                    'description': 'teamset_desc',
                }
            ]
        })
        cls.course = CourseFactory(teams_configuration=teams_config)
        # pylint: disable=protected-access
        cls.header_fields = csv._get_team_membership_csv_headers(cls.course)

        cls.team = CourseTeamFactory(course_id=cls.course.id, name='team_name', topic_id=cls.teamset_id)

        cls.user_no_program = UserFactory.create()
        cls.user_in_program = UserFactory.create()
        cls.user_in_program_no_external_id = UserFactory.create()
        cls.user_in_program_not_enrolled_through_program = UserFactory.create()

        # user_no_program is only enrolled in the course
        cls.add_user_to_course_program_team(cls.user_no_program, enroll_in_program=False)

        # user_in_program is enrolled in the course and the program, with an external_id
        cls.external_user_key = 'externalProgramUserId-123'
        cls.add_user_to_course_program_team(cls.user_in_program, external_user_key=cls.external_user_key)

        # user_in_program is enrolled in the course and the program, with no external_id
        cls.add_user_to_course_program_team(cls.user_in_program_no_external_id)

        # user_in_program_not_enrolled_through_program is enrolled in a program and the course, but they not connected
        cls.add_user_to_course_program_team(
            cls.user_in_program_not_enrolled_through_program, connect_enrollments=False
        )

        # initialize import manager
        cls.import_manager = csv.TeamMembershipImportManager(cls.course)
        cls.import_manager.teamset_ids = {ts.teamset_id for ts in cls.course.teamsets}

    @classmethod
    def add_user_to_course_program_team(
        cls, user, add_to_team=True, enroll_in_program=True, connect_enrollments=True, external_user_key=None
    ):
        """
        Set up a test user by enrolling them in self.course, and then optionaly:
            - enroll them in a program
            - link their program and course enrollments
            - give their program enrollment an external_user_key
        """
        course_enrollment = CourseEnrollmentFactory.create(user=user, course_id=cls.course.id)
        if add_to_team:
            cls.team.add_user(user)
        if enroll_in_program:
            program_enrollment = ProgramEnrollmentFactory.create(user=user, external_user_key=external_user_key)
            if connect_enrollments:
                ProgramCourseEnrollmentFactory.create(
                    program_enrollment=program_enrollment, course_enrollment=course_enrollment
                )

    def assert_user_on_team(self, user):
        self.assertTrue(CourseTeamMembership.is_user_on_team(user, self.team))

    def assert_user_not_on_team(self, user):
        self.assertFalse(CourseTeamMembership.is_user_on_team(user, self.team))

    def test_add_user_to_team_with_external_key(self):
        # Make a new user with an external_user_key who is enrolled in the course and program, with an external_key,
        #  but is not on the team
        new_user = UserFactory.create()
        new_ext_key = "another-external-user-id-FKQP12345"
        self.add_user_to_course_program_team(new_user, add_to_team=False, external_user_key=new_ext_key)
        self.assert_user_not_on_team(new_user)

        with BytesIO() as mock_csv_file:
            with TextIOWrapper(mock_csv_file, write_through=True) as text_wrapper:
                # Create the fake csv file
                csv_writer = DictWriter(text_wrapper, fieldnames=self.header_fields)
                csv_writer.writeheader()
                # Add the new user to the team via CSV upload, identified by their external key
                csv_writer.writerow({'user': new_ext_key, 'mode': 'audit', self.teamset_id: self.team.name})
                # We need to seek to the beginning of the file so the csv import manager can read it
                mock_csv_file.seek(0)
                #After processing the file, the user should be on the team
                self.import_manager.set_team_membership_from_csv(mock_csv_file)

        self.assert_user_on_team(new_user)

    def test_lookup_team_membership_data(self):
        with self.assertNumQueries(3):
            # pylint: disable=protected-access
            data = csv._lookup_team_membership_data(self.course)
        self._assert_test_users_on_team(data)

    def test_get_csv(self):
        with StringIO() as read_buf:
            csv.load_team_membership_csv(self.course, read_buf)
            read_buf.seek(0)
            reader = DictReader(read_buf)
            team_memberships = list(reader)
        self._assert_test_users_on_team(team_memberships)

    def _assert_test_users_on_team(self, data):
        """
        Assert that the four test users should be listed as members of the team,
        and user_in_program should be identified by their external_user_key
        """
        self.assertEqual(len(data), 4)
        self.assertEqual(
            {user_row['user'] for user_row in data},
            {
                self.user_no_program.username,
                self.user_in_program_no_external_id.username,
                self.user_in_program_not_enrolled_through_program.username,
                self.external_user_key
            }
        )
        for user_row in data:
            self.assertEqual(len(user_row), 3)
            self.assertEqual(user_row['mode'], 'audit')
            self.assertEqual(user_row[self.teamset_id], self.team.name)
