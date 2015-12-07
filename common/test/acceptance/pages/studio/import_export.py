"""
Import/Export pages.
"""
import time
from datetime import datetime

from bok_choy.promise import EmptyPromise
import os
import re
import requests

from ..common.utils import click_css

from .library import LibraryPage
from .course_page import CoursePage
from . import BASE_URL


class TemplateCheckMixin(object):
    """
    Mixin for verifying that a template is loading the correct text.
    """
    @property
    def header_text(self):
        """
        Get the header text of the page.
        """
        # There are prefixes like 'Tools' and '>', but the text itself is not in a span.
        return self.q(css='h1.page-header')[0].text.split('\n')[-1]


class ExportMixin(object):
    """
    Export page Mixin.
    """

    url_path = "export"

    def is_browser_on_page(self):
        """
        Verify this is the export page
        """
        return self.q(css='body.view-export').present

    def _get_tarball(self, url):
        """
        Download tarball at `url`
        """
        kwargs = dict()
        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)

        return response.status_code == 200, response.headers

    def download_tarball(self):
        """
        Downloads the course or library in tarball form.
        """
        tarball_url = self.q(css='a.action-export').attrs('href')[0]
        good_status, headers = self._get_tarball(tarball_url)
        return good_status, headers['content-type'] == 'application/x-tgz'

    def click_export(self):
        """
        Click the export button. Should only be used if expected to fail, as
        otherwise a browser dialog for saving the file will be presented.
        """
        self.q(css='a.action-export').click()

    def is_error_modal_showing(self):
        """
        Indicates whether or not the error modal is showing.
        """
        return self.q(css='.prompt.error').visible

    def click_modal_button(self):
        """
        Click the button on the modal dialog that appears when there's a problem.
        """
        self.q(css='.prompt.error .action-primary').click()

    def wait_for_error_modal(self):
        """
        If an import or export has an error, an error modal will be shown.
        """
        EmptyPromise(self.is_error_modal_showing, 'Error Modal Displayed', timeout=30).fulfill()


class LibraryLoader(object):
    """
    URL loading mixing for Library import/export
    """
    @property
    def url(self):
        """
        This pattern isn't followed universally by library URLs,
        but is used for import/export.
        """
        # pylint: disable=no-member
        return "/".join([BASE_URL, self.url_path, unicode(self.locator)])


class ExportCoursePage(ExportMixin, TemplateCheckMixin, CoursePage):
    """
    Export page for Courses
    """


class ExportLibraryPage(ExportMixin, TemplateCheckMixin, LibraryLoader, LibraryPage):
    """
    Export page for Libraries
    """


class ImportMixin(object):
    """
    Import page mixin
    """

    url_path = "import"

    @property
    def timestamp(self):
        """
        The timestamp is displayed on the page as "(MM/DD/YYYY at HH:mm)"
        It parses the timestamp and returns a (date, time) tuple
        """
        string = self.q(css='.item-progresspoint-success-date').text[0]

        return re.match(r'\(([^ ]+).+?(\d{2}:\d{2})', string).groups()

    @property
    def parsed_timestamp(self):
        """
        Return python datetime object from the parsed timestamp tuple (date, time)
        """
        timestamp = "{0} {1}".format(*self.timestamp)
        formatted_timestamp = time.strptime(timestamp, "%m/%d/%Y %H:%M")
        return datetime.fromtimestamp(time.mktime(formatted_timestamp))

    def is_browser_on_page(self):
        """
        Verify this is the export page
        """
        return self.q(css='.choose-file-button').present

    @staticmethod
    def file_path(filename):
        """
        Construct file path to be uploaded from the data upload folder.

        Arguments:
            filename (str): asset filename

        """
        # Should grab common point between this page module and the data folder.
        return os.sep.join(__file__.split(os.sep)[:-4]) + '/data/imports/' + filename

    def _wait_for_button(self):
        """
        Wait for the upload button to appear.
        """
        return EmptyPromise(
            lambda: self.q(css='#replace-courselike-button')[0],
            "Upload button appears",
            timeout=30
        ).fulfill()

    def upload_tarball(self, tarball_filename):
        """
        Upload a tarball to be imported.
        """
        asset_file_path = self.file_path(tarball_filename)
        # Make the upload elements visible to the WebDriver.
        self.browser.execute_script('$(".file-name-block").show();$(".file-input").show()')
        self.q(css='input[type="file"]')[0].send_keys(asset_file_path)
        self._wait_for_button()
        click_css(self, '.submit-button', require_notification=False)

    def is_upload_finished(self):
        """
        Checks if the 'view updated' button is showing.
        """
        return self.q(css='#view-updated-button').visible

    @staticmethod
    def _task_properties(completed):
        """
        Outputs the CSS class and promise description for task states based on completion.
        """
        if completed:
            return 'is-complete', "'{}' is marked complete"
        else:
            return 'is-not-started', "'{}' is in not-yet-started status"

    def wait_for_tasks(self, completed=False, fail_on=None):
        """
        Wait for all of the items in the task list to be set to the correct state.
        """
        classes = {
            'Uploading': 'item-progresspoint-upload',
            'Unpacking': 'item-progresspoint-unpack',
            'Verifying': 'item-progresspoint-verify',
            'Updating': 'item-progresspoint-import',
            'Success': 'item-progresspoint-success'
        }
        if fail_on:
            # Makes no sense to include this if the tasks haven't run.
            completed = True

        state, desc_template = self._task_properties(completed)

        for desc, css_class in classes.items():
            desc_text = desc_template.format(desc)
            # pylint: disable=cell-var-from-loop
            EmptyPromise(lambda: self.q(css='.{}.{}'.format(css_class, state)).present, desc_text, timeout=30)
            if fail_on == desc:
                EmptyPromise(
                    lambda: self.q(css='.{}.is-complete.has-error'.format(css_class)).present,
                    "{} checkpoint marked as failed".format(desc),
                    timeout=30
                )
                # The rest should never run.
                state, desc_template = self._task_properties(False)

    def wait_for_upload(self):
        """
        Wait for the upload to be confirmed.
        """
        EmptyPromise(self.is_upload_finished, 'Upload Finished', timeout=30).fulfill()

    def is_filename_error_showing(self):
        """
        An should be shown if the user tries to upload the wrong kind of file.

        Tell us whether it's currently being shown.
        """
        return self.q(css='#fileupload .error-block').visible

    def is_task_list_showing(self):
        """
        The task list shows a series of steps being performed during import. It is normally
        hidden until the upload begins.

        Tell us whether it's currently visible.
        """
        return self.q(css='.wrapper-status').visible

    def is_timestamp_visible(self):
        """
        Checks if the UTC timestamp of the last successful import is visible
        """
        return self.q(css='.item-progresspoint-success-date').visible

    def wait_for_timestamp_visible(self):
        """
        Wait for the timestamp of the last successful import to be visible.
        """
        EmptyPromise(self.is_timestamp_visible, 'Timestamp Visible', timeout=30).fulfill()

    def wait_for_filename_error(self):
        """
        Wait for the upload field to display an error.
        """
        EmptyPromise(self.is_filename_error_showing, 'Upload Error Displayed', timeout=30).fulfill()

    def finished_target_url(self):
        """
        Grab the URL of the 'view updated library/course outline' button.
        """
        return self.q(css='.action.action-primary')[0].get_attribute('href')


class ImportCoursePage(ImportMixin, TemplateCheckMixin, CoursePage):
    """
    Import page for Courses
    """


class ImportLibraryPage(ImportMixin, TemplateCheckMixin, LibraryLoader, LibraryPage):
    """
    Import page for Libraries
    """
