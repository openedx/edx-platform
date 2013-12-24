from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class ExportPage(PageObject):
    """
    Course Export page.
    """

    @property
    def name(self):
        return "studio.export"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self, course_id=None):
        if course_id is None:
            raise NotImplemented("Must provide a course ID")

        elements = course_id.split('.')

        # You need at least 3 parts to a course ID: org, number, and run
        if len(elements) < 3:
            raise NotImplemented("Invalid course ID: '{}'".format(course_id))

        course_run = elements[-1]

        return "{0}/export/{1}/branch/draft/block/{2}".format(
            BASE_URL, course_id, course_run
        )

    def is_browser_on_page(self):
        return self.is_css_present('body.view-export')
