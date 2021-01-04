# -*- coding: utf-8 -*-
"""
Tests for Python APIs of the Teams app
"""

from uuid import uuid4

import ddt
import mock
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.teams import api as teams_api
from lms.djangoapps.teams.models import CourseTeam
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from openedx.core.lib.teams_config import TeamsConfig, TeamsetType
from common.djangoapps.student.models import CourseEnrollment, AnonymousUserId
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

COURSE_KEY1 = CourseKey.from_string('edx/history/1')
COURSE_KEY2 = CourseKey.from_string('edx/math/1')
TOPIC1 = 'topic-1'
TOPIC2 = 'topic-2'
TOPIC3 = 'topic-3'

DISCUSSION_TOPIC_ID = uuid4().hex


@ddt.ddt
class PythonAPITests(SharedModuleStoreTestCase):
    """
    The set of tests for different API endpoints
    """
    @classmethod
    def setUpClass(cls):
        super(PythonAPITests, cls).setUpClass()
        cls.user1 = UserFactory.create(username='user1')
        cls.user2 = UserFactory.create(username='user2')
        cls.user3 = UserFactory.create(username='user3')
        cls.user4 = UserFactory.create(username='user4')

        topic_data = [
            (TOPIC1, TeamsetType.private_managed.value),
            (TOPIC2, TeamsetType.open.value),
            (TOPIC3, TeamsetType.public_managed.value)
        ]
        topics = [
            {
                'id': topic_id,
                'name': 'name-' + topic_id,
                'description': 'desc-' + topic_id,
                'type': teamset_type
            } for topic_id, teamset_type in topic_data
        ]
        teams_config_1 = TeamsConfig({'topics': [topics[0]]})
        teams_config_2 = TeamsConfig({'topics': [topics[1], topics[2]]})
        cls.course1 = CourseFactory(
            org=COURSE_KEY1.org,
            course=COURSE_KEY1.course,
            run=COURSE_KEY1.run,
            teams_configuration=teams_config_1,
        )
        cls.course2 = CourseFactory(
            org=COURSE_KEY2.org,
            course=COURSE_KEY2.course,
            run=COURSE_KEY2.run,
            teams_configuration=teams_config_2,
        )

        for user in (cls.user1, cls.user2, cls.user3, cls.user4):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY1)

        for user in (cls.user3, cls.user4):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY2)

        cls.team1 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            discussion_topic_id=DISCUSSION_TOPIC_ID,
            team_id='team1',
            topic_id=TOPIC1,
        )
        cls.team1a = CourseTeamFactory(  # Same topic / team set as team1
            course_id=COURSE_KEY1,
            team_id='team1a',
            topic_id=TOPIC1,
        )
        cls.team2 = CourseTeamFactory(course_id=COURSE_KEY2, team_id='team2', topic_id=TOPIC2)
        cls.team2a = CourseTeamFactory(  # Same topic / team set as team2
            course_id=COURSE_KEY2,
            team_id='team2a',
            topic_id=TOPIC2
        )
        cls.team3 = CourseTeamFactory(course_id=COURSE_KEY2, team_id='team3', topic_id=TOPIC3)

        cls.team1.add_user(cls.user1)
        cls.team1.add_user(cls.user2)
        cls.team2.add_user(cls.user3)

        cls.team1a.add_user(cls.user4)
        cls.team2a.add_user(cls.user4)

    def test_get_team_by_team_id_non_existence(self):
        self.assertIsNone(teams_api.get_team_by_team_id('DO_NOT_EXIST'))

    def test_get_team_by_team_id_exists(self):
        team = teams_api.get_team_by_team_id(self.team1.team_id)
        self.assertEqual(team, self.team1)

    def test_get_team_by_discussion_non_existence(self):
        self.assertIsNone(teams_api.get_team_by_discussion('DO_NOT_EXIST'))

    def test_get_team_by_discussion_exists(self):
        team = teams_api.get_team_by_discussion(DISCUSSION_TOPIC_ID)
        self.assertEqual(team, self.team1)

    def test_is_team_discussion_private_is_private(self):
        self.assertTrue(teams_api.is_team_discussion_private(self.team1))

    def test_is_team_discussion_private_is_public(self):
        self.assertFalse(teams_api.is_team_discussion_private(None))
        self.assertFalse(teams_api.is_team_discussion_private(self.team2))
        self.assertFalse(teams_api.is_team_discussion_private(self.team3))

    def test_is_instructor_managed_team(self):
        self.assertTrue(teams_api.is_instructor_managed_team(self.team1))
        self.assertFalse(teams_api.is_instructor_managed_team(self.team2))
        self.assertTrue(teams_api.is_instructor_managed_team(self.team3))

    def test_is_instructor_managed_topic(self):
        self.assertTrue(teams_api.is_instructor_managed_topic(COURSE_KEY1, TOPIC1))
        self.assertFalse(teams_api.is_instructor_managed_topic(COURSE_KEY2, TOPIC2))
        self.assertTrue(teams_api.is_instructor_managed_topic(COURSE_KEY2, TOPIC3))

    def test_user_is_a_team_member(self):
        self.assertTrue(teams_api.user_is_a_team_member(self.user1, self.team1))
        self.assertFalse(teams_api.user_is_a_team_member(self.user1, None))
        self.assertFalse(teams_api.user_is_a_team_member(self.user1, self.team2))

    def test_private_discussion_visible_by_user(self):
        self.assertTrue(teams_api.discussion_visible_by_user(DISCUSSION_TOPIC_ID, self.user1))
        self.assertTrue(teams_api.discussion_visible_by_user(DISCUSSION_TOPIC_ID, self.user2))
        # self.assertFalse(teams_api.discussion_visible_by_user(DISCUSSION_TOPIC_ID, self.user3))

    def test_public_discussion_visible_by_user(self):
        self.assertTrue(teams_api.discussion_visible_by_user(self.team2.discussion_topic_id, self.user1))
        self.assertTrue(teams_api.discussion_visible_by_user(self.team2.discussion_topic_id, self.user2))
        self.assertTrue(teams_api.discussion_visible_by_user('DO_NOT_EXISTS', self.user3))

    @ddt.unpack
    @ddt.data(
        (COURSE_KEY1, TOPIC1, ['team1', 'team1', None, 'team1a']),
        (COURSE_KEY1, TOPIC2, [None, None, None, None]),
        (COURSE_KEY2, TOPIC1, [None, None, None, None]),
        (COURSE_KEY2, TOPIC2, [None, None, 'team2', 'team2a']),
    )
    def test_get_team_for_user_course_topic(self, course_key, topic_id, expected_team_ids):
        user1_team = teams_api.get_team_for_user_course_topic(self.user1, str(course_key), topic_id)
        user2_team = teams_api.get_team_for_user_course_topic(self.user2, str(course_key), topic_id)
        user3_team = teams_api.get_team_for_user_course_topic(self.user3, str(course_key), topic_id)
        user4_team = teams_api.get_team_for_user_course_topic(self.user4, str(course_key), topic_id)

        self.assertEqual(user1_team.team_id if user1_team else None, expected_team_ids[0])
        self.assertEqual(user2_team.team_id if user2_team else None, expected_team_ids[1])
        self.assertEqual(user3_team.team_id if user3_team else None, expected_team_ids[2])
        self.assertEqual(user4_team.team_id if user4_team else None, expected_team_ids[3])

    @mock.patch('lms.djangoapps.teams.api.CourseTeam.objects')
    def test_get_team_multiple_teams(self, mocked_manager):
        """
        This is a test for a use case that is very unlikely to occur.
        Currently users cannot be in multiple teams in a course, but even after we allow multiple
        teams in a course then they should still be limited to one team per topic
        """
        mocked_manager.get.side_effect = CourseTeam.MultipleObjectsReturned()
        expected_result = "This is somehow the first team"
        mock_qs = mock.MagicMock()
        mock_qs.first.return_value = expected_result
        mocked_manager.filter.return_value = mock_qs
        result = teams_api.get_team_for_user_course_topic(self.user1, str(COURSE_KEY1), TOPIC1)
        self.assertEqual(result, expected_result)

    def test_get_team_course_not_found(self):
        team = teams_api.get_team_for_user_course_topic(self.user1, 'nonsense/garbage/nonexistant', 'topic')
        self.assertIsNone(team)

    def test_get_team_invalid_course(self):
        invalid_course_id = 'lol!()#^$&course'
        message = 'The supplied course id lol!()#^$&course is not valid'
        with self.assertRaisesMessage(ValueError, message):
            teams_api.get_team_for_user_course_topic(self.user1, invalid_course_id, 'who-cares')

    def test_anonymous_user_ids_for_team(self):
        """
        A learner should be able to get the anonymous user IDs of their team members
        """
        team_anonymous_user_ids = teams_api.anonymous_user_ids_for_team(self.user1, self.team1)
        self.assertTrue(AnonymousUserId.objects.get(user=self.user1, course_id=self.team1.course_id))
        self.assertEqual(len(self.team1.users.all()), len(team_anonymous_user_ids))

    def test_anonymous_user_ids_for_team_not_on_team(self):
        """
        A learner should not be able to get IDs from members of a team they are not a member of
        """
        self.assertRaises(Exception, teams_api.anonymous_user_ids_for_team, self.user1, self.team2)

    def test_anonymous_user_ids_for_team_bad_user_or_team(self):
        """
        An exception should be thrown when a bad user or team are passed to the endpoint
        """
        self.assertRaises(Exception, teams_api.anonymous_user_ids_for_team, None, self.team1)

    def test_anonymous_user_ids_for_team_staff(self):
        """
        Course staff should be able to get anonymous IDs for teams in their course
        """
        user_staff = UserFactory.create(username='user_staff')
        CourseEnrollmentFactory.create(user=user_staff, course_id=COURSE_KEY1)
        CourseStaffRole(COURSE_KEY1).add_users(user_staff)

        team_anonymous_user_ids = teams_api.anonymous_user_ids_for_team(user_staff, self.team1)
        self.assertEqual(len(self.team1.users.all()), len(team_anonymous_user_ids))


