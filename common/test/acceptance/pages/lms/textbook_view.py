"""
Course Textbooks page.
"""

from .course_page import CoursePage
from bok_choy.promise import EmptyPromise


class TextbookViewPage(CoursePage):
    """
    Course Textbooks page.
    """

    url_path = "pdfbook/0/"

    def is_browser_on_page(self):
        return self.q(css='.book-sidebar').present

    def switch_to_pdf_frame(self, test):
        """
        Waits for pdf frame to load, then switches driver to the frame
        """
        EmptyPromise(
            lambda: self.q(css='iframe').present, "Iframe loaded"
        ).fulfill()

        driver = test.get_web_driver()
        driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
