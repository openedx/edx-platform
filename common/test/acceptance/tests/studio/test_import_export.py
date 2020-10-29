"""
Acceptance tests for the Import and Export pages
"""


from abc import abstractmethod
from datetime import datetime

from common.test.acceptance.pages.studio.import_export import (
    ExportCoursePage,
    ExportLibraryPage,
    ImportCoursePage,
    ImportLibraryPage
)
from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest, StudioLibraryTest
from openedx.core.lib.tests import attr


class ExportTestMixin(object):
    """
    Tests to run both for course and library export pages.
    """
    def test_export(self):
        """
        Scenario: I am able to export a course or library
            Given that I have a course or library
            And I click the download button
            The download will succeed
            And the file will be of the right MIME type.
        """
        self.export_page.wait_for_export_click_handler()
        self.export_page.click_export()
        self.export_page.wait_for_export()
        good_status, is_tarball_mimetype = self.export_page.download_tarball()
        self.assertTrue(good_status)
        self.assertTrue(is_tarball_mimetype)

    def test_export_timestamp(self):
        """
        Scenario: I perform a course / library export
            On export success, the page displays a UTC timestamp previously not visible
            And if I refresh the page, the timestamp is still displayed
        """
        self.assertFalse(self.export_page.is_timestamp_visible())

        # Get the time when the export has started.
        # export_page timestamp is in (MM/DD/YYYY at HH:mm) so replacing (second, microsecond) to
        # keep the comparison consistent
        export_start_time = datetime.utcnow().replace(microsecond=0, second=0)
        self.export_page.wait_for_export_click_handler()
        self.export_page.click_export()
        self.export_page.wait_for_export()

        # Get the time when the export has finished.
        # export_page timestamp is in (MM/DD/YYYY at HH:mm) so replacing (second, microsecond) to
        # keep the comparison consistent
        export_finish_time = datetime.utcnow().replace(microsecond=0, second=0)

        export_timestamp = self.export_page.parsed_timestamp
        self.export_page.wait_for_timestamp_visible()

        # Verify that 'export_timestamp' is between start and finish upload time
        self.assertLessEqual(
            export_start_time,
            export_timestamp,
            "Course export timestamp should be export_start_time <= export_timestamp <= export_end_time"
        )
        self.assertGreaterEqual(
            export_finish_time,
            export_timestamp,
            "Course export timestamp should be export_start_time <= export_timestamp <= export_end_time"
        )

        self.export_page.visit()
        self.export_page.wait_for_tasks(completed=True)
        self.export_page.wait_for_timestamp_visible()

    def test_task_list(self):
        """
        Scenario: I should see feedback checkpoints when exporting a course or library
            Given that I am on an export page
            No task checkpoint list should be showing
            When I export the course or library
            Each task in the checklist should be marked confirmed
            And the task list should be visible
        """
        # The task list shouldn't be visible to start.
        self.assertFalse(self.export_page.is_task_list_showing(), "Task list shown too early.")
        self.export_page.wait_for_tasks()
        self.export_page.wait_for_export_click_handler()
        self.export_page.click_export()
        self.export_page.wait_for_tasks(completed=True)
        self.assertTrue(self.export_page.is_task_list_showing(), "Task list did not display.")


@attr(shard=7)
class TestCourseExport(ExportTestMixin, StudioCourseTest):
    """
    Export tests for courses.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(TestCourseExport, self).setUp()
        self.export_page = ExportCoursePage(
            self.browser,
            self.course_info['org'], self.course_info['number'], self.course_info['run'],
        )
        self.export_page.visit()

    def test_header(self):
        """
        Scenario: I should see the correct text when exporting a course.
            Given that I have a course to export from
            When I visit the export page
            The correct header should be shown
        """
        self.assertEqual(self.export_page.header_text, 'Course Export')


@attr(shard=7)
class TestLibraryExport(ExportTestMixin, StudioLibraryTest):
    """
    Export tests for libraries.
    """
    def setUp(self):
        """
        Ensure a library exists and navigate to the library edit page.
        """
        super(TestLibraryExport, self).setUp()
        self.export_page = ExportLibraryPage(self.browser, self.library_key)
        self.export_page.visit()

    def test_header(self):
        """
        Scenario: I should see the correct text when exporting a library.
            Given that I have a library to export from
            When I visit the export page
            The correct header should be shown
        """
        self.assertEqual(self.export_page.header_text, 'Library Export')


@attr(shard=7)
class ImportTestMixin(object):
    """
    Tests to run for both course and library import pages.
    """
    def setUp(self):
        super(ImportTestMixin, self).setUp()
        self.import_page = self.import_page_class(*self.page_args())
        self.landing_page = self.landing_page_class(*self.page_args())
        self.import_page.visit()

    @abstractmethod
    def page_args(self):
        """
        Generates the args for initializing a page object.
        """
        return []


@attr(shard=7)
class TestEntranceExamCourseImport(ImportTestMixin, StudioCourseTest):
    """
    Tests the Course import page
    """
    tarball_name = 'entrance_exam_course.2015.tar.gz'
    bad_tarball_name = 'bad_course.tar.gz'
    import_page_class = ImportCoursePage
    landing_page_class = CourseOutlinePage

    def page_args(self):
        return [self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']]


@attr(shard=7)
class TestCourseImport(ImportTestMixin, StudioCourseTest):
    """
    Tests the Course import page
    """
    tarball_name = '2015.lzdwNM.tar.gz'
    bad_tarball_name = 'bad_course.tar.gz'
    import_page_class = ImportCoursePage
    landing_page_class = CourseOutlinePage

    def page_args(self):
        return [self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']]

    def test_header(self):
        """
        Scenario: I should see the correct text when importing a course.
            Given that I have a course to import to
            When I visit the import page
            The correct header should be shown
        """
        self.assertEqual(self.import_page.header_text, 'Course Import')


@attr(shard=7)
class TestLibraryImport(ImportTestMixin, StudioLibraryTest):
    """
    Tests the Library import page
    """
    tarball_name = 'library.HhJfPD.tar.gz'
    bad_tarball_name = 'bad_library.tar.gz'
    import_page_class = ImportLibraryPage
    landing_page_class = LibraryEditPage

    def page_args(self):
        return [self.browser, self.library_key]

    def test_header(self):
        """
        Scenario: I should see the correct text when importing a library.
            Given that I have a library to import to
            When I visit the import page
            The correct header should be shown
        """
        self.assertEqual(self.import_page.header_text, 'Library Import')
