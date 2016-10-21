# -*- coding: utf-8 -*-
"""
Instructor (2) dashboard page.
"""

from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms.course_page import CoursePage
import os
from bok_choy.promise import EmptyPromise, Promise
from common.test.acceptance.tests.helpers import select_option_by_text, get_selected_option_text, get_options


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

    def select_data_download(self):
        """
        Selects the data download tab and returns a DataDownloadPage.
        """
        self.q(css='[data-section="data_download"]').first.click()
        data_download_section = DataDownloadPage(self.browser)
        data_download_section.wait_for_page()
        return data_download_section

    def select_student_admin(self, admin_class):
        """
        Selects the student admin tab and returns the requested
        admin section.
        admin_class should be a subclass of StudentAdminPage.
        """
        self.q(css='[data-section="student_admin"]').first.click()
        student_admin_section = admin_class(self.browser)
        student_admin_section.wait_for_page()
        return student_admin_section

    def select_certificates(self):
        """
        Selects the certificates tab and returns the CertificatesSection
        """
        self.q(css='[data-section="certificates"]').first.click()
        certificates_section = CertificatesPage(self.browser)
        certificates_section.wait_for_page()
        return certificates_section

    def select_special_exams(self):
        """
        Selects the timed exam tab and returns the Special Exams Section
        """
        self.q(css='[data-section="special_exams"]').first.click()
        timed_exam_section = SpecialExamsPage(self.browser)
        timed_exam_section.wait_for_page()
        return timed_exam_section

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
        folders_list_in_path = __file__.split(os.sep)

        # Get rid of the last 4 elements: 'acceptance', 'pages', 'lms', and 'instructor_dashboard.py'
        # to point to the 'test' folder, a shared point in the path's tree.
        folders_list_in_path = folders_list_in_path[:-4]

        # Append the folders in the asset's path
        folders_list_in_path.extend(['data', 'uploads', file_name])

        # Return the joined path of the required asset.
        return os.sep.join(folders_list_in_path)


class BulkEmailPage(PageObject):
    """
    Bulk email section of the instructor dashboard.
    This feature is controlled by an admin panel feature flag, which is turned on via database fixture for testing.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='[data-section=send_email].active-section').present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to the bulk-email context.
        """
        return '.send-email {}'.format(selector)

    def _select_recipient(self, recipient):
        """
        Selects the specified recipient from the selector. Assumes that recipient is not None.
        """
        recipient_selector_css = "input[name='send_to'][value='{}']".format(recipient)
        self.q(css=self._bounded_selector(recipient_selector_css))[0].click()

    def send_message(self, recipients):
        """
        Send a test message to the specified recipient.
        """
        send_css = "input[name='send']"
        test_subject = "Hello"
        test_body = "This is a test email"

        for recipient in recipients:
            self._select_recipient(recipient)
        self.q(css=self._bounded_selector("input[name='subject']")).fill(test_subject)
        self.q(css=self._bounded_selector("iframe#mce_0_ifr"))[0].click()
        self.q(css=self._bounded_selector("iframe#mce_0_ifr"))[0].send_keys(test_body)

        with self.handle_alert(confirm=True):
            self.q(css=self._bounded_selector(send_css)).click()

    def verify_message_queued_successfully(self):
        """
        Verifies that the "you email was queued" message appears.

        Note that this does NOT ensure the message gets sent successfully, that functionality
        is covered by the bulk_email unit tests.
        """
        confirmation_selector = self._bounded_selector(".msg-confirm")
        expected_text = u"Your email message was successfully queued for sending."
        EmptyPromise(
            lambda: expected_text in self.q(css=confirmation_selector)[0].text,
            "Message Queued Confirmation"
        ).fulfill()


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


