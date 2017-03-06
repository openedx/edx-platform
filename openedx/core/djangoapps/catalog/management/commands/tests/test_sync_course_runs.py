"""
Tests for the sync course runs management command.
"""
import ddt
import mock

from django.core.management import call_command

from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

COMMAND_MODULE = 'openedx.core.djangoapps.catalog.management.commands.sync_course_runs'


@ddt.ddt
@mock.patch(COMMAND_MODULE + '.get_course_runs')
class TestSyncCourseRunsCommand(ModuleStoreTestCase):
    """
    Test for the sync course runs management command.
    """
    def setUp(self):
        super(TestSyncCourseRunsCommand, self).setUp()
        # create mongo course
        self.course = CourseFactory.create()
        # load this course into course overview
        CourseOverview.get_from_id(self.course.id)
        # create a catalog course run with the same course id.
        self.catalog_course_run = CourseRunFactory(
            key=unicode(self.course.id),
            marketing_url='test_marketing_url'
        )

    def get_course_overview_marketing_url(self, course_id):
        """
        Get course overview marketing url.
        """
        return CourseOverview.objects.get(id=course_id).marketing_url

    def test_marketing_url_on_sync(self, mock_catalog_course_runs):
        """
        Verify the updated marketing url on execution of the management command.
        """
        mock_catalog_course_runs.return_value = [self.catalog_course_run]
        earlier_marketing_url = self.get_course_overview_marketing_url(self.course.id)

        call_command('sync_course_runs')
        updated_marketing_url = self.get_course_overview_marketing_url(self.course.id)
        # Assert that the Marketing URL has changed.
        self.assertNotEqual(earlier_marketing_url, updated_marketing_url)
        self.assertEqual(updated_marketing_url, 'test_marketing_url')

    @mock.patch(COMMAND_MODULE + '.log.info')
    def test_course_overview_does_not_exist(self, mock_log_info, mock_catalog_course_runs):
        """
        Verify no error in case if a course run is not found in course overview.
        """
        nonexistent_course_run = CourseRunFactory()
        mock_catalog_course_runs.return_value = [self.catalog_course_run, nonexistent_course_run]

        call_command('sync_course_runs')

        mock_log_info.assert_any_call(
            '[sync_course_runs] course overview record not found for course run: %s',
            nonexistent_course_run['key'],
        )
        updated_marketing_url = self.get_course_overview_marketing_url(self.course.id)
        self.assertEqual(updated_marketing_url, 'test_marketing_url')

    @mock.patch(COMMAND_MODULE + '.log.info')
    def test_starting_and_ending_logs(self, mock_log_info, mock_catalog_course_runs):
        """
        Verify logging at start and end of the command.
        """
        mock_catalog_course_runs.return_value = [self.catalog_course_run, CourseRunFactory(), CourseRunFactory()]

        call_command('sync_course_runs')
        # Assert the logs at the start of the command.
        mock_log_info.assert_any_call('[sync_course_runs] Fetching course runs from catalog service.')
        # Assert the log metrics at it's completion.
        mock_log_info.assert_any_call(
            ('[sync_course_runs] course runs retrieved: %d, course runs found in course overview: %d,'
             ' course runs not found in course overview: %d, course overviews metadata updated: %d,'),
            3,
            1,
            2,
            1,
        )
