from bok_choy.page_object import PageObject
from studiohelp import StudioHelpPage
from readthedocspdf import ReadTheDocsPDF
from courseoutlinepage import CourseOutlinePage
from edgehelp import EdgeHelpPage

class MyCoursesPage(PageObject):
    """
    My Courses Page after logging in
    """

    url = None

    def is_browser_on_page(self):
        return 'studio home' in self.browser.title.lower()

    def click_edx_image(self):
        # Clicks on the EDX image

        self.q(css='h1.branding a img').first.click()
        MyCoursesPage(self.browser).wait_for_page()

    def click_help_link(self):
        # Clicks on pages Help Link

        self.q(css='h3.title span.label a').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        StudioHelpPage(self.browser).wait_for_page()

    def click_mycourses_link(self):
        # Clicks on My Courses link under Account User Name

        self.q(css='span.account-username').first.click()
        self.q(css='.nav-account-dashboard a').first.click()
        MyCoursesPage(self.browser).wait_for_page()

    def click_email_staff_to_create(self):
        # Clicks on Email staff to create course link

        return self.q(css='.nav-actions > ul:nth-child(2) > li:nth-child(1) > a:nth-child(1)').attrs('href')[0]

    def click_getting_started_with_studio_link(self):
        # Clicks on Getting Started with edX pages link

        self.q(css='ol.list-actions > li:nth-child(1) > a:nth-child(1)').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        StudioHelpPage(self.browser).wait_for_page()

    def click_request_help_with_studio_link(self):
        # Clicks on Request help with edX pages link

        self.q(css='.action-primary[title="Use our feedback tool, Tender, to request help"]').first.click()
        EdgeHelpPage(self.browser).wait_for_page()

    def click_staff_to_help_create_course(self):
        # Clicks edX staff to help you create a course link

        return self.q(css='div.bit p a').attrs('href')[0]

    def click_contact_us_link(self):
        # Click Contact Us link

        self.q(css='.show-tender').first.click()
        self.wait_for_element_presence('#tender_frame', 'Help and Support pop up not found')

    def click_looking_help_with_studio(self):
        # Click Looking for help with studio link then Building and Running an edX course

        self.q(css='.copy-show.is-shown').first.click()
        self.q(css='.js-help-pdf > a:nth-child(1)').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        ReadTheDocsPDF(self.browser).wait_for_page()

    def click_manual_smoke_test_course_1_auto(self):
        # Click Manual Smoke Test Course 1 - Auto (our automation course)

        self.q(css='.course-title').filter(lambda el:el.text=='Manual Smoke Test Course 1 - Auto').click()
        CourseOutlinePage(self.browser).wait_for_page()