class SpecialExamsPage(PageObject):
    """
    Timed exam section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='[data-section=special_exams].active-section').present

    def select_allowance_section(self):
        """
        Expand the allowance section
        """
        allowance_section = SpecialExamsPageAllowanceSection(self.browser)
        if not self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-0[aria-selected=true]").present:
            self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-0").click()
            self.wait_for_element_presence("div.wrap #ui-accordion-proctoring-accordion-header-0[aria-selected=true]",
                                           "Allowance Section")
        allowance_section.wait_for_page()
        return allowance_section

    def select_exam_attempts_section(self):
        """
        Expand the Student Attempts Section
        """
        exam_attempts_section = SpecialExamsPageAttemptsSection(self.browser)
        if not self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-1[aria-selected=true]").present:
            self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-1").click()
            self.wait_for_element_presence("div.wrap #ui-accordion-proctoring-accordion-header-1[aria-selected=true]",
                                           "Attempts Section")
        exam_attempts_section.wait_for_page()
        return exam_attempts_section


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
    discussion_form_selectors = {
        'course-wide': '.cohort-course-wide-discussions-form',
        'inline': '.cohort-inline-discussions-form'
    }

    def get_cohort_help_element_and_click_help(self):
        """
        Clicks help link and returns it. Specifically, clicks 'What does it mean'

        Returns:
            help_element (WebElement): help link element
        """
        help_element = self.q(css=self.cohort_help_css).results[0]
        help_element.click()
        return help_element

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
        return '.cohort-management {}'.format(selector)

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

    def toggles_showing_of_discussion_topics(self):
        """
        Shows the discussion topics.
        """
        self.q(css=self._bounded_selector(".toggle-cohort-management-discussions")).first.click()
        self.wait_for_element_visibility("#cohort-discussions-management", "Waiting for discussions to appear")

    def discussion_topics_visible(self):
        """
        Returns the visibility status of cohort discussion controls.
        """
        EmptyPromise(
            lambda: self.q(css=self._bounded_selector('.cohort-discussions-nav')).results != 0,
            "Waiting for discussion section to show"
        ).fulfill()

        return (self.q(css=self._bounded_selector('.cohort-course-wide-discussions-nav')).visible and
                self.q(css=self._bounded_selector('.cohort-inline-discussions-nav')).visible)

    def select_discussion_topic(self, key):
        """
        Selects discussion topic checkbox by clicking on it.
        """
        self.q(css=self._bounded_selector(".check-discussion-subcategory-%s" % key)).first.click()

    def select_always_inline_discussion(self):
        """
        Selects the always_cohort_inline_discussions radio button.
        """
        self.q(css=self._bounded_selector(".check-all-inline-discussions")).first.click()

    def always_inline_discussion_selected(self):
        """
        Returns the checked always_cohort_inline_discussions radio button.
        """
        return self.q(css=self._bounded_selector(".check-all-inline-discussions:checked"))

    def cohort_some_inline_discussion_selected(self):
        """
        Returns the checked some_cohort_inline_discussions radio button.
        """
        return self.q(css=self._bounded_selector(".check-cohort-inline-discussions:checked"))

    def select_cohort_some_inline_discussion(self):
        """
        Selects the cohort_some_inline_discussions radio button.
        """
        self.q(css=self._bounded_selector(".check-cohort-inline-discussions")).first.click()

    def inline_discussion_topics_disabled(self):
        """
        Returns the status of inline discussion topics, enabled or disabled.
        """
        inline_topics = self.q(css=self._bounded_selector('.check-discussion-subcategory-inline'))
        return all(topic.get_attribute('disabled') == 'true' for topic in inline_topics)

    def is_save_button_disabled(self, key):
        """
        Returns the status for form's save button, enabled or disabled.
        """
        save_button_css = '%s %s' % (self.discussion_form_selectors[key], '.action-save')
        disabled = self.q(css=self._bounded_selector(save_button_css)).attrs('disabled')
        return disabled[0] == 'true'

    def is_category_selected(self):
        """
        Returns the status for category checkboxes.
        """
        return self.q(css=self._bounded_selector('.check-discussion-category:checked')).is_present()

    def get_cohorted_topics_count(self, key):
        """
        Returns the count for cohorted topics.
        """
        cohorted_topics = self.q(css=self._bounded_selector('.check-discussion-subcategory-%s:checked' % key))
        return len(cohorted_topics.results)

    def save_discussion_topics(self, key):
        """
        Saves the discussion topics.
        """
        save_button_css = '%s %s' % (self.discussion_form_selectors[key], '.action-save')
        self.q(css=self._bounded_selector(save_button_css)).first.click()

    def get_cohort_discussions_message(self, key, msg_type="confirmation"):
        """
        Returns the message related to modifying discussion topics.
        """
        title_css = "%s .message-%s .message-title" % (self.discussion_form_selectors[key], msg_type)

        EmptyPromise(
            lambda: self.q(css=self._bounded_selector(title_css)),
            "Waiting for message to appear"
        ).fulfill()

        message_title = self.q(css=self._bounded_selector(title_css))

        if len(message_title.results) == 0:
            return ''
        return message_title.first.text[0]

    def cohort_discussion_heading_is_visible(self, key):
        """
        Returns the visibility of discussion topic headings.
        """
        form_heading_css = '%s %s' % (self.discussion_form_selectors[key], '.subsection-title')
        discussion_heading = self.q(css=self._bounded_selector(form_heading_css))

        if len(discussion_heading) == 0:
            return False
        return discussion_heading.first.text[0]

    def cohort_management_controls_visible(self):
        """
        Return the visibility status of cohort management controls(cohort selector section etc).
        """
        return (self.q(css=self._bounded_selector('.cohort-management-nav')).visible and
                self.q(css=self._bounded_selector('.wrapper-cohort-supplemental')).visible)


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
        email_selector = "{} textarea".format(self.batch_enrollment_selector)
        enrollment_button = "{} .enrollment-button[data-action='enroll']".format(self.batch_enrollment_selector)

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
        notification_selector = '{} .request-response'.format(self.batch_enrollment_selector)
        self.wait_for_element_visibility(notification_selector, 'Notification div is visible')
        return self.q(css="{} h3".format(notification_selector)).text


class SpecialExamsPageAllowanceSection(PageObject):
    """
    Allowance section of the Instructor dashboard's Special Exams tab.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-0[aria-selected=true]").present

    @property
    def is_add_allowance_button_visible(self):
        """
        Returns True if the Add Allowance button is present.
        """
        return self.q(css="a#add-allowance").present

    @property
    def is_allowance_record_visible(self):
        """
        Returns True if the Add Allowance button is present.
        """
        return self.q(css="table.allowance-table tr.allowance-items").present

    @property
    def is_add_allowance_popup_visible(self):
        """
        Returns True if the Add Allowance popup and it's all assets are present.
        """
        return self.q(css="div.modal div.modal-header").present and self._are_all_assets_present()

    def _are_all_assets_present(self):
        """
        Returns True if all the assets present in add allowance popup/form
        """
        return (
            self.q(css="select#proctored_exam").present and
            self.q(css="label#exam_type_label").present and
            self.q(css="input#allowance_value").present and
            self.q(css="input#user_info").present and
            self.q(css="input#addNewAllowance").present
        ) and (
            # This will be present if exam is proctored
            self.q(css="select#allowance_type").present or
            # This will be present if exam is timed
            self.q(css="label#timed_exam_allowance_type").present
        )

    def click_add_allowance_button(self):
        """
        Click the add allowance button
        """
        self.q(css="a#add-allowance").click()
        self.wait_for_element_presence("div.modal div.modal-header", "Popup should be visible")

    def submit_allowance_form(self, allowed_minutes, username):
        """
        Fill and submit the allowance
        """
        self.q(css='input#allowance_value').fill(allowed_minutes)
        self.q(css='input#user_info').fill(username)
        self.q(css="input#addNewAllowance").click()
        self.wait_for_element_absence("div.modal div.modal-header", "Popup should be hidden")
        self.wait_for_ajax()


