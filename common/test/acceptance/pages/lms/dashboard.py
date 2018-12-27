# -*- coding: utf-8 -*-
"""
Student dashboard page.
"""
from bok_choy.page_object import PageObject
from opaque_keys.edx.keys import CourseKey

from common.test.acceptance.pages.lms import BASE_URL


class DashboardPage(PageObject):
    """
    Student dashboard, where the student can view
    courses she/he has registered for.
    """
    url = "{base}/dashboard".format(base=BASE_URL)

    def is_browser_on_page(self):
        return self.q(css='.my-courses').present

    @property
    def current_courses_text(self):
        """
        This is the title label for the section of the student dashboard that
        shows all the courses that the student is enrolled in.
        The string displayed is defined in lms/templates/dashboard.html.
        """
        text_items = self.q(css='#my-courses').text
        if len(text_items) > 0:
            return text_items[0]
        else:
            return ""

    @property
    def available_courses(self):
        """
        Return list of the names of available courses (e.g. "999 edX Demonstration Course")
        """
        def _get_course_name(el):
            return el.text

        return self.q(css='h3.course-title > a').map(_get_course_name).results

    @property
    def banner_text(self):
        """
        Return the text of the banner on top of the page, or None if
        the banner is not present.
        """
        message = self.q(css='div.wrapper-msg')
        if message.present:
            return message.text[0]
        return None

    def get_enrollment_mode(self, course_name):
        """Get the enrollment mode for a given course on the dashboard.

        Arguments:
            course_name (str): The name of the course whose mode should be retrieved.

        Returns:
            String, indicating the enrollment mode for the course corresponding to
            the provided course name.

        Raises:
            Exception, if no course with the provided name is found on the dashboard.
        """
        # Filter elements by course name, only returning the relevant course item
        course_listing = self.q(css=".course").filter(lambda el: course_name in el.text).results

        if course_listing:
            # There should only be one course listing for the provided course name.
            # Since 'ENABLE_VERIFIED_CERTIFICATES' is true in the Bok Choy settings, we
            # can expect two classes to be present on <article> elements, one being 'course'
            # and the other being the enrollment mode.
            enrollment_mode = course_listing[0].get_attribute('class').split('course ')[1]
        else:
            raise Exception("No course named {} was found on the dashboard".format(course_name))

        return enrollment_mode

    def upgrade_enrollment(self, course_name, upgrade_page):
        """Interact with the upgrade button for the course with the provided name.

        Arguments:
            course_name (str): The name of the course whose mode should be checked.
            upgrade_page (PageObject): The page to wait on after clicking the upgrade button. Importing
                the definition of PaymentAndVerificationFlow results in a circular dependency.

        Raises:
            Exception, if no enrollment corresponding to the provided course name appears
                on the dashboard.
        """
        # Filter elements by course name, only returning the relevant course item
        course_listing = self.q(css=".course").filter(lambda el: course_name in el.text).results

        if course_listing:
            # There should only be one course listing corresponding to the provided course name.
            el = course_listing[0]

            # Click the upgrade button
            el.find_element_by_css_selector('#upgrade-to-verified').click()

            upgrade_page.wait_for_page()
        else:
            raise Exception("No enrollment for {} is visible on the dashboard.".format(course_name))

    def view_course(self, course_id):
        """
        Go to the course with `course_id` (e.g. edx/Open_DemoX/edx_demo_course)
        """
        link_css = self._link_css(course_id)

        if link_css is not None:
            self.q(css=link_css).first.click()
        else:
            msg = "No links found for course {0}".format(course_id)
            self.warning(msg)

    def _link_css(self, course_id):
        """
        Return a CSS selector for the link to the course with `course_id`.
        """
        # Get the link hrefs for all courses
        all_links = self.q(css='a.enter-course').map(lambda el: el.get_attribute('href')).results

        # Search for the first link that matches the course id
        link_index = None
        for index in range(len(all_links)):
            if course_id in all_links[index]:
                link_index = index
                break

        if link_index is not None:
            return "a.enter-course:nth-of-type({0})".format(link_index + 1)
        else:
            return None

    def view_course_unenroll_dialog_message(self, course_id):
        """
        Go to the course unenroll dialog message for `course_id` (e.g. edx/Open_DemoX/edx_demo_course)
        """
        div_index = self.get_course_actions_link_css(course_id)
        button_link_css = "#actions-dropdown-link-{}".format(div_index)
        unenroll_css = "#unenroll-{}".format(div_index)

        if button_link_css is not None:
            self.q(css=button_link_css).first.click()
            self.wait_for_element_visibility(unenroll_css, 'Unenroll message dialog is visible.')
            self.q(css=unenroll_css).first.click()
            self.wait_for_ajax()

            return {
                'track-info': self.q(css='#track-info').html,
                'refund-info': self.q(css='#refund-info').html
            }

        else:
            msg = "No links found for course {0}".format(course_id)
            self.warning(msg)

    def get_course_actions_link_css(self, course_id):
        """
            Return a index for unenroll button with `course_id`.
        """
        # Get the link hrefs for all courses
        all_divs = self.q(css='div.wrapper-action-more').map(lambda el: el.get_attribute('data-course-key')).results

        # Search for the first link that matches the course id
        div_index = None
        for index in range(len(all_divs)):
            if course_id in all_divs[index]:
                div_index = index
                break

        return div_index

    def pre_requisite_message_displayed(self):
        """
        Verify if pre-requisite course messages are being displayed.
        """
        return self.q(css='div.prerequisites > .tip').visible

    def get_course_listings(self):
        """Retrieve the list of course DOM elements"""
        return self.q(css='ul.listing-courses')

    def get_course_social_sharing_widget(self, widget_name):
        """ Retrieves the specified social sharing widget by its classification """
        return self.q(css='a.action-{}'.format(widget_name))

    def get_profile_img(self):
        """ Retrieves the user's profile image """
        return self.q(css='img.user-image-frame')

    def get_courses(self):
        """
        Get all courses shown in the dashboard
        """
        return self.q(css='ul.listing-courses .course-item')

    def get_course_date(self):
        """
        Get course date of the first course from dashboard
        """
        return self.q(css='ul.listing-courses .course-item:first-of-type .info-date-block').first.text[0]

    def click_username_dropdown(self):
        """
        Click username dropdown.
        """
        self.q(css='.toggle-user-dropdown').first.click()

    @property
    def username_dropdown_link_text(self):
        """
        Return list username dropdown links.
        """
        return self.q(css='.dropdown-user-menu a').text

    @property
    def tabs_link_text(self):
        """
        Return the text of all the tabs on the dashboard.
        """
        return self.q(css='.nav-tab a').text

    def click_my_profile_link(self):
        """
        Click on `Profile` link.
        """
        self.q(css='.nav-tab a').nth(1).click()

    def click_account_settings_link(self):
        """
        Click on `Account` link.
        """
        self.q(css='.dropdown-user-menu a').nth(1).click()

    @property
    def language_selector(self):
        """
        return language selector
        """
        self.wait_for_element_visibility(
            '#settings-language-value',
            'Language selector element is available'
        )
        return self.q(css='#settings-language-value')

    def is_course_present(self, course_id):
        """
        Checks whether course is present or not.

        Arguments:
            course_id(str): The unique course id.

        Returns:
            bool: True if the course is present.
        """
        course_number = CourseKey.from_string(course_id).course
        return self.q(
            css='#actions-dropdown-link-0[data-course-number="{}"]'.format(
                course_number
            )
        ).present
