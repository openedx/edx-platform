"""
Tests for `backfill_course_outlines` Studio (cms) management command.
"""
from unittest import mock

from django.core.management import call_command

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.tabs import InvalidTabsException


class BackfillCourseTabsTest(ModuleStoreTestCase):
    """
    Test `backfill_course_tabs`
    """
    @mock.patch('cms.djangoapps.contentstore.management.commands.backfill_course_tabs.logger')
    def test_no_tabs_to_add(self, mock_logger):
        """ Calls command with a course already having all default tabs. """
        course = CourseFactory()
        tabs_before = course.tabs

        call_command('backfill_course_tabs')

        course = self.store.get_course(course.id)
        tabs_after = course.tabs
        assert tabs_before == tabs_after
        # Ensure update_item was never called since there were no changes necessary
        # Using logger as a proxy. First time is number of courses read.
        assert mock_logger.info.call_count == 1

    @mock.patch('cms.djangoapps.contentstore.management.commands.backfill_course_tabs.logger')
    def test_add_one_tab(self, mock_logger):
        """
        Calls command on a course with existing tabs, but not all default ones.
        """
        course = CourseFactory()
        course.tabs = [tab for tab in course.tabs if tab.type != 'dates']
        self.update_course(course, ModuleStoreEnum.UserID.test)
        assert len(course.tabs) == 6
        assert 'dates' not in {tab.type for tab in course.tabs}

        call_command('backfill_course_tabs')

        course = self.store.get_course(course.id)
        assert len(course.tabs) == 7
        assert 'dates' in {tab.type for tab in course.tabs}
        mock_logger.info.assert_called_with(f'Updating tabs for {course.id}.')
        assert mock_logger.info.call_count == 2

        call_command('backfill_course_tabs')
        # Ensure rerunning the command does not require another update on the course.
        # Goes up by one from the courses read log.
        assert mock_logger.info.call_count == 3

    @mock.patch('cms.djangoapps.contentstore.management.commands.backfill_course_tabs.logger')
    def test_multiple_courses_one_update(self, mock_logger):
        """
        Calls command on multiple courses, some that already have all their tabs, and some that need updates.
        """
        CourseFactory()
        CourseFactory()
        CourseFactory()
        course = CourseFactory()
        course.tabs = [tab for tab in course.tabs if tab.type in ('course_info', 'courseware')]
        self.update_course(course, ModuleStoreEnum.UserID.test)
        assert len(course.tabs) == 2
        assert 'dates' not in {tab.type for tab in course.tabs}
        assert 'progress' not in {tab.type for tab in course.tabs}

        call_command('backfill_course_tabs')

        course = self.store.get_course(course.id)
        assert len(course.tabs) == 7
        assert 'dates' in {tab.type for tab in course.tabs}
        assert 'progress' in {tab.type for tab in course.tabs}
        mock_logger.info.assert_any_call('4 courses read from modulestore.')
        mock_logger.info.assert_called_with(f'Updating tabs for {course.id}.')
        assert mock_logger.info.call_count == 2

        call_command('backfill_course_tabs')
        # Ensure rerunning the command does not require another update on the course.
        # Goes up by one from the courses read log.
        assert mock_logger.info.call_count == 3

    @mock.patch('cms.djangoapps.contentstore.management.commands.backfill_course_tabs.logger')
    def test_multiple_courses_all_updated(self, mock_logger):
        """
        Calls command on multiple courses where all of them need updates.
        """
        course_1 = CourseFactory()
        course_1.tabs = [tab for tab in course_1.tabs if tab.type != 'dates']
        self.update_course(course_1, ModuleStoreEnum.UserID.test)
        course_2 = CourseFactory()
        course_2.tabs = [tab for tab in course_2.tabs if tab.type != 'progress']
        self.update_course(course_2, ModuleStoreEnum.UserID.test)
        assert len(course_1.tabs) == 6
        assert len(course_2.tabs) == 6
        assert 'dates' not in {tab.type for tab in course_1.tabs}
        assert 'progress' not in {tab.type for tab in course_2.tabs}

        call_command('backfill_course_tabs')

        course_1 = self.store.get_course(course_1.id)
        course_2 = self.store.get_course(course_2.id)
        assert len(course_1.tabs) == 7
        assert len(course_2.tabs) == 7
        assert 'dates' in {tab.type for tab in course_1.tabs}
        assert 'progress' in {tab.type for tab in course_2.tabs}
        mock_logger.info.assert_any_call('2 courses read from modulestore.')
        mock_logger.info.assert_any_call(f'Updating tabs for {course_1.id}.')
        mock_logger.info.assert_any_call(f'Updating tabs for {course_2.id}.')
        assert mock_logger.info.call_count == 3

        call_command('backfill_course_tabs')
        # Ensure rerunning the command does not require another update on any courses.
        # Goes up by one from the courses read log.
        assert mock_logger.info.call_count == 4

    @mock.patch('cms.djangoapps.contentstore.management.commands.backfill_course_tabs.logger')
    def test_command_fails_if_error_raised(self, mock_logger):
        CourseFactory()
        with mock.patch(
            'cms.djangoapps.contentstore.management.commands.backfill_course_tabs.CourseTabList.initialize_default',
            side_effect=InvalidTabsException
        ):
            with self.assertRaises(InvalidTabsException):
                call_command('backfill_course_tabs')
        # Never calls the update, but does make it through grabbing the courses
        mock_logger.info.assert_called_once_with('1 courses read from modulestore.')
