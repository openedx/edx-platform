"""
Import/Export pages.
"""


import os
import re
import time
from datetime import datetime

import requests
import six
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.library import LibraryPage


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


class ImportExportMixin(object):
    """
    Mixin for functionality common to both the import and export pages
    """

    def is_task_list_showing(self):
        """
        The task list shows a series of steps being performed during import or
        export. It is normally hidden until the process begins.

        Tell us whether it's currently visible.
        """
        return self.q(css='.wrapper-status').visible

    def is_timestamp_visible(self):
        """
        Checks if the UTC timestamp of the last successful import/export is visible
        """
        return self.q(css='.item-progresspoint-success-date').visible

    @property
    def parsed_timestamp(self):
        """
        Return python datetime object from the parsed timestamp tuple (date, time)
        """
        timestamp = u"{0} {1}".format(*self.timestamp)
        formatted_timestamp = time.strptime(timestamp, u"%m/%d/%Y %H:%M")
        return datetime.fromtimestamp(time.mktime(formatted_timestamp))

    @property
    def timestamp(self):
        """
        The timestamp is displayed on the page as "(MM/DD/YYYY at HH:mm)"
        It parses the timestamp and returns a (date, time) tuple
        """
        string = self.q(css='.item-progresspoint-success-date').text[0]

        return re.match(six.text_type(r'\(([^ ]+).+?(\d{2}:\d{2})'), string).groups()

    def wait_for_tasks(self, completed=False, fail_on=None):
        """
        Wait for all of the items in the task list to be set to the correct state.
        """
        if fail_on:
            # Makes no sense to include this if the tasks haven't run.
            completed = True

        state, desc_template = self._task_properties(completed)

        for desc, css_class in self.task_classes.items():
            desc_text = desc_template.format(desc)
            # pylint: disable=cell-var-from-loop
            EmptyPromise(lambda: self.q(css=u'.{}.{}'.format(css_class, state)).present, desc_text, timeout=30)
            if fail_on == desc:
                EmptyPromise(
                    lambda: self.q(css=u'.{}.is-complete.has-error'.format(css_class)).present,
                    u"{} checkpoint marked as failed".format(desc),
                    timeout=30
                )
                # The rest should never run.
                state, desc_template = self._task_properties(False)

    def wait_for_timestamp_visible(self):
        """
        Wait for the timestamp of the last successful import/export to be visible.
        """
        EmptyPromise(self.is_timestamp_visible, 'Timestamp Visible', timeout=30).fulfill()

    @staticmethod
    def _task_properties(completed):
        """
        Outputs the CSS class and promise description for task states based on completion.
        """
        if completed:
            return 'is-complete', u"'{}' is marked complete"
        else:
            return 'is-not-started', u"'{}' is in not-yet-started status"


class ExportMixin(ImportExportMixin):
    """
    Export page Mixin.
    """

    url_path = "export"

    task_classes = {
        'Preparing': 'item-progresspoint-prepare',
        'Exporting': 'item-progresspoint-export',
        'Compressing': 'item-progresspoint-compress',
        'Success': 'item-progresspoint-success'
    }

    def is_browser_on_page(self):
        """
        Verify this is the export page
        """
        return self.q(css='body.view-export').present

    def is_click_handler_registered(self):
        """
        Check if the click handler for the export button has been registered yet
        """
        script = """
            var $ = require('jquery'),
                    buttonEvents = $._data($('a.action-primary')[0], 'events');
            return buttonEvents && buttonEvents.hasOwnProperty('click');"""
        stripped_script = ''.join([line.strip() for line in script.split('\n')])
        return self.browser.execute_script(stripped_script)

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
        tarball_url = self.q(css='#download-exported-button')[0].get_attribute('href')
        good_status, headers = self._get_tarball(tarball_url)
        return good_status, headers['content-type'] == 'application/x-tgz'

    def click_export(self):
        """
        Click the export button.
        """
        self.q(css='a.action-export').click()

    def is_error_modal_showing(self):
        """
        Indicates whether or not the error modal is showing.
        """
        return self.q(css='.prompt.error').visible

    def is_export_finished(self):
        """
        Checks if the 'Download Exported Course/Library' button is showing.
        """
        button = self.q(css='#download-exported-button')[0]
        return button.is_displayed() and button.get_attribute('href')

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

    def wait_for_export(self):
        """
        Wait for the export process to finish.
        """
        EmptyPromise(self.is_export_finished, 'Export Finished', timeout=30).fulfill()

    def wait_for_export_click_handler(self):
        """
        Wait for the export button click handler to be registered
        """
        EmptyPromise(self.is_click_handler_registered, 'Export Button Click Handler Registered', timeout=30).fulfill()


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
        return "/".join([BASE_URL, self.url_path, six.text_type(self.locator)])


class ExportCoursePage(ExportMixin, TemplateCheckMixin, CoursePage):
    """
    Export page for Courses
    """


class ExportLibraryPage(ExportMixin, TemplateCheckMixin, LibraryLoader, LibraryPage):
    """
    Export page for Libraries
    """


class ImportMixin(ImportExportMixin):
    """
    Import page mixin
    """

    url_path = "import"

    task_classes = {
        'Uploading': 'item-progresspoint-upload',
        'Unpacking': 'item-progresspoint-unpack',
        'Verifying': 'item-progresspoint-verify',
        'Updating': 'item-progresspoint-import',
        'Success': 'item-progresspoint-success'
    }

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
        # Upload the file.
        self.q(css='input[type="file"]')[0].send_keys(asset_file_path)
        # Upload the same file again. Reason behind this is to decrease the
        # probability or fraction of times the failure occur. Please be
        # noted this doesn't eradicate the root cause of the error, it
        # just decreases to failure rate to minimal.
        # Jira ticket reference: TNL-4191.
        self.q(css='input[type="file"]')[0].send_keys(asset_file_path)
        # Some of the tests need these lines to pass so don't remove them.
        self._wait_for_button()
        click_css(self, '.submit-button', require_notification=True)

    def is_upload_finished(self):
        """
        Checks if the 'view updated' button is showing.
        """
        return self.q(css='#view-updated-button').visible

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
