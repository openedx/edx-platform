# -*- coding: utf-8 -*-
"""
Instructor (2) dashboard page.
"""


import os

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise

from common.test.acceptance.pages.lms.course_page import CoursePage
from common.test.acceptance.tests.helpers import get_options, get_selected_option_text, select_option_by_text


class InstructorDashboardPage(CoursePage):
    """
    Instructor dashboard, where course staff can manage a course.
    """
    url_path = "instructor"

    def is_browser_on_page(self):
        return self.q(css='div.instructor-dashboard-wrapper-2').present

    def get_help_element(self):
        """
        Returns the general Help button in the header.
        """
        return self.q(css='.help-link').first

    def select_membership(self):
        """
        Selects the membership tab and returns the MembershipSection
        """
        self.q(css='[data-section="membership"]').first.click()
        membership_section = MembershipPage(self.browser)
        membership_section.wait_for_page()
        return membership_section

    def select_cohort_management(self):
        """
        Selects the cohort management tab and returns the CohortManagementSection
        """
        self.q(css='[data-section="cohort_management"]').first.click()
        cohort_management_section = CohortManagementSection(self.browser)
        # The first time cohort management is selected, an ajax call is made.
        cohort_management_section.wait_for_ajax()
        cohort_management_section.wait_for_page()
        return cohort_management_section

    def select_certificates(self):
        """
        Selects the certificates tab and returns the CertificatesSection
        """
        self.q(css='[data-section="certificates"]').first.click()
        certificates_section = CertificatesPage(self.browser)
        certificates_section.wait_for_page()
        return certificates_section

    def select_bulk_email(self):
        """
        Selects the email tab and returns the bulk email section
        """
        self.q(css='[data-section="send_email"]').first.click()
        email_section = BulkEmailPage(self.browser)
        email_section.wait_for_page()
        return email_section

    @staticmethod
    def get_asset_path(file_name):
        """
        Returns the full path of the file to upload.
        These files have been placed in edx-platform/common/test/data/uploads/
        """

        # Separate the list of folders in the path reaching to the current file,
        # e.g.  '... common/test/acceptance/pages/lms/instructor_dashboard.py' will result in
        #       [..., 'common', 'test', 'acceptance', 'pages', 'lms', 'instructor_dashboard.py']
        folders_list_in_path = os.path.abspath(__file__).split(os.sep)

        # Get rid of the last 4 elements: 'acceptance', 'pages', 'lms', and 'instructor_dashboard.py'
        # to point to the 'test' folder, a shared point in the path's tree.
        folders_list_in_path = folders_list_in_path[:-4]

        # Append the folders in the asset's path
        folders_list_in_path.extend(['data', 'uploads', file_name])

        # Return the joined path of the required asset.
        return os.sep.join(folders_list_in_path)


