"""
Acceptance tests for the Import and Export pages
"""
from abc import abstractmethod
from bok_choy.promise import EmptyPromise
from datetime import datetime

from .base_studio_test import StudioLibraryTest, StudioCourseTest
from ...fixtures.course import XBlockFixtureDesc
from ...pages.studio.import_export import ExportLibraryPage, ExportCoursePage, ImportLibraryPage, ImportCoursePage
from ...pages.studio.library import LibraryEditPage
from ...pages.studio.container import ContainerPage
from ...pages.studio.overview import CourseOutlinePage


# pylint: disable=no-member
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
        good_status, is_tarball_mimetype = self.export_page.download_tarball()
        self.assertTrue(good_status)
        self.assertTrue(is_tarball_mimetype)


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


class TestLibraryExport(ExportTestMixin, StudioLibraryTest):
    """
    Export tests for libraries.
    """
    def setUp(self):  # pylint: disable=arguments-differ
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


# pylint: disable=no-member
class BadExportMixin(object):
    """
    Test mixin for bad exports.
    """
    def test_bad_export(self):
        """
        Scenario: I should receive an error when attempting to export a broken course or library.
            Given that I have a course or library
            No error modal should be showing
            When I click the export button
            An error modal should be shown
            When I click the modal's action button
            I should arrive at the edit page for the broken component
        """
        # No error should be there to start.
        self.assertFalse(self.export_page.is_error_modal_showing())
        self.export_page.click_export()
        self.export_page.wait_for_error_modal()
        self.export_page.click_modal_button()
        EmptyPromise(
            lambda: self.edit_page.is_browser_on_page,
            'Arrived at component edit page',
            timeout=30
        )


class TestLibraryBadExport(BadExportMixin, StudioLibraryTest):
    """
    Verify exporting a bad library causes an error.
    """

    def setUp(self):
        """
        Set up the pages and start the tests.
        """
        super(TestLibraryBadExport, self).setUp()
        self.export_page = ExportLibraryPage(self.browser, self.library_key)
        self.edit_page = LibraryEditPage(self.browser, self.library_key)
        self.export_page.visit()

    def populate_library_fixture(self, library_fixture):
        """
        Create a library with a bad component.
        """
        library_fixture.add_children(
            XBlockFixtureDesc("problem", "Bad Problem", data='<'),
        )


class TestCourseBadExport(BadExportMixin, StudioCourseTest):
    """
    Verify exporting a bad course causes an error.
    """
    ready_method = 'wait_for_component_menu'

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestCourseBadExport, self).setUp()
        self.export_page = ExportCoursePage(
            self.browser,
            self.course_info['org'], self.course_info['number'], self.course_info['run'],
        )
        self.edit_page = ContainerPage(self.browser, self.unit.locator)
        self.export_page.visit()

    def populate_course_fixture(self, course_fixture):
        """
        Populate the course with a unit that has a bad problem.
        """
        self.unit = XBlockFixtureDesc('vertical', 'Unit')
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Main Section').add_children(
                XBlockFixtureDesc('sequential', 'Subsection').add_children(
                    self.unit.add_children(
                        XBlockFixtureDesc("problem", "Bad Problem", data='<')
                    )
                )
            )
        )


