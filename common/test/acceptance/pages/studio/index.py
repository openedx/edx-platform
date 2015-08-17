"""
Studio Home page
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class DashboardPage(PageObject):
    """
    Studio Home page
    """

    url = BASE_URL + "/course/"

    def is_browser_on_page(self):
        return self.q(css='body.view-dashboard').present

    @property
    def course_runs(self):
        """
        The list of course run metadata for all displayed courses
        Returns an empty string if there are none
        """
        return self.q(css='.course-run>.value').text

    @property
    def has_processing_courses(self):
        return self.q(css='.courses-processing').present

    def create_rerun(self, display_name):
        """
        Clicks the create rerun link of the course specified by display_name.
        """
        name = self.q(css='.course-title').filter(lambda el: el.text == display_name)[0]
        name.find_elements_by_xpath('../..')[0].find_elements_by_class_name('rerun-button')[0].click()

    def click_course_run(self, run):
        """
        Clicks on the course with run given by run.
        """
        self.q(css='.course-run .value').filter(lambda el: el.text == run)[0].click()

    def has_new_library_button(self):
        """
        (bool) is the "New Library" button present?
        """
        return self.q(css='.new-library-button').present

    def click_new_library(self):
        """
        Click on the "New Library" button
        """
        self.q(css='.new-library-button').click()

    def is_new_library_form_visible(self):
        """
        Is the new library form visisble?
        """
        return self.q(css='.wrapper-create-library').visible

    def fill_new_library_form(self, display_name, org, number):
        """
        Fill out the form to create a new library.
        Must have called click_new_library() first.
        """
        field = lambda fn: self.q(css='.wrapper-create-library #new-library-{}'.format(fn))
        field('name').fill(display_name)
        field('org').fill(org)
        field('number').fill(number)

    def is_new_library_form_valid(self):
        """
        IS the new library form ready to submit?
        """
        return (
            self.q(css='.wrapper-create-library .new-library-save:not(.is-disabled)').present and
            not self.q(css='.wrapper-create-library .wrap-error.is-shown').present
        )

    def submit_new_library_form(self):
        """
        Submit the new library form.
        """
        self.q(css='.wrapper-create-library .new-library-save').click()

    def list_courses(self):
        """
        List all the courses found on the page's list of libraries.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        course_tab_link = self.q(css='#course-index-tabs .courses-tab a')
        if course_tab_link:
            course_tab_link.click()
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'org': element.find_element_by_css_selector('.course-org .value').text,
            'number': element.find_element_by_css_selector('.course-num .value').text,
            'run': element.find_element_by_css_selector('.course-run .value').text,
            'url': element.find_element_by_css_selector('a.course-link').get_attribute('href'),
        }
        return self.q(css='.courses li.course-item').map(div2info).results

    def list_libraries(self):
        """
        Click the tab to display the available libraries, and return detail of them.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        self.q(css='#course-index-tabs .libraries-tab a').click()
        if self.q(css='.list-notices.libraries-tab').present:
            # No libraries are available.
            self.wait_for_element_visibility('.libraries-tab .new-library-button', "Switch to library tab")
            return []
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'org': element.find_element_by_css_selector('.course-org .value').text,
            'number': element.find_element_by_css_selector('.course-num .value').text,
            'url': element.find_element_by_css_selector('a.library-link').get_attribute('href'),
        }
        self.wait_for_element_visibility('.libraries li.course-item', "Switch to library tab")
        return self.q(css='.libraries li.course-item').map(div2info).results

    def has_library(self, **kwargs):
        """
        Does the page's list of libraries include a library matching kwargs?
        """
        for lib in self.list_libraries():
            if all([lib[key] == kwargs[key] for key in kwargs]):
                return True
        return False
