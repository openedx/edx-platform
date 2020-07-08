# -*- coding: utf-8 -*-
"""
Student dashboard page.
"""


from bok_choy.page_object import PageObject

from common.test.acceptance.pages.lms import BASE_URL


class DashboardPage(PageObject):
    """
    Student dashboard, where the student can view
    courses she/he has registered for.
    """
    url = "{base}/dashboard".format(base=BASE_URL)

    def is_browser_on_page(self):
        return self.q(css='.my-courses').present

    def get_courses(self):
        """
        Get all courses shown in the dashboard
        """
        return self.q(css='ul.listing-courses .course-item')
