# -*- coding: utf-8 -*-
"""
Tests for Python APIs of the Teams app
"""
from __future__ import absolute_import, unicode_literals

import unittest
from uuid import uuid4

import ddt
from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
from lms.djangoapps.teams import api as teams_api
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from student.models import CourseEnrollment
from student.roles import CourseStaffRole
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

COURSE_KEY1 = CourseKey.from_string('edx/history/1')
COURSE_KEY2 = CourseKey.from_string('edx/history/2')

DISCUSSION_TOPIC_ID = uuid4().hex


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

        for user in (cls.user1, cls.user2, cls.user3):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY1)

        CourseEnrollmentFactory.create(user=cls.user3, course_id=COURSE_KEY2)

        cls.team1 = CourseTeamFactory(
            course_id=COURSE_KEY1,
            discussion_topic_id=DISCUSSION_TOPIC_ID,
            team_id='team1'
        )
        cls.team2 = CourseTeamFactory(course_id=COURSE_KEY2, team_id='team2')

        cls.team1.add_user(cls.user1)
        cls.team1.add_user(cls.user2)
        cls.team2.add_user(cls.user3)

    def test_get_team_by_discussion_non_existence(self):
        self.assertIsNone(teams_api.get_team_by_discussion('DO_NOT_EXIST'))

    def test_get_team_by_discussion_exists(self):
        team = teams_api.get_team_by_discussion(DISCUSSION_TOPIC_ID)
        self.assertEqual(team, self.team1)

    @unittest.skip("This functionality is not yet implemented")
    def test_is_team_discussion_private_is_private(self):
        self.assertTrue(teams_api.is_team_discussion_private(self.team1))

    def test_is_team_discussion_private_is_public(self):
        self.assertFalse(teams_api.is_team_discussion_private(None))
        self.assertFalse(teams_api.is_team_discussion_private(self.team2))

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

        for user in (cls.user_audit, cls.user_staff):
            CourseEnrollmentFactory.create(user=user, course_id=COURSE_KEY1)
        CourseEnrollmentFactory.create(user=cls.user_masters, course_id=COURSE_KEY1, mode=CourseMode.MASTERS)

        CourseStaffRole(COURSE_KEY1).add_users(cls.user_staff)

        cls.topic_id = 'RANDOM TOPIC'
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
    def test_team_counter_get_team_count_query_set(self, username, expected_count):
        user = self.users[username]
        try:
            organization_protection_status = teams_api.user_organization_protection_status(
                user,
                COURSE_KEY1
            )
        except ValueError:
            self.assertFalse(CourseEnrollment.is_enrolled(user, COURSE_KEY1))
            return
        teams_query_set = teams_api.get_team_count_query_set(
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
            [topic],
            COURSE_KEY1,
            organization_protection_status
        )
        self.assertEqual(
            expected_team_count,
            topic.get('team_count')
        )