@ddt.ddt
class TeamAccessTests(SharedModuleStoreTestCase):
    """
    The set of tests for API endpoints related to access of a team based on the users
    """
    @classmethod
    def setUpClass(cls):
        super(TeamAccessTests, cls).setUpClass()
        cls.user_audit = UserFactory.create(username='user_audit')
        cls.user_staff = UserFactory.create(username='user_staff')
        cls.user_masters = UserFactory.create(username='user_masters')
        cls.user_unenrolled = UserFactory.create(username='user_unenrolled')
        cls.users = {
            'user_audit': cls.user_audit,
            'user_staff': cls.user_staff,
            'user_masters': cls.user_masters,
            'user_unenrolled': cls.user_unenrolled,
        }

        cls.topic_id = 'RANDOM TOPIC'
        cls.course_1 = CourseFactory.create(
            teams_configuration=TeamsConfig({
                'team_sets': [{'id': cls.topic_id, 'name': cls.topic_id, 'description': cls.topic_id}]
            }),
            org=COURSE_KEY1.org,
            course=COURSE_KEY1.course,
            run=COURSE_KEY1.run
        )

        for user in (cls.user_audit, cls.user_staff):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY1)
        CourseEnrollmentFactory.create(user=cls.user_masters, course_id=COURSE_KEY1, mode=CourseMode.MASTERS)

        CourseStaffRole(COURSE_KEY1).add_users(cls.user_staff)

        cls.team_unprotected_1 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            topic_id=cls.topic_id,
            team_id='team_unprotected_1'
        )
        cls.team_unprotected_2 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            topic_id=cls.topic_id,
            team_id='team_unprotected_2'
        )
        cls.team_unprotected_3 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            topic_id=cls.topic_id,
            team_id='team_unprotected_3'
        )
        cls.team_protected_1 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            team_id='team_protected_1',
            topic_id=cls.topic_id,
            organization_protected=True
        )
        cls.team_protected_2 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            team_id='team_protected_2',
            topic_id=cls.topic_id,
            organization_protected=True
        )

    @ddt.data(
        ('user_audit', True),
        ('user_masters', True),
        ('user_staff', True),
        ('user_unenrolled', False),
    )
    @ddt.unpack
    def test_has_team_api_access(self, username, expected_have_access):
        user = self.users[username]
        self.assertEqual(
            expected_have_access,
            teams_api.has_team_api_access(user, COURSE_KEY1)
        )

    @ddt.data(
        ('user_audit', teams_api.OrganizationProtectionStatus.unprotected),
        ('user_masters', teams_api.OrganizationProtectionStatus.protected),
        ('user_staff', teams_api.OrganizationProtectionStatus.protection_exempt),
        ('user_unenrolled', None),
    )
    @ddt.unpack
    def test_user_organization_protection_status(self, username, expected_protection_status):
        user = self.users[username]
        try:
            self.assertEqual(
                expected_protection_status,
                teams_api.user_organization_protection_status(user, COURSE_KEY1)
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, COURSE_KEY1))

    @ddt.data(
        ('user_audit', True),
        ('user_masters', False),
        ('user_staff', True),
        ('user_unenrolled', False),
    )
    @ddt.unpack
    def test_has_specific_team_access_unprotected_team(self, username, expected_return):
        user = self.users[username]
        try:
            self.assertEqual(
                expected_return,
                teams_api.has_specific_team_access(user, self.team_unprotected_1)
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, self.team_unprotected_1.course_id))

    @ddt.data(
        ('user_audit', False),
        ('user_masters', True),
        ('user_staff', True),
        ('user_unenrolled', False),
    )
    @ddt.unpack
    def test_has_specific_team_access_protected_team(self, username, expected_return):
        user = self.users[username]
        try:
            self.assertEqual(
                expected_return,
                teams_api.has_specific_team_access(user, self.team_protected_1)
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, self.team_protected_1.course_id))

    @ddt.data(
        ('user_audit', 3),
        ('user_masters', 2),
        ('user_staff', 5),
        ('user_unenrolled', 3),
    )
    @ddt.unpack
    def test_team_counter_get_teams_accessible_by_user(self, username, expected_count):
        user = self.users[username]
        try:
            organization_protection_status = teams_api.user_organization_protection_status(
                user,
                COURSE_KEY1
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, COURSE_KEY1))
            return
        teams_query_set = teams_api.get_teams_accessible_by_user(
            user,
            [self.topic_id],
            COURSE_KEY1,
            organization_protection_status
        )
        self.assertEqual(
            expected_count,
            teams_query_set.count()
        )

    @ddt.data(
        ('user_audit', 3),
        ('user_masters', 2),
        ('user_staff', 5),
        ('user_unenrolled', 3),
    )
    @ddt.unpack
    def test_team_counter_add_team_count(self, username, expected_team_count):
        user = self.users[username]
        try:
            organization_protection_status = teams_api.user_organization_protection_status(
                user,
                COURSE_KEY1
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, COURSE_KEY1))
            return
        topic = {
            'id': self.topic_id
        }
        teams_api.add_team_count(
            user,
            [topic],
            COURSE_KEY1,
            organization_protection_status
        )
        self.assertEqual(
            expected_team_count,
            topic.get('team_count')
        )