class CohortManagementSection(PageObject):
    """
    The Cohort Management section of the Instructor dashboard.
    """
    url = None
    cohort_help_css = '.setup-value .incontext-help.action-secondary.action-help'
    csv_browse_button_selector_css = '.csv-upload #file-upload-form-file'
    csv_upload_button_selector_css = '.csv-upload #file-upload-form-submit'
    content_group_selector_css = 'select.input-cohort-group-association'
    no_content_group_button_css = '.cohort-management-details-association-course input.radio-no'
    select_content_group_button_css = '.cohort-management-details-association-course input.radio-yes'
    assignment_type_buttons_css = '.cohort-management-assignment-type-settings input'

    def get_cohort_help_element(self):
        """
        Returns the help element ('What does it mean')

        Returns:
            help_element (WebElement): help link element
        """
        return self.q(css=self.cohort_help_css).results[0]

    def is_browser_on_page(self):
        """
        Cohorts management exists under one class; however, render time can be longer because of sub-classes
        that must be rendered beneath it. To determine if the browser is on the cohorts management page (and
        allow for it to fully-render), we need to consider three different states of the page:
        * When no cohorts have been added yet
        * When a new cohort is being added (a confirmation state)
        * When cohorts exist (the traditional management page)
        """
        cohorts_warning_title = '.message-warning .message-title'

        if self.q(css=cohorts_warning_title).visible:
            return self.q(css='.message-title').text[0] == u'You currently have no cohorts configured'
        # The page may be in either the traditional management state, or an 'add new cohort' state.
        # Confirm the CSS class is visible because the CSS class can exist on the page even in different states.
        return self.q(css='.cohorts-state-section').visible or self.q(css='.new-cohort-form').visible

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to the cohort management context.
        """
        return u'.cohort-management {}'.format(selector)

    def _get_cohort_options(self):
        """
        Returns the available options in the cohort dropdown, including the initial "Select a cohort".
        """
        def check_func():
            """Promise Check Function"""
            query = self.q(css=self._bounded_selector("#cohort-select option"))
            return len(query) > 0, query

        return Promise(check_func, "Waiting for cohort selector to populate").fulfill()

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

    def save_cohort_settings(self):
        """
        Click on Save button shown after click on Settings tab or when we add a new cohort.
        """
        self.q(css=self._bounded_selector("div.form-actions .action-save")).first.click()

    @property
    def is_assignment_settings_disabled(self):
        """
        Check if assignment settings are disabled.
        """
        attributes = self.q(css=self._bounded_selector('.cohort-management-assignment-type-settings')).attrs('class')
        if 'is-disabled' in attributes[0].split():
            return True

        return False

    @property
    def assignment_settings_message(self):
        """
        Return assignment settings disabled message in case of default cohort.
        """
        query = self.q(css=self._bounded_selector('.copy-error'))
        if query.visible:
            return query.text[0]

        return ''

    @property
    def cohort_name_in_header(self):
        """
        Return cohort name as shown in cohort header.
        """
        return self._cohort_name(self.q(css=self._bounded_selector(".group-header-title .title-value")).text[0])

    def get_cohorts(self):
        """
        Returns, as a list, the names of the available cohorts in the drop-down, filtering out "Select a cohort".
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
        # Note: can't use Select to select by text because the count is also included in the displayed text.
        self._get_cohort_options().filter(
            lambda el: self._cohort_name(el.text) == cohort_name
        ).first.click()
        # wait for cohort to render as selected on screen
        EmptyPromise(
            lambda: self.q(css='.title-value').text[0] == cohort_name,
            "Waiting to confirm cohort has been selected"
        ).fulfill()

    def set_cohort_name(self, cohort_name):
        """
        Set Cohort Name.
        """
        textinput = self.q(css=self._bounded_selector("#cohort-name")).results[0]
        textinput.clear()
        textinput.send_keys(cohort_name)

    def set_assignment_type(self, assignment_type):
        """
        Set assignment type for selected cohort.

        Arguments:
            assignment_type (str): Should be 'random' or 'manual'
        """
        css = self._bounded_selector(self.assignment_type_buttons_css)
        self.q(css=css).filter(lambda el: el.get_attribute('value') == assignment_type).first.click()

    def add_cohort(self, cohort_name, content_group=None, assignment_type=None):
        """
        Adds a new manual cohort with the specified name.
        If a content group should also be associated, the name of the content group should be specified.
        """
        add_cohort_selector = self._bounded_selector(".action-create")

        # We need to wait because sometime add cohort button is not in a state to be clickable.
        self.wait_for_element_presence(add_cohort_selector, 'Add Cohort button is present.')
        create_buttons = self.q(css=add_cohort_selector)
        # There are 2 create buttons on the page. The second one is only present when no cohort yet exists
        # (in which case the first is not visible). Click on the last present create button.
        create_buttons.results[len(create_buttons.results) - 1].click()

        # Both the edit and create forms have an element with id="cohort-name". Verify that the create form
        # has been rendered.
        self.wait_for(
            lambda: "Add a New Cohort" in self.q(css=self._bounded_selector(".form-title")).text,
            "Create cohort form is visible"
        )
        textinput = self.q(css=self._bounded_selector("#cohort-name")).results[0]
        textinput.send_keys(cohort_name)

        # Manual assignment type will be selected by default for a new cohort
        # if we are not setting the assignment type explicitly
        if assignment_type:
            self.set_assignment_type(assignment_type)

        if content_group:
            self._select_associated_content_group(content_group)
        self.save_cohort_settings()
        EmptyPromise(
            lambda: cohort_name == self.get_selected_cohort(), "Waiting for new cohort"
        ).fulfill()

    def get_cohort_group_setup(self):
        """
        Returns the description of the current cohort
        """
        return self.q(css=self._bounded_selector('.cohort-management-group-setup .setup-value')).first.text[0]

    def select_edit_settings(self):
        self.q(css=self._bounded_selector(".action-edit")).first.click()

    def select_manage_settings(self):
        """
        Click on Manage Students Tab under cohort management section.
        """
        self.q(css=self._bounded_selector(".tab-manage_students")).first.click()

    def add_students_to_selected_cohort(self, users):
        """
        Adds a list of users (either usernames or email addresses) to the currently selected cohort.
        """
        textinput = self.q(css=self._bounded_selector("#cohort-management-group-add-students")).results[0]
        for user in users:
            textinput.send_keys(user)
            textinput.send_keys(",")
        self.q(css=self._bounded_selector("div.cohort-management-group-add .action-primary")).first.click()
        # Expect the confirmation message substring. (The full message will differ depending on 1 or >1 students added)
        self.wait_for(
            lambda: "added to this cohort" in self.get_cohort_confirmation_messages(wait_for_messages=True)[0],
            "Student(s) added confirmation message."
        )

    def get_cohort_student_input_field_value(self):
        """
        Returns the contents of the input field where students can be added to a cohort.
        """
        return self.q(
            css=self._bounded_selector("#cohort-management-group-add-students")
        ).results[0].get_attribute("value")

    def select_studio_group_settings(self):
        """
        When no content groups have been defined, a messages appears with a link
        to go to Studio group settings. This method assumes the link is visible and clicks it.
        """
        return self.q(css=self._bounded_selector("a.link-to-group-settings")).first.click()

    def get_all_content_groups(self):
        """
        Returns all the content groups available for associating with the cohort currently being edited.
        """
        selector_query = self.q(css=self._bounded_selector(self.content_group_selector_css))
        return [
            option.text for option in get_options(selector_query) if option.text != "Not selected"
        ]

    def get_cohort_associated_content_group(self):
        """
        Returns the content group associated with the cohort currently being edited.
        If no content group is associated, returns None.
        """
        self.select_cohort_settings()
        radio_button = self.q(css=self._bounded_selector(self.no_content_group_button_css)).results[0]
        if radio_button.is_selected():
            return None
        return get_selected_option_text(self.q(css=self._bounded_selector(self.content_group_selector_css)))

    def get_cohort_associated_assignment_type(self):
        """
        Returns the assignment type associated with the cohort currently being edited.
        """
        self.select_cohort_settings()
        css_selector = self._bounded_selector(self.assignment_type_buttons_css)
        radio_button = self.q(css=css_selector).filter(lambda el: el.is_selected()).results[0]
        return radio_button.get_attribute('value')

    def set_cohort_associated_content_group(self, content_group=None, select_settings=True):
        """
        Sets the content group associated with the cohort currently being edited.
        If content_group is None, un-links the cohort from any content group.
        Presses Save to update the cohort's settings.
        """
        if select_settings:
            self.select_cohort_settings()
        if content_group is None:
            self.q(css=self._bounded_selector(self.no_content_group_button_css)).first.click()
        else:
            self._select_associated_content_group(content_group)
        self.save_cohort_settings()

    def _select_associated_content_group(self, content_group):
        """
        Selects the specified content group from the selector. Assumes that content_group is not None.
        """
        self.select_content_group_radio_button()
        select_option_by_text(
            self.q(css=self._bounded_selector(self.content_group_selector_css)), content_group
        )

    def select_content_group_radio_button(self):
        """
        Clicks the radio button for "No Content Group" association.
        Returns whether or not the radio button is in the selected state after the click.
        """
        radio_button = self.q(css=self._bounded_selector(self.select_content_group_button_css)).results[0]
        if not radio_button.is_enabled():
            return False
        radio_button.click()
        return radio_button.is_selected()

    def select_cohort_settings(self):
        """
        Selects the settings tab for the cohort currently being edited.
        """
        self.q(css=self._bounded_selector(".cohort-management-settings li.tab-settings>.toggle-button")).first.click()

    # pylint: disable=redefined-builtin
    def get_cohort_settings_messages(self, type="confirmation", wait_for_messages=True):
        """
        Returns an array of messages related to modifying cohort settings. If wait_for_messages
        is True, will wait for a message to appear.
        """
        title_css = "div.cohort-management-settings .message-" + type + " .message-title"
        detail_css = "div.cohort-management-settings .message-" + type + " .summary-item"

        return self._get_messages(title_css, detail_css, wait_for_messages=wait_for_messages)

    def _get_cohort_messages(self, type, wait_for_messages=False):
        """
        Returns array of messages related to manipulating cohorts directly through the UI for the given type.
        """
        title_css = "div.cohort-management-group-add .cohort-" + type + " .message-title"
        detail_css = "div.cohort-management-group-add .cohort-" + type + " .summary-item"

        return self._get_messages(title_css, detail_css, wait_for_messages)

    def get_csv_messages(self):
        """
        Returns array of messages related to a CSV upload of cohort assignments.
        """
        title_css = ".csv-upload .message-title"
        detail_css = ".csv-upload .summary-item"
        return self._get_messages(title_css, detail_css)

    def _get_messages(self, title_css, details_css, wait_for_messages=False):
        """
        Helper method to get messages given title and details CSS.
        """
        if wait_for_messages:
            EmptyPromise(
                lambda: len(self.q(css=self._bounded_selector(title_css)).results) != 0,
                "Waiting for messages to appear"
            ).fulfill()
        message_title = self.q(css=self._bounded_selector(title_css))
        if len(message_title.results) == 0:
            return []
        messages = [message_title.first.text[0]]
        details = self.q(css=self._bounded_selector(details_css)).results
        for detail in details:
            messages.append(detail.text)
        return messages

    def get_cohort_confirmation_messages(self, wait_for_messages=False):
        """
        Returns an array of messages present in the confirmation area of the cohort management UI.
        The first entry in the array is the title. Any further entries are the details.
        """
        return self._get_cohort_messages("confirmations", wait_for_messages)

    def get_cohort_error_messages(self):
        """
        Returns an array of messages present in the error area of the cohort management UI.
        The first entry in the array is the title. Any further entries are the details.
        """
        return self._get_cohort_messages("errors")

    def get_cohort_related_content_group_message(self):
        """
        Gets the error message shown next to the content group selector for the currently selected cohort.
        If no message, returns None.
        """
        message = self.q(css=self._bounded_selector(".input-group-other .copy-error"))
        if not message:
            return None
        return message.results[0].text

    def select_data_download(self):
        """
        Click on the link to the Data Download Page.
        """
        self.q(css=self._bounded_selector('[data-section="data_download"]')).first.click()

    def upload_cohort_file(self, filename):
        """
        Uploads a file with cohort assignment information.
        """
        # Toggle on the CSV upload section.
        cvs_upload_toggle_css = '.toggle-cohort-management-secondary'
        self.wait_for_element_visibility(cvs_upload_toggle_css, "Wait for csv upload link to appear")
        cvs_upload_toggle = self.q(css=self._bounded_selector(cvs_upload_toggle_css)).first
        if cvs_upload_toggle:
            cvs_upload_toggle.click()
            self.wait_for_element_visibility(
                self._bounded_selector(self.csv_browse_button_selector_css),
                'File upload link visible'
            )
        path = InstructorDashboardPage.get_asset_path(filename)
        file_input = self.q(css=self._bounded_selector(self.csv_browse_button_selector_css)).results[0]
        file_input.send_keys(path)
        self.q(css=self._bounded_selector(self.csv_upload_button_selector_css)).first.click()

    @property
    def is_cohorted(self):
        """
        Returns the state of `Enable Cohorts` checkbox state.
        """
        return self.q(css=self._bounded_selector('.cohorts-state')).selected

    @is_cohorted.setter
    def is_cohorted(self, state):
        """
        Check/Uncheck the `Enable Cohorts` checkbox state.
        """
        if state != self.is_cohorted:
            self.q(css=self._bounded_selector('.cohorts-state')).first.click()
            self.wait_for_ajax()

    def cohort_management_controls_visible(self):
        """
        Return the visibility status of cohort management controls(cohort selector section etc).
        """
        return (self.q(css=self._bounded_selector('.cohort-management-nav')).visible and
                self.q(css=self._bounded_selector('.wrapper-cohort-supplemental')).visible)


