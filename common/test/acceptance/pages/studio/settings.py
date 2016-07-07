# coding: utf-8
"""
Course Schedule and Details Settings page.
"""
from __future__ import unicode_literals
import os
from bok_choy.promise import EmptyPromise
from bok_choy.javascript import requirejs

from .course_page import CoursePage
from .users import wait_for_ajax_or_reload
from .utils import press_the_notification_button


@requirejs('js/factories/settings')
class SettingsPage(CoursePage):
    """
    Course Schedule and Details Settings page.
    """

    url_path = "settings/details"
    upload_image_browse_button_selector = 'form.upload-dialog input[type=file]'
    upload_image_upload_button_selector = '.modal-actions li:nth-child(1) a'
    upload_image_popup_window_selector = '.assetupload-modal'

    ################
    # Helpers
    ################
    def is_browser_on_page(self):
        wait_for_ajax_or_reload(self.browser)
        return self.q(css='body.view-settings').visible

    def wait_for_require_js(self):
        """
        Wait for require-js to load javascript files.
        """
        if hasattr(self, 'wait_for_js'):
            self.wait_for_js()  # pylint: disable=no-member

    def wait_for_jquery_value(self, jquery_element, value):
        """
        Use jQuery to obtain the element's value.
        This is useful for when jQuery performs functions towards the
        end of the page load. (In other words, waiting for jquery to
        load is not enough; we need to also query values that it has
        injected onto the page to ensure it's done.)
        """
        self.wait_for(
            lambda: self.browser.execute_script(
                "return $('{ele}').val();".format(ele=jquery_element)) == '{val}'.format(val=value),
            'wait for jQuery to finish loading data on page.'
        )

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

    def get_elements(self, css_selector):
        self.wait_for_element_presence(
            css_selector,
            'Elements matching "{}" selector are present'.format(css_selector)
        )
        results = self.q(css=css_selector)
        return results

    def get_element(self, css_selector):
        results = self.get_elements(css_selector=css_selector)
        return results[0] if results else None

    ################
    # Properties
    ################
    @property
    def pre_requisite_course_options(self):
        """
        Returns the pre-requisite course drop down field options.
        """
        self.wait_for_element_visibility(
            '#pre-requisite-course',
            'Prerequisite course element is available'
        )
        return self.get_elements('#pre-requisite-course')

    @property
    def entrance_exam_field(self):
        """
        Returns the enable entrance exam checkbox.
        """
        self.wait_for_element_visibility(
            '#entrance-exam-enabled',
            'Entrance exam checkbox is available'
        )
        return self.get_element('#entrance-exam-enabled')

    @property
    def alert_confirmation_title(self):
        """
        Returns the alert confirmation element, which contains text
        such as 'Your changes have been saved.'
        """
        self.wait_for_element_visibility(
            '#alert-confirmation-title',
            'Alert confirmation title element is available'
        )
        return self.get_element('#alert-confirmation-title')

    @property
    def course_license(self):
        """
        Property. Returns the text of the license type for the course
        ("All Rights Reserved" or "Creative Commons")
        """
        license_types_css = ".license ul.license-types li.license-type"
        self.wait_for_element_presence(
            license_types_css,
            "license type buttons are present",
        )
        selected = self.q(css=license_types_css + " button.is-selected")
        if selected.is_present():
            return selected.text[0]

        # Look for the license text that will be displayed by default,
        # if no button is yet explicitly selected
        license_text = self.q(css='.license span.license-text')
        if license_text.is_present():
            return license_text.text[0]
        return None

    @course_license.setter
    def course_license(self, license_name):
        """
        Sets the course license to the given license_name
        (str, "All Rights Reserved" or "Creative Commons")
        """
        license_types_css = ".license ul.license-types li.license-type"
        self.wait_for_element_presence(
            license_types_css,
            "license type buttons are present",
        )
        button_xpath = (
            "//div[contains(@class, 'license')]"
            "//ul[contains(@class, 'license-types')]"
            "//li[contains(@class, 'license-type')]"
            "//button[contains(text(),'{license_name}')]"
        ).format(license_name=license_name)
        button = self.q(xpath=button_xpath)
        if not button.present:
            raise Exception("Invalid license name: {name}".format(name=license_name))
        button.click()

    pacing_css = '.pacing input[type=radio]'

    @property
    def checked_pacing_css(self):
        """CSS for the course pacing button which is currently checked."""
        return self.pacing_css + ':checked'

    @property
    def course_pacing(self):
        """
        Returns the label text corresponding to the checked pacing radio button.
        """
        self.wait_for_element_presence(self.checked_pacing_css, 'course pacing controls present and rendered')
        checked = self.q(css=self.checked_pacing_css).results[0]
        checked_id = checked.get_attribute('id')
        return self.q(css='label[for={checked_id}]'.format(checked_id=checked_id)).results[0].text

    @course_pacing.setter
    def course_pacing(self, pacing):
        """
        Sets the course to either self-paced or instructor-paced by checking
        the appropriate radio button.
        """
        self.wait_for_element_presence(self.checked_pacing_css, 'course pacing controls present')
        self.q(xpath="//label[contains(text(), '{pacing}')]".format(pacing=pacing)).click()

    @property
    def course_pacing_disabled_text(self):
        """
        Return the message indicating that course pacing cannot be toggled.
        """
        return self.q(css='#course-pace-toggle-tip').results[0].text

    def course_pacing_disabled(self):
        """
        Return True if the course pacing controls are disabled; False otherwise.
        """
        self.wait_for_element_presence(self.checked_pacing_css, 'course pacing controls present')
        statuses = self.q(css=self.pacing_css).map(lambda e: e.get_attribute('disabled')).results
        return all((s == 'true' for s in statuses))

    ################
    # Waits
    ################
    def wait_for_prerequisite_course_options(self):
        """
        Ensure the pre_requisite_course_options dropdown selector is displayed
        """
        EmptyPromise(
            lambda: self.q(css="#pre-requisite-course").present,
            'Prerequisite course dropdown selector is displayed'
        ).fulfill()

    ################
    # Clicks
    ################

    ################
    # Workflows
    ################

    def require_entrance_exam(self, required=True):
        """
        Set the entrance exam requirement via the checkbox.
        """
        checkbox = self.entrance_exam_field
        selected = checkbox.is_selected()
        if required and not selected:
            checkbox.click()
            self.wait_for_element_visibility(
                '#entrance-exam-minimum-score-pct',
                'Entrance exam minimum score percent is visible'
            )
        if not required and selected:
            checkbox.click()
            self.wait_for_element_invisibility(
                '#entrance-exam-minimum-score-pct',
                'Entrance exam minimum score percent is invisible'
            )

    def save_changes(self, wait_for_confirmation=True):
        """
        Clicks save button, waits for confirmation unless otherwise specified
        """
        press_the_notification_button(self, "save")
        if wait_for_confirmation:
            self.wait_for_element_visibility(
                '#alert-confirmation-title',
                'Save confirmation message is visible'
            )

    def refresh_page(self, wait_for_confirmation=True):
        """
        Reload the page.
        """
        self.browser.refresh()
        if wait_for_confirmation:
            EmptyPromise(
                lambda: self.q(css='body.view-settings').present,
                'Page is refreshed'
            ).fulfill()
        self.wait_for_require_js()
        self.wait_for_ajax()

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

    def upload_image(self, upload_btn_selector, file_to_upload):
        """
        Upload image specified by image_selector and file_to_upload
        """

        # wait for upload button
        self.wait_for_element_visibility(upload_btn_selector, 'upload button is present')

        self.q(css=upload_btn_selector).results[0].click()

        # wait for popup
        self.wait_for_element_presence(self.upload_image_popup_window_selector, 'upload dialog is present')

        # upload image
        filepath = SettingsPage.get_asset_path(file_to_upload)
        self.q(css=self.upload_image_browse_button_selector).results[0].send_keys(filepath)
        self.q(css=self.upload_image_upload_button_selector).results[0].click()

        # wait for popup closed
        self.wait_for_element_absence(self.upload_image_popup_window_selector, 'upload dialog is hidden')

    def get_uploaded_image_path(self, image_selector):
        """
        Returns the uploaded image path
        """

        return self.q(css=image_selector).attrs('src')[0]
