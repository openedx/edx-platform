# -*- coding: utf-8 -*-
"""
Tests for Python APIs of the Teams app
"""
from __future__ import absolute_import

from uuid import uuid4
import unittest

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.teams import api as teams_api
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
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
