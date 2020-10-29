"""
Staff views of various tabs (e.g. courseware, course home)
"""


from bok_choy.page_object import PageObject

from common.test.acceptance.pages.lms.courseware import CoursewarePage


class StaffPreviewPage(PageObject):
    """
    Handles Staff Preview for any course tab that provides that functionality.
    """
    url = None

    PREVIEW_MENU_CSS = '.preview-menu'
    VIEW_MODE_OPTIONS_CSS = '.preview-menu .action-preview-select option'

    def __init__(self, browser, parent_page=None):
        """
        Initialize the staff preview page.

        This page can either be used as a subclass, or a child of a parent page.

        Arguments:
            browser: The selenium browser.
            parent_page: None if this is being used as a subclass.  Otherwise,
                the parent_page the contains this staff preview page fragment.
        """
        super(StaffPreviewPage, self).__init__(browser)
        self.parent_page = parent_page

    def is_browser_on_page(self):
        if self.parent_page and not self.parent_page.is_browser_on_page:
            return False
        return self.q(css=self.PREVIEW_MENU_CSS).present

    @property
    def staff_view_mode(self):
        """
        Return the currently chosen view mode, e.g. "Staff", "Learner" or a content group.
        """
        return self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.is_selected()).first.text[0]

    def set_staff_view_mode(self, view_mode):
        """
        Set the current view mode, e.g. "Staff", "Learner" or a content group.
        """
        self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.text.strip() == view_mode).first.click()
        self.wait_for_ajax()

    def set_staff_view_mode_specific_student(self, username_or_email):
        """
        Set the current preview mode to "Specific learner" with the given username or email
        """
        required_mode = "Specific learner"
        if self.staff_view_mode != required_mode:
            self.q(css=self.VIEW_MODE_OPTIONS_CSS).filter(lambda el: el.text == required_mode).first.click()
        # Use a script here because .clear() + .send_keys() triggers unwanted behavior if a username is already set
        self.browser.execute_script(
            '$(".action-preview-username").val("{}").blur().change();'.format(username_or_email)
        )
        self.wait_for_ajax()


class StaffCoursewarePage(CoursewarePage, StaffPreviewPage):
    """
    View of courseware pages while logged in as course staff
    """

    url = None

    def __init__(self, browser, course_id):
        CoursewarePage.__init__(self, browser, course_id)
        StaffPreviewPage.__init__(self, browser)

    def is_browser_on_page(self):
        if not CoursewarePage.is_browser_on_page(self):
            return False
        return StaffPreviewPage.is_browser_on_page(self)

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
        return self.q(css='.staff-modal').present

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
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='.staff-modal .staff-debug-sdelete').first.click()

    def rescore(self, user=None):
        """
        This clicks on the reset attempts link with an optionally
        specified user.
        """
        if user:
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='.staff-modal .staff-debug-rescore').click()

    def rescore_if_higher(self, user=None):
        """
        This clicks on the reset attempts link with an optionally
        specified user.
        """
        if user:
            self.q(css='input[id^=sd_fu_]').first.fill(user)
        self.q(css='.staff-modal .staff-debug-rescore-if-higher').click()

    @property
    def idash_msg(self):
        """
        Returns the value of #idash_msg
        """
        self.wait_for_ajax()
        return self.q(css='#idash_msg').text
