"""
Staff view of courseware
"""
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms.courseware import CoursewarePage


class StaffPage(CoursewarePage):
    """
    View of courseware pages while logged in as course staff
    """

    url = None
    PREVIEW_MENU_CSS = '.preview-menu'
    VIEW_MODE_OPTIONS_CSS = '.preview-menu .action-preview-select option'

    def is_browser_on_page(self):
        if not super(StaffPage, self).is_browser_on_page():
            return False
        return self.q(css=self.PREVIEW_MENU_CSS).present

    @property
    def staff_view_mode(self):
        """
        Return the currently chosen view mode, e.g. "Staff", "Student" or a content group.
        """
        return self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.is_selected()).first.text[0]

    def set_staff_view_mode(self, view_mode):
        """
        Set the current view mode, e.g. "Staff", "Student" or a content group.
        """
        self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.text.strip() == view_mode).first.click()
        self.wait_for_ajax()

    def set_staff_view_mode_specific_student(self, username_or_email):
        """
        Set the current preview mode to "Specific Student" with the given username or email
        """
        required_mode = "Specific student"
        if self.staff_view_mode != required_mode:
            self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.text == required_mode).first.click()
        # Use a script here because .clear() + .send_keys() triggers unwanted behavior if a username is already set
        self.browser.execute_script(
            '$(".action-preview-username").val("{}").blur().change();'.format(username_or_email)
        )
        self.wait_for_ajax()

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
        self.q(css='.staff-modal .staff-debug-reset').click()

    def delete_state(self, user=None):
        """
        This delete's a student's state for the problem
        """
        if user:
            self.q(css='input[id^=sd_fu_]').fill(user)
        self.q(css='.staff-modal .staff-debug-sdelete').click()

    def rescore(self, user=None):
        """
        This clicks on the reset attempts link with an optionally
        specified user.
        """
        if user:
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='.staff-modal .staff-debug-rescore').click()

    @property
    def idash_msg(self):
        """
        Returns the value of #idash_msg
        """
        self.wait_for_ajax()
        return self.q(css='#idash_msg').text
