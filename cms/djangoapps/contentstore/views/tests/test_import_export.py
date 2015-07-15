"""
Unit tests for course import and export
"""
import logging

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url

log = logging.getLogger(__name__)


class ImportExportTestCase(CourseTestCase):
    """
    Tests for export_handler.
    """
    def setUp(self):
        """
        Sets up the test course.
        """
        super(ImportExportTestCase, self).setUp()
        self.import_url = reverse_course_url('import_handler', self.course.id)
        self.export_url = reverse_course_url('export_handler', self.course.id)

    def test_import_html(self):
        """
        Get the HTML for the import page.
        """
        resp = self.client.get_html(self.import_url)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Replace Your Course Content")

    def test_export_html(self):
        """
        Get the HTML for the export page.
        """
        resp = self.client.get_html(self.export_url)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Export My Course Content")

    def test_permission_denied(self):
        """
        Test if the views handle unauthorized requests properly
        """
        # pylint: disable=unused-variable
        client, user = self.create_non_staff_authed_user_client(
            authenticate=True
        )
        for url in [self.import_url, self.export_url]:
            resp = client.get(url)
            self.assertEquals(resp.status_code, 403)