class SpecialExamsPageAttemptsSection(PageObject):
    """
    Exam Attempts section of the Instructor dashboard's Special Exams tab.
    """
    url = None

    def is_browser_on_page(self):
        return (self.q(css="div.wrap #ui-accordion-proctoring-accordion-header-1[aria-selected=true]").present and
                self.q(css="#search_attempt_id").present)

    @property
    def is_search_text_field_visible(self):
        """
        Returns True if the search field is present
        """
        return self.q(css="#search_attempt_id").present

    @property
    def is_student_attempt_visible(self):
        """
        Returns True if a row with the Student's attempt is present
        """
        return self.q(css="a.remove-attempt").present

    def remove_student_attempt(self):
        """
        Clicks the "x" to remove the Student's attempt.
        """
        with self.handle_alert(confirm=True):
            self.q(css=".remove-attempt").first.click()
        self.wait_for_element_absence(".remove-attempt", "exam attempt")


class DataDownloadPage(PageObject):
    """
    Data Download section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='[data-section=data_download].active-section').present

    @property
    def generate_student_report_button(self):
        """
        Returns the "Download profile information as a CSV" button.
        """
        return self.q(css='input[name=list-profiles-csv]')

    @property
    def generate_grade_report_button(self):
        """
        Returns the "Generate Grade Report" button.
        """
        return self.q(css='input[name=calculate-grades-csv]')

    @property
    def generate_problem_report_button(self):
        """
        Returns the "Generate Problem Grade Report" button.
        """
        return self.q(css='input[name=problem-grade-report]')

    @property
    def report_download_links(self):
        """
        Returns the download links for the current page.
        """
        return self.q(css="#report-downloads-table .file-download-link>a")

    @property
    def generate_ora2_response_report_button(self):
        """
        Returns the ORA2 response download button for the current page.
        """
        return self.q(css='input[name=export-ora2-data]')

    def wait_for_available_report(self):
        """
        Waits for a downloadable report to be available.
        """
        EmptyPromise(
            lambda: len(self.report_download_links) >= 1, 'Waiting for downloadable report'
        ).fulfill()

    def get_available_reports_for_download(self):
        """
        Returns a list of all the available reports for download.
        """
        return self.report_download_links.map(lambda el: el.text)


class StudentAdminPage(PageObject):
    """
    Student admin section of the Instructor dashboard.
    """
    url = None
    CONTAINER = None

    PROBLEM_INPUT_NAME = None
    STUDENT_EMAIL_INPUT_NAME = None

    RESET_ATTEMPTS_BUTTON_NAME = None
    RESCORE_BUTTON_NAME = None
    RESCORE_IF_HIGHER_BUTTON_NAME = None
    DELETE_STATE_BUTTON_NAME = None

    BACKGROUND_TASKS_BUTTON_NAME = None
    TASK_HISTORY_TABLE_NAME = None

    def is_browser_on_page(self):
        """
        Confirms student admin section is present
        """
        return self.q(css='[data-section=student_admin].active-section').present

    def _input_with_name(self, input_name):
        """
        Returns the input box with the given name
        for this object's container.
        """
        return self.q(css='{} input[name={}]'.format(self.CONTAINER, input_name))

    @property
    def problem_location_input(self):
        """
        Returns input box for problem location
        """
        return self._input_with_name(self.PROBLEM_INPUT_NAME)

    def set_problem_location(self, problem_location):
        """
        Returns input box for problem location
        """
        input_box = self.problem_location_input.first.results[0]
        input_box.send_keys(unicode(problem_location))

    @property
    def student_email_or_username_input(self):
        """
        Returns email address/username input box.
        """
        return self._input_with_name(self.STUDENT_EMAIL_INPUT_NAME)

    def set_student_email_or_username(self, email_or_username):
        """
        Sets given email or username as value of
        student email/username input box.
        """
        input_box = self.student_email_or_username_input.first.results[0]
        input_box.send_keys(email_or_username)

    @property
    def reset_attempts_button(self):
        """
        Returns reset student attempts button.
        """
        return self._input_with_name(self.RESET_ATTEMPTS_BUTTON_NAME)

    @property
    def rescore_button(self):
        """
        Returns rescore button.
        """
        return self._input_with_name(self.RESCORE_BUTTON_NAME)

    @property
    def rescore_if_higher_button(self):
        """
        Returns rescore if higher button.
        """
        return self._input_with_name(self.RESCORE_IF_HIGHER_BUTTON_NAME)

    @property
    def delete_state_button(self):
        """
        Returns delete state button.
        """
        return self._input_with_name(self.DELETE_STATE_BUTTON_NAME)

    @property
    def task_history_button(self):
        """
        Return Background Tasks History button.
        """
        return self._input_with_name(self.BACKGROUND_TASKS_BUTTON_NAME)

    def wait_for_task_history_table(self):
        """
        Waits until the task history table is visible.
        """
        def check_func():
            """
            Promise Check Function
            """
            query = self.q(css="{} .{}".format(self.CONTAINER, self.TASK_HISTORY_TABLE_NAME))
            return query.visible, query

        return Promise(check_func, "Waiting for student admin task history table to be visible.").fulfill()

    def wait_for_task_completion(self, expected_task_string):
        """
        Waits until the task history table is visible.
        """
        def check_func():
            """
            Promise Check Function
            """
            self.task_history_button.click()
            table = self.wait_for_task_history_table()
            return len(table) > 0 and expected_task_string in table.results[0].text

        return EmptyPromise(check_func, "Waiting for student admin task to complete.").fulfill()


class StudentSpecificAdmin(StudentAdminPage):
    """
    Student specific section of the Student Admin page.
    """
    CONTAINER = ".student-grade-container"

    PROBLEM_INPUT_NAME = "problem-select-single"
    STUDENT_EMAIL_INPUT_NAME = "student-select-grade"

    RESET_ATTEMPTS_BUTTON_NAME = "reset-attempts-single"
    RESCORE_BUTTON_NAME = "rescore-problem-single"
    RESCORE_IF_HIGHER_BUTTON_NAME = "rescore-problem-if-higher-single"
    DELETE_STATE_BUTTON_NAME = "delete-state-single"

    BACKGROUND_TASKS_BUTTON_NAME = "task-history-single"
    TASK_HISTORY_TABLE_NAME = "task-history-single-table"


class CourseSpecificAdmin(StudentAdminPage):
    """
    Course specific section of the Student Admin page.
    """
    CONTAINER = ".course-specific-container"

    PROBLEM_INPUT_NAME = "problem-select-all"
    STUDENT_EMAIL_INPUT_NAME = None

    RESET_ATTEMPTS_BUTTON_NAME = "reset-attempts-all"
    RESCORE_BUTTON_NAME = "rescore-problem-all"
    RESCORE_IF_HIGHER_BUTTON_NAME = "rescore-problem-all-if-higher"
    DELETE_STATE_BUTTON_NAME = None

    BACKGROUND_TASKS_BUTTON_NAME = "task-history-all"
    TASK_HISTORY_TABLE_NAME = "task-history-all-table"


class EntranceExamAdmin(StudentAdminPage):
    """
    Entrance exam section of the Student Admin page.
    """
    CONTAINER = ".entrance-exam-grade-container"

    STUDENT_EMAIL_INPUT_NAME = "entrance-exam-student-select-grade"
    PROBLEM_INPUT_NAME = None

    RESET_ATTEMPTS_BUTTON_NAME = "reset-entrance-exam-attempts"
    RESCORE_BUTTON_NAME = "rescore-entrance-exam"
    RESCORE_IF_HIGHER_BUTTON_NAME = "rescore-entrance-exam-if-higher"
    DELETE_STATE_BUTTON_NAME = "delete-entrance-exam-state"

    BACKGROUND_TASKS_BUTTON_NAME = "entrance-exam-task-history"
    TASK_HISTORY_TABLE_NAME = "entrance-exam-task-history-table"

    @property
    def skip_entrance_exam_button(self):
        """
        Return Let Student Skip Entrance Exam button.
        """
        return self.q(css='{} input[name=skip-entrance-exam]'.format(self.CONTAINER))

    @property
    def top_notification(self):
        """
        Returns show background task history for student button.
        """
        return self.q(css='{} .request-response-error'.format(self.CONTAINER)).first

    def are_all_buttons_visible(self):
        """
        Returns whether all buttons related to entrance exams
        are visible.
        """
        return (
            self.student_email_or_username_input.is_present() and
            self.reset_attempts_button.is_present() and
            self.rescore_button.is_present() and
            self.rescore_if_higher_button.is_present() and
            self.delete_state_button.is_present() and
            self.task_history_button.is_present()
        )


class CertificatesPage(PageObject):
    """
    Certificates section of the Instructor dashboard.
    """
    url = None
    PAGE_SELECTOR = 'section#certificates'

    def wait_for_certificate_exceptions_section(self):
        """
        Wait for Certificate Exceptions to be rendered on page
        """
        self.wait_for_element_visibility(
            'div.certificate-exception-container',
            'Certificate Exception Section is visible'
        )
        self.wait_for_element_visibility('#add-exception', 'Add Exception button is visible')

    def wait_for_certificate_invalidations_section(self):  # pylint: disable=invalid-name
        """
        Wait for certificate invalidations section to be rendered on page
        """
        self.wait_for_element_visibility(
            'div.certificate-invalidation-container',
            'Certificate invalidations section is visible.'
        )
        self.wait_for_element_visibility('#invalidate-certificate', 'Invalidate Certificate button is visible')

    def refresh(self):
        """
        Refresh Certificates Page and wait for the page to load completely.
        """
        self.browser.refresh()
        self.wait_for_page()

    def is_browser_on_page(self):
        return self.q(css='[data-section=certificates].active-section').present

    def get_selector(self, css_selector):
        """
        Makes query selector by pre-pending certificates section
        """
        return self.q(css=' '.join([self.PAGE_SELECTOR, css_selector]))

    def add_certificate_exception(self, student, free_text_note):
        """
        Add Certificate Exception for 'student'.
        """
        self.wait_for_element_visibility('#add-exception', 'Add Exception button is visible')

        self.get_selector('#certificate-exception').fill(student)
        self.get_selector('#notes').fill(free_text_note)
        self.get_selector('#add-exception').click()

        self.wait_for_ajax()
        self.wait_for(
            lambda: student in self.get_selector('div.white-listed-students table tr:last-child td').text,
            description='Certificate Exception added to list'
        )

    def remove_first_certificate_exception(self):
        """
        Remove Certificate Exception from the white list.
        """
        self.wait_for_element_visibility('#add-exception', 'Add Exception button is visible')
        self.get_selector('div.white-listed-students table tr td .delete-exception').first.click()
        self.wait_for_ajax()

    def click_generate_certificate_exceptions_button(self):  # pylint: disable=invalid-name
        """
        Click 'Generate Exception Certificates' button in 'Certificates Exceptions' section
        """
        self.get_selector('#generate-exception-certificates').click()

    def fill_user_name_field(self, student):
        """
        Fill username/email field with given text
        """
        self.get_selector('#certificate-exception').fill(student)

    def click_add_exception_button(self):
        """
        Click 'Add Exception' button in 'Certificates Exceptions' section
        """
        self.get_selector('#add-exception').click()

    def add_certificate_invalidation(self, student, notes):
        """
        Add certificate invalidation for 'student'.
        """
        self.wait_for_element_visibility('#invalidate-certificate', 'Invalidate Certificate button is visible')

        self.get_selector('#certificate-invalidation-user').fill(student)
        self.get_selector('#certificate-invalidation-notes').fill(notes)
        self.get_selector('#invalidate-certificate').click()

        self.wait_for_ajax()
        self.wait_for(
            lambda: student in self.get_selector('div.invalidation-history table tr:last-child td').text,
            description='Certificate invalidation added to list.'
        )

    def remove_first_certificate_invalidation(self):
        """
        Remove certificate invalidation from the invalidation list.
        """
        self.wait_for_element_visibility('#invalidate-certificate', 'Invalidate Certificate button is visible')
        self.get_selector('div.invalidation-history table tr td .re-validate-certificate').first.click()
        self.wait_for_ajax()

    def fill_certificate_invalidation_user_name_field(self, student):  # pylint: disable=invalid-name
        """
        Fill username/email field with given text
        """
        self.get_selector('#certificate-invalidation-user').fill(student)

    def click_invalidate_certificate_button(self):
        """
        Click 'Invalidate Certificate' button in 'certificates invalidations' section
        """
        self.get_selector('#invalidate-certificate').click()

    @property
    def generate_certificates_button(self):
        """
        Returns the "Generate Certificates" button.
        """
        return self.get_selector('#btn-start-generating-certificates')

    @property
    def generate_certificates_disabled_button(self):  # pylint: disable=invalid-name
        """
        Returns the disabled state of button
        """
        return self.get_selector('#disabled-btn-start-generating-certificates')

    @property
    def certificate_generation_status(self):
        """
        Returns certificate generation status message container.
        """
        return self.get_selector('div.certificate-generation-status')

    @property
    def pending_tasks_section(self):
        """
        Returns the "Pending Instructor Tasks" section.
        """
        return self.get_selector('div.running-tasks-container')

    @property
    def certificate_exceptions_section(self):
        """
        Returns the "Certificate Exceptions" section.
        """
        return self.get_selector('div.certificate-exception-container')

    @property
    def last_certificate_exception(self):
        """
        Returns the Last Certificate Exception in Certificate Exceptions list in "Certificate Exceptions" section.
        """
        return self.get_selector('div.white-listed-students table tr:last-child td')

    @property
    def message(self):
        """
        Returns the Message (error/success) in "Certificate Exceptions" section.
        """
        return self.get_selector('.certificate-exception-container div.message')

    @property
    def last_certificate_invalidation(self):
        """
        Returns last certificate invalidation from "Certificate Invalidations" section.
        """
        return self.get_selector('div.certificate-invalidation-container table tr:last-child td')

    @property
    def certificate_invalidation_message(self):  # pylint: disable=invalid-name
        """
        Returns the message (error/success) in "Certificate Invalidation" section.
        """
        return self.get_selector('.certificate-invalidation-container div.message')
