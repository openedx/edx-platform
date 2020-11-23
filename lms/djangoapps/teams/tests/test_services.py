# -*- coding: utf-8 -*-
"""
Tests for any Teams app services
"""


from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory

from lms.djangoapps.teams.services import TeamsService
from lms.djangoapps.teams.tests.factories import CourseTeamFactory


class TeamsServiceTests(ModuleStoreTestCase):
    """ Tests for the TeamsService """

    def setUp(self):
        super(TeamsServiceTests, self).setUp()
        self.course_run = CourseRunFactory.create()
        self.course_key = self.course_run['key']
        self.team = CourseTeamFactory.create(course_id=self.course_key)
        self.service = TeamsService()
        self.user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course_key)
        self.team.add_user(self.user)

    def test_get_team_by_team_id(self):
        team = self.service.get_team_by_team_id('NONEXISTANCE')
        self.assertIsNone(team)

        team = self.service.get_team_by_team_id(self.team.team_id)
        self.assertEqual(team, self.team)

    def test_get_team(self):
        user_team = self.service.get_team(self.user, self.course_key, self.team.topic_id)
        self.assertEqual(user_team, self.team)

        user2 = UserFactory.create()
        user2_team = self.service.get_team(user2, self.course_key, self.team.topic_id)
        self.assertIsNone(user2_team)

    def test_get_team_detail_url(self):
        # edx.org/courses/blah/teams/#teams/topic_id/team_id
        team_detail_url = self.service.get_team_detail_url(self.team)
        split_url = team_detail_url.split('/')
        self.assertEqual(
            split_url[1:],
            [
                'courses',
                str(self.course_run['key']),
                'teams',
                '#teams',
                self.team.topic_id,
                self.team.team_id,
            ]
        )