# pylint: disable=no-member
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

    def test_upload(self):
        """
        Scenario: I want to upload a course or library for import.
            Given that I have a library or course to import into
            And I have a valid .tar.gz file containing data to replace it with
            I can select the file and upload it
            And the page will give me confirmation that it uploaded successfully
        """
        self.import_page.upload_tarball(self.tarball_name)
        self.import_page.wait_for_upload()

    def test_import_timestamp(self):
        """
        Scenario: I perform a course / library import
            On import success, the page displays a UTC timestamp previously not visible
            And if I refresh the page, the timestamp is still displayed
        """
        self.assertFalse(self.import_page.is_timestamp_visible())
        self.import_page.upload_tarball(self.tarball_name)
        self.import_page.wait_for_upload()

        utc_now = datetime.utcnow()
        import_date, import_time = self.import_page.timestamp

        self.import_page.wait_for_timestamp_visible()
        self.assertEqual(utc_now.strftime('%m/%d/%Y'), import_date)
        self.assertEqual(utc_now.strftime('%H:%M'), import_time)

        self.import_page.visit()
        self.import_page.wait_for_tasks(completed=True)
        self.import_page.wait_for_timestamp_visible()

    def test_landing_url(self):
        """
        Scenario: When uploading a library or course, a link appears for me to view the changes.
            Given that I upload a library or course
            A button will appear that contains the URL to the library or course's main page
        """
        self.import_page.upload_tarball(self.tarball_name)
        self.assertEqual(self.import_page.finished_target_url(), self.landing_page.url)

    def test_bad_filename_error(self):
        """
        Scenario: I should be reprimanded for trying to upload something that isn't a .tar.gz file.
            Given that I select a file that is an .mp4 for upload
            An error message will appear
        """
        self.import_page.upload_tarball('funny_cat_video.mp4')
        self.import_page.wait_for_filename_error()

    def test_task_list(self):
        """
        Scenario: I should see feedback checkpoints when uploading a course or library
            Given that I am on an import page
            No task checkpoint list should be showing
            When I upload a valid tarball
            Each task in the checklist should be marked confirmed
            And the task list should be visible
        """
        # The task list shouldn't be visible to start.
        self.assertFalse(self.import_page.is_task_list_showing(), "Task list shown too early.")
        self.import_page.wait_for_tasks()
        self.import_page.upload_tarball(self.tarball_name)
        self.import_page.wait_for_tasks(completed=True)
        self.assertTrue(self.import_page.is_task_list_showing(), "Task list did not display.")

    def test_bad_import(self):
        """
        Scenario: I should see a failed checklist when uploading an invalid course or library
            Given that I am on an import page
            And I upload a tarball with a broken XML file
            The tasks should be confirmed up until the 'Updating' task
            And the 'Updating' task should be marked failed
            And the remaining tasks should not be marked as started
        """
        self.import_page.upload_tarball(self.bad_tarball_name)
        self.import_page.wait_for_tasks(fail_on='Updating')


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

    def test_course_updated(self):
        """
        Given that I visit an empty course before import
        I should not see a section named 'Section'
        When I visit the import page
        And I upload a course that has a section named 'Section'
        And I visit the course outline page again
        The section named 'Section' should now be available
        """
        self.landing_page.visit()
        # Should not exist yet.
        self.assertRaises(IndexError, self.landing_page.section, "Section")
        self.import_page.visit()
        self.import_page.upload_tarball(self.tarball_name)
        self.import_page.wait_for_upload()
        self.landing_page.visit()
        # There's a section named 'Section' in the tarball.
        self.landing_page.section("Section")

    def test_header(self):
        """
        Scenario: I should see the correct text when importing a course.
            Given that I have a course to import to
            When I visit the import page
            The correct header should be shown
        """
        self.assertEqual(self.import_page.header_text, 'Course Import')


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

    def test_library_updated(self):
        """
        Given that I visit an empty library
        No XBlocks should be shown
        When I visit the import page
        And I upload a library that contains three XBlocks
        And I visit the library page
        Three XBlocks should be shown
        """
        self.landing_page.visit()
        self.landing_page.wait_until_ready()
        # No items should be in the library to start.
        self.assertEqual(len(self.landing_page.xblocks), 0)
        self.import_page.visit()
        self.import_page.upload_tarball(self.tarball_name)
        self.import_page.wait_for_upload()
        self.landing_page.visit()
        self.landing_page.wait_until_ready()
        # There are three blocks in the tarball.
        self.assertEqual(len(self.landing_page.xblocks), 3)

    def test_header(self):
        """
        Scenario: I should see the correct text when importing a library.
            Given that I have a library to import to
            When I visit the import page
            The correct header should be shown
        """
        self.assertEqual(self.import_page.header_text, 'Library Import')
