# coding: utf-8
"""
Course Schedule and Details Settings page.
"""
from __future__ import unicode_literals
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .utils import press_the_notification_button


class SettingsPage(CoursePage):
    """
    Course Schedule and Details Settings page.
    """

    url_path = "settings/details"

    ################
    # Helpers
    ################
    def is_browser_on_page(self):
        return self.q(css='body.view-settings').present

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
        license_types_css = "section.license ul.license-types li.license-type"
        self.wait_for_element_presence(
            license_types_css,
            "license type buttons are present",
        )
        selected = self.q(css=license_types_css + " button.is-selected")
        if selected.is_present():
            return selected.text[0]

        # Look for the license text that will be displayed by default,
        # if no button is yet explicitly selected
        license_text = self.q(css='section.license span.license-text')
        if license_text.is_present():
            return license_text.text[0]
        return None

    @course_license.setter
    def course_license(self, license_name):
        """
        Sets the course license to the given license_name
        (str, "All Rights Reserved" or "Creative Commons")
        """
        license_types_css = "section.license ul.license-types li.license-type"
        self.wait_for_element_presence(
            license_types_css,
            "license type buttons are present",
        )
        button_xpath = (
            "//section[contains(@class, 'license')]"
            "//ul[contains(@class, 'license-types')]"
            "//li[contains(@class, 'license-type')]"
            "//button[contains(text(),'{license_name}')]"
        ).format(license_name=license_name)
        button = self.q(xpath=button_xpath)
        if not button.present:
            raise Exception("Invalid license name: {name}".format(name=license_name))
        button.click()

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
        self.wait_for_ajax()
