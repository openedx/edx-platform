from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class DashboardPage(PageObject):
    """
    My Courses page in Studio
    """

    @property
    def name(self):
        return "studio.dashboard"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self, course_id=None):
        return BASE_URL + "/course"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-dashboard')
