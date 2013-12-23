from bok_choy.page_object import PageObject
from ..lms import BASE_URL


class CourseInfoPage(PageObject):
    """
    Course info.
    """

    @property
    def name(self):
        return "lms.course_info"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self, course_id=None):
        """
        Go directly to the course info page for `course_id`.
        (e.g. "edX/Open_DemoX/edx_demo_course")
        """
        return BASE_URL + "/courses/" + course_id + "/info"

    def is_browser_on_page(self):
        return self.is_css_present('section.updates')

    def num_updates(self):
        """
        Return the number of updates on the page.
        """
        return self.css_count('section.updates ol li')

    def handout_links(self):
        """
        Return a list of handout assets links.
        """
        return self.css_map('section.handouts ol li a', lambda el: el['href'])
