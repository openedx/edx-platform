"""
Staff view of courseware
"""
from bok_choy.page_object import PageObject


class StaffPage(PageObject):
    """
    View of courseware pages while logged in as course staff
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='#staffstatus').present

    @property
    def staff_status(self):
        """
        Return the current status, either Staff view or Student view
        """
        return self.q(css='#staffstatus').text[0]

    def open_staff_debug_info(self):
        """
        Open the staff debug window
        Return the page object for it.
        """
        self.q(css='a.instructor-info-action').first.click()
        staff_debug_page = StaffDebugPage(self.browser)
        staff_debug_page.wait_for_page()
        return staff_debug_page

    def answer_problem(self):
        """
        Answers the problem to give state that we can clean
        """
        self.q(css='input.check').first.click()
        self.wait_for_ajax()

    def load_problem_via_ajax(self):
        """
        Load problem via ajax by clicking next.
        """
        self.q(css="li.next").click()
        self.wait_for_ajax()


class StaffDebugPage(PageObject):
    """
    Staff Debug modal
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='section.staff-modal').present

    def reset_attempts(self, user=None):
        """
        This clicks on the reset attempts link with an optionally
        specified user.
        """
        if user:
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='section.staff-modal a.staff-debug-reset').click()

    def delete_state(self, user=None):
        """
        This delete's a student's state for the problem
        """
        if user:
            self.q(css='input[id^=sd_fu_]').fill(user)
        self.q(css='section.staff-modal a.staff-debug-sdelete').click()

    def rescore(self, user=None):
        """
        This clicks on the reset attempts link with an optionally
        specified user.
        """
        if user:
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='section.staff-modal a.staff-debug-rescore').click()

    @property
    def idash_msg(self):
        """
        Returns the value of #idash_msg
        """
        self.wait_for_ajax()
        return self.q(css='#idash_msg').text
