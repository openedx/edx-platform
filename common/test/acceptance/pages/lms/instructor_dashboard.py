# -*- coding: utf-8 -*-
"""
Instructor (2) dashboard page.
"""

from bok_choy.page_object import PageObject
from .course_page import CoursePage
import os


class InstructorDashboardPage(CoursePage):
    """
    Instructor dashboard, where course staff can manage a course.
    """
    url_path = "instructor"

    def is_browser_on_page(self):
        return self.q(css='div.instructor-dashboard-wrapper-2').present

    def select_membership(self):
        """
        Selects the membership tab and returns the MembershipSection
        """
        self.q(css='a[data-section=membership]').first.click()
        membership_section = MembershipPage(self.browser)
        membership_section.wait_for_page()
        return membership_section


class MembershipPage(PageObject):
    """
    Membership section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='a[data-section=membership].active-section').present

    def select_auto_enroll_section(self):
        """
        returns the MembershipPageAutoEnrollSection
        """
        return MembershipPageAutoEnrollSection(self.browser)

    def _get_cohort_options(self):
        """
        Returns the available options in the cohort dropdown, including the initial "Select a cohort group".
        """
        return self.q(css=".cohort-management #cohort-select option")

    def _cohort_name(self, label):
        """
        Returns the name of the cohort with the count information excluded.
        """
        return label.split(' (')[0]

    def _cohort_count(self, label):
        """
        Returns the count for the cohort (as specified in the label in the selector).
        """
        return int(label.split(' (')[1].split(')')[0])

    def get_cohorts(self):
        """
        Returns, as a list, the names of the available cohorts in the drop-down, filtering out "Select a cohort group".
        """
        return [
            self._cohort_name(opt.text)
            for opt in self._get_cohort_options().filter(lambda el: el.get_attribute('value') != "")
        ]

    def get_selected_cohort(self):
        """
        Returns the name of the selected cohort.
        """
        return self._cohort_name(
            self._get_cohort_options().filter(lambda el: el.is_selected()).first.text[0]
        )

    def get_selected_cohort_count(self):
        """
        Returns the number of users in the selected cohort.
        """
        return self._cohort_count(
            self._get_cohort_options().filter(lambda el: el.is_selected()).first.text[0]
        )

    def select_cohort(self, cohort_name):
        """
        Selects the given cohort in the drop-down.
        """
        self.q(css=".cohort-management #cohort-select option").filter(
            lambda el: self._cohort_name(el.text) == cohort_name
        ).first.click()

    def add_cohort(self, cohort_name):
        """
        Adds a new manual cohort with the specified name.
        """
        self.q(css="div.cohort-management-nav .action-create").first.click()
        textinput = self.q(css="#cohort-create-name").results[0]
        textinput.send_keys(cohort_name)
        self.q(css="div.form-actions .action-save").first.click()

    def get_cohort_group_setup(self):
        """
        Returns the description of the current cohort
        """
        return self.q(css='.cohort-management-group-setup .setup-value').first.text[0]

    def select_edit_settings(self):
        self.q(css=".action-edit").first.click()

    def add_students_to_selected_cohort(self, users):
        """
        Adds a list of users (either usernames or email addresses) to the currently selected cohort.
        """
        textinput = self.q(css="#cohort-management-group-add-students").results[0]
        for user in users:
            textinput.send_keys(user)
            textinput.send_keys(",")
        self.q(css="div.cohort-management-group-add .action-primary").first.click()

    def get_cohort_student_input_field_value(self):
        """
        Returns the contents of the input field where students can be added to a cohort.
        """
        return self.q(css="#cohort-management-group-add-students").results[0].get_attribute("value")

    def _get_cohort_messages(self, type):
        """
        Returns array of messages for given type.
        """
        message_title = self.q(css="div.cohort-management-group-add .cohort-" + type + " .message-title")
        if len(message_title.results) == 0:
            return []
        messages = [message_title.first.text[0]]
        details = self.q(css="div.cohort-management-group-add .cohort-" + type + " .summary-item").results
        for detail in details:
            messages.append(detail.text)
        return messages

    def get_cohort_confirmation_messages(self):
        """
        Returns an array of messages present in the confirmation area of the cohort management UI.
        The first entry in the array is the title. Any further entries are the details.
        """
        return self._get_cohort_messages("confirmations")

    def get_cohort_error_messages(self):
        """
        Returns an array of messages present in the error area of the cohort management UI.
        The first entry in the array is the title. Any further entries are the details.
        """
        return self._get_cohort_messages("errors")

    def select_data_download(self):
        """
        Click on the link to the Data Download Page.
        """
        self.q(css="a.link-cross-reference[data-section=data_download]").first.click()


class MembershipPageAutoEnrollSection(PageObject):
    """
    CSV Auto Enroll section of the Membership tab of the Instructor dashboard.
    """
    url = None

    auto_enroll_browse_button_selector = '.auto_enroll_csv .file-browse input.file_field#browseBtn'
    auto_enroll_upload_button_selector = '.auto_enroll_csv button[name="enrollment_signup_button"]'
    NOTIFICATION_ERROR = 'error'
    NOTIFICATION_WARNING = 'warning'
    NOTIFICATION_SUCCESS = 'confirmation'

    def is_browser_on_page(self):
        return self.q(css=self.auto_enroll_browse_button_selector).present

    def is_file_attachment_browse_button_visible(self):
        """
        Returns True if the Auto-Enroll Browse button is present.
        """
        return self.q(css=self.auto_enroll_browse_button_selector).is_present()

    def is_upload_button_visible(self):
        """
        Returns True if the Auto-Enroll Upload button is present.
        """
        return self.q(css=self.auto_enroll_upload_button_selector).is_present()

    def click_upload_file_button(self):
        """
        Clicks the Auto-Enroll Upload Button.
        """
        self.q(css=self.auto_enroll_upload_button_selector).click()

    def is_notification_displayed(self, section_type):
        """
        Valid inputs for section_type: MembershipPageAutoEnrollSection.NOTIFICATION_SUCCESS /
                                       MembershipPageAutoEnrollSection.NOTIFICATION_WARNING /
                                       MembershipPageAutoEnrollSection.NOTIFICATION_ERROR
        Returns True if a {section_type} notification is displayed.
        """
        notification_selector = '.auto_enroll_csv .results .message-%s' % section_type
        self.wait_for_element_presence(notification_selector, "%s Notification" % section_type.title())
        return self.q(css=notification_selector).is_present()

    def first_notification_message(self, section_type):
        """
        Valid inputs for section_type: MembershipPageAutoEnrollSection.NOTIFICATION_WARNING /
                                       MembershipPageAutoEnrollSection.NOTIFICATION_ERROR
        Returns the first message from the list of messages in the {section_type} section.
        """
        error_message_selector = '.auto_enroll_csv .results .message-%s li.summary-item' % section_type
        self.wait_for_element_presence(error_message_selector, "%s message" % section_type.title())
        return self.q(css=error_message_selector).text[0]

    def get_asset_path(self, file_name):
        """
        Returns the full path of the file to upload.
        These files have been placed in edx-platform/common/test/data/uploads/
        """

        # Separate the list of folders in the path reaching to the current file,
        # e.g.  '... common/test/acceptance/pages/lms/instructor_dashboard.py' will result in
        #       [..., 'common', 'test', 'acceptance', 'pages', 'lms', 'instructor_dashboard.py']
        folders_list_in_path = __file__.split(os.sep)

        # Get rid of the last 4 elements: 'acceptance', 'pages', 'lms', and 'instructor_dashboard.py'
        # to point to the 'test' folder, a shared point in the path's tree.
        folders_list_in_path = folders_list_in_path[:-4]

        # Append the folders in the asset's path
        folders_list_in_path.extend(['data', 'uploads', file_name])

        # Return the joined path of the required asset.
        return os.sep.join(folders_list_in_path)

    def upload_correct_csv_file(self):
        """
        Selects the correct file and clicks the upload button.
        """
        correct_files_path = self.get_asset_path('auto_reg_enrollment.csv')
        self.q(css=self.auto_enroll_browse_button_selector).results[0].send_keys(correct_files_path)
        self.click_upload_file_button()

    def upload_csv_file_with_errors_warnings(self):
        """
        Selects the file which will generate errors and warnings and clicks the upload button.
        """
        errors_warnings_files_path = self.get_asset_path('auto_reg_enrollment_errors_warnings.csv')
        self.q(css=self.auto_enroll_browse_button_selector).results[0].send_keys(errors_warnings_files_path)
        self.click_upload_file_button()

    def upload_non_csv_file(self):
        """
        Selects an image file and clicks the upload button.
        """
        errors_warnings_files_path = self.get_asset_path('image.jpg')
        self.q(css=self.auto_enroll_browse_button_selector).results[0].send_keys(errors_warnings_files_path)
        self.click_upload_file_button()


class DataDownloadPage(PageObject):
    """
    Data Download section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='a[data-section=data_download].active-section').present
