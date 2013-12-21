from bok_choy.page_object import PageObject
from ..lms import BASE_URL


class DashboardPage(PageObject):
    """
    Student dashboard, where the student can view
    courses she/he has registered for.
    """

    @property
    def name(self):
        return "lms.dashboard"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self, **kwargs):
        return BASE_URL + "/dashboard"

    def is_browser_on_page(self):
        return self.is_css_present('section.my-courses')

    def available_courses(self):
        """
        Return list of the names of available courses (e.g. "999 edX Demonstration Course")
        """
        return self.css_text('section.info > hgroup > h3 > a')

    def view_course(self, course_id):
        """
        Go to the course with `course_id` (e.g. edx/Open_DemoX/edx_demo_course)
        """
        link_css = self._link_css(course_id)

        if link_css is not None:
            self.css_click(link_css)
        else:
            msg = "No links found for course {0}".format(course_id)
            self.warning(msg)

    def _link_css(self, course_id):

        # Get the link hrefs for all courses
        all_links = self.css_map('a.enter-course', lambda el: el['href'])

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
