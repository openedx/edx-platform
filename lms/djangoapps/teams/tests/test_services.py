# -*- coding: utf-8 -*-
"""
Tests for any Teams app services
"""
from __future__ import absolute_import, unicode_literals

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory

from lms.djangoapps.teams.services import TeamsService
from lms.djangoapps.teams.tests.factories import CourseTeamFactory


class TeamsServiceTests(ModuleStoreTestCase):
    """ Tests for the TeamsService """

    def setUp(self):
        super(TeamsServiceTests, self).setUp()
        self.course_run = CourseRunFactory.create()
        self.team = CourseTeamFactory.create(course_id=self.course_run['key'])
        self.service = TeamsService()

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
