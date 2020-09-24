"""
Unit Tests for Django management command to archive course community on nodeBB.
"""
from __future__ import unicode_literals

from datetime import datetime, timedelta

import mock
import pytz
from django.core.management import call_command

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class ArchivePastCoursesCommunities(ModuleStoreTestCase):
    """
    Tests for `archive_past_courses_communities` command.
    """

    def setUp(self):
        """
        This function is responsible for creating courses for every test and mocking the function for tests.
        :return:
        """
        super(ArchivePastCoursesCommunities, self).setUp()

        self.course_1 = CourseFactory.create(display_name='test course 1', run='Testing_course_1')
        self.course_2 = CourseFactory.create(display_name='test course 2', run='Testing_course_2')
        self.course_1.end = datetime.now(pytz.UTC) - timedelta(hours=2)
        self.course_2.end = datetime.now(pytz.UTC) - timedelta(hours=2)

        self.get_visible_courses_patcher = \
            mock.patch('philu_commands.management.commands.archive_past_courses_communities.get_visible_courses')
        self.archive_course_community_patcher = \
            mock.patch('philu_commands.management.commands.archive_past_courses_communities.archive_course_community')

        self.mock_archive_course_community = self.archive_course_community_patcher.start()
        self.mock_get_visible_courses = self.get_visible_courses_patcher.start()

    def test_archive_command_with_past_courses(self):
        """
        Test 'archive_past_courses_communities' command by passing completed courses with end time of 2 hours ago.
        """
        self.mock_get_visible_courses.return_value = [self.course_1, self.course_2]
        call_command('archive_past_courses_communities')

        expected_calls = [
            mock.call(self.course_1.id),
            mock.call(self.course_2.id),
        ]

        self.assertEqual(2, self.mock_archive_course_community.call_count)
        self.mock_archive_course_community.assert_has_calls(expected_calls)

    def test_archive_command_without_courses(self):
        """
        Test 'archive_past_courses_communities' command by passing empty courses.
        """
        self.mock_get_visible_courses.return_value = []
        call_command('archive_past_courses_communities')

        self.assertEqual(0, self.mock_archive_course_community.call_count)

    def test_archive_command_with_no_past_courses(self):
        """
        Test 'archive_past_courses_communities' command by passing no past courses.
        """
        self.course_1.end = None
        self.course_2.end = None
        self.mock_get_visible_courses.return_value = [self.course_1, self.course_2]
        call_command('archive_past_courses_communities')

        self.assertEqual(0, self.mock_archive_course_community.call_count)

    def test_archive_command_with_one_past_courses(self):
        """
        Test 'archive_past_courses_communities' command by passing one past course.
        """
        self.course_2.end = None

        self.mock_get_visible_courses.return_value = [self.course_1, self.course_2]
        call_command('archive_past_courses_communities')

        expected_call = [
            mock.call(self.course_1.id),
        ]
        self.assertEqual(1, self.mock_archive_course_community.call_count)
        self.mock_archive_course_community.assert_has_calls(expected_call)

    def tearDown(self):
        """
        This function is responsible for cleaning the patchers.
        :return:
        """
        super(ArchivePastCoursesCommunities, self).tearDown()
        self.addCleanup(self.archive_course_community_patcher.stop)
        self.addCleanup(self.get_visible_courses_patcher.stop)
