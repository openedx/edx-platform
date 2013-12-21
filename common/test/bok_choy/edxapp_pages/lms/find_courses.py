from bok_choy.page_object import PageObject
from bok_choy.promise import BrokenPromise
from ..lms import BASE_URL


class FindCoursesPage(PageObject):
    """
    Find courses page (main page of the LMS).
    """

    @property
    def name(self):
        return "lms.find_courses"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        return BASE_URL

    def is_browser_on_page(self):
        return self.browser.title == "edX"

    def course_id_list(self):
        """
        Retrieve the list of available course IDs
        on the page.
        """
        return self.css_map('article.course', lambda el: el['id'])

    def go_to_course(self, course_id):
        """
        Navigate to the course with `course_id`.
        Currently the course id has the form
        edx/999/2013_Spring, but this could change.
        """

        # Try clicking the link directly
        try:
            css = 'a[href="/courses/{0}/about"]'.format(course_id)

            # In most browsers, there are multiple links
            # that match this selector, most without text
            # In IE 10, only the second one works.
            # In IE 9, there is only one link
            if self.css_count(css) > 1:
                index = 1
            else:
                index = 0

            self.css_click(css + ":nth-of-type({0})".format(index))

        # Chrome gives an error that another element would receive the click.
        # So click higher up in the DOM
        except BrokenPromise:
            # We need to escape forward slashes in the course_id
            # to create a valid CSS selector
            course_id = course_id.replace('/', '\/')
            self.css_click('article.course#{0}'.format(course_id))

        # Ensure that we end up on the next page
        self.ui.wait_for_page('lms.course_about')
