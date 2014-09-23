# -*- coding: utf-8 -*-
"""
Student dashboard page.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from . import BASE_URL


class DashboardPage(PageObject):
    """
    Student dashboard, where the student can view
    courses she/he has registered for.
    """

    url = BASE_URL + "/dashboard"

    def is_browser_on_page(self):
        return self.q(css='section.my-courses').present

    @property
    def courses_text(self):
        text_items = self.q(css='section#my-courses span.my-courses-title-label').text
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
            # The first component in the link text is the course number
            _, course_name = el.text.split(' ', 1)
            return course_name

        return self.q(css='section.info > hgroup > h3 > a').map(_get_course_name).results

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

    def change_language(self, code):
        """
        Change the language on the dashboard to the language corresponding with `code`.
        """
        self.q(css=".edit-language").first.click()
        self.q(css='select[name="language"] option[value="{}"]'.format(code)).first.click()
        self.q(css="#submit-lang").first.click()

        # Clicking the submit-lang button does a jquery ajax post, so make sure that
        # has completed before continuing on.
        self.wait_for_ajax()

        self._changed_lang_promise(code).fulfill()

    def _changed_lang_promise(self, code):
        def _check_func():
            language_is_selected = self.q(css='select[name="language"] option[value="{}"]'.format(code)).selected
            modal_is_visible = self.q(css='section#change_language.modal').visible
            return (language_is_selected and not modal_is_visible)
        return EmptyPromise(_check_func, "language changed and modal hidden")