class BulkEmailPage(PageObject):
    """
    Bulk email section of the instructor dashboard.
    This feature is controlled by an admin panel feature flag, which is turned on via database fixture for testing.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='[data-section=send_email].active-section').present


class MembershipPage(PageObject):
    """
    Membership section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='[data-section=membership].active-section').present

    def select_auto_enroll_section(self):
        """
        Returns the MembershipPageAutoEnrollSection page object.
        """
        return MembershipPageAutoEnrollSection(self.browser)


class MembershipPageAutoEnrollSection(PageObject):
    """
    CSV Auto Enroll section of the Membership tab of the Instructor dashboard.
    """
    url = None

    auto_enroll_browse_button_selector = '.auto_enroll_csv .file-browse input.file_field#browseBtn-auto-enroll'
    auto_enroll_upload_button_selector = '.auto_enroll_csv button[name="enrollment_signup_button"]'
    batch_enrollment_selector = '.batch-enrollment'
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
        notification_selector = u'.auto_enroll_csv .results .message-%s' % section_type
        self.wait_for_element_presence(notification_selector, u"%s Notification" % section_type.title())
        return self.q(css=notification_selector).is_present()

    def first_notification_message(self, section_type):
        """
        Valid inputs for section_type: MembershipPageAutoEnrollSection.NOTIFICATION_WARNING /
                                       MembershipPageAutoEnrollSection.NOTIFICATION_ERROR
        Returns the first message from the list of messages in the {section_type} section.
        """
        error_message_selector = u'.auto_enroll_csv .results .message-%s li.summary-item' % section_type
        self.wait_for_element_presence(error_message_selector, u"%s message" % section_type.title())
        return self.q(css=error_message_selector).text[0]

    def upload_correct_csv_file(self):
        """
        Selects the correct file and clicks the upload button.
        """
        self._upload_file('auto_reg_enrollment.csv')

    def upload_csv_file_with_errors_warnings(self):
        """
        Selects the file which will generate errors and warnings and clicks the upload button.
        """
        self._upload_file('auto_reg_enrollment_errors_warnings.csv')

    def upload_non_csv_file(self):
        """
        Selects an image file and clicks the upload button.
        """
        self._upload_file('image.jpg')

    def _upload_file(self, filename):
        """
        Helper method to upload a file with registration and enrollment information.
        """
        file_path = InstructorDashboardPage.get_asset_path(filename)
        self.q(css=self.auto_enroll_browse_button_selector).results[0].send_keys(file_path)
        self.click_upload_file_button()

    def fill_enrollment_batch_text_box(self, email):
        """
        Fill in the form with the provided email and submit it.
        """
        email_selector = u"{} textarea".format(self.batch_enrollment_selector)
        enrollment_button = u"{} .enrollment-button[data-action='enroll']".format(self.batch_enrollment_selector)

        # Fill the email addresses after the email selector is visible.
        self.wait_for_element_visibility(email_selector, 'Email field is visible')
        self.q(css=email_selector).fill(email)

        # Verify enrollment button is present before clicking
        EmptyPromise(
            lambda: self.q(css=enrollment_button).present, "Enrollment button"
        ).fulfill()
        self.q(css=enrollment_button).click()

    def get_notification_text(self):
        """
        Check notification div is visible and have message.
        """
        notification_selector = u'{} .request-response'.format(self.batch_enrollment_selector)
        self.wait_for_element_visibility(notification_selector, 'Notification div is visible')
        return self.q(css=u"{} h3".format(notification_selector)).text


class CertificatesPage(PageObject):
    """
    Certificates section of the Instructor dashboard.
    """
    url = None
    PAGE_SELECTOR = 'section#certificates'

    def is_browser_on_page(self):
        return self.q(css='[data-section=certificates].active-section').present
