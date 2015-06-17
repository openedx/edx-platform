from bok_choy.page_object import PageObject

class ReadTheDocsPDF(PageObject):
    """
    Read the docs pdf
    """

    url = None

    def is_browser_on_page(self):
        return 'edx-partner-course-staff.pdf' in self.browser.title.lower()