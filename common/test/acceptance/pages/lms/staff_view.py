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
