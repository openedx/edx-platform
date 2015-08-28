from bok_choy.page_object import PageObject

class CoursewarePage(PageObject):
    """
    Courseware Page
    """

    url = None

    def is_browser_on_page(self):
        # Check if Login page appears then Login first

        if 'log into' in self.browser.title:
            self.q(css='input#email').fill('raees.chachar@edx.org')
            self.q(css='input#password').fill('edx')
            self.q(css='button#submit').first.click()
            self.wait_for_element_presence('body.courseware', 'On Courseware page')
            return self.q(css='body.courseware').present
        else:
            return self.q(css='body.courseware').present
