"""
Wiki tab on courses
"""


from common.test.acceptance.pages.lms.course_page import CoursePage
from common.test.acceptance.pages.studio.utils import get_codemirror_value, type_in_codemirror


class CourseWikiPage(CoursePage):
    """
    Course wiki navigation and objects.
    """

    url_path = "wiki"

    def is_browser_on_page(self):
        """
        Browser is on the wiki page if the wiki breadcrumb is present
        """
        return self.q(css='.breadcrumb').present

    def open_editor(self):
        """
        Display the editor for a wiki article.
        """
        edit_button = self.q(css='.fa-pencil')
        edit_button.click()

    def show_history(self):
        """
        Show the change history for a wiki article.
        """
        edit_button = self.q(css='.fa-clock-o')
        edit_button.click()

    def show_children(self):
        """
        Show the children of a wiki article.
        """
        children_link = self.q(css='.see-children>a')
        children_link.click()

    @property
    def article_name(self):
        """
        Return the name of the article
        """
        return str(self.q(css='.main-article .entry-title').text[0])


class CourseWikiSubviewPage(CoursePage):  # pylint: disable=abstract-method
    """ Abstract base page for subviews within the wiki. """

    def __init__(self, browser, course_id, course_info):
        """
        Course ID is currently of the form "edx/999/2013_Spring"
        but this format could change.
        """
        super(CourseWikiSubviewPage, self).__init__(browser, course_id)
        self.course_id = course_id
        self.course_info = course_info
        self.article_name = "{org}.{course_number}.{course_run}".format(
            org=self.course_info['org'],
            course_number=self.course_info['number'],
            course_run=self.course_info['run']
        )


class CourseWikiEditPage(CourseWikiSubviewPage):
    """
    Editor page
    """

    @property
    def url_path(self):
        """
        Construct a URL to the page within the course.
        """
        return "/wiki/" + self.article_name + "/_edit"

    def is_browser_on_page(self):
        """
        The wiki page editor
        """
        return self.q(css='.CodeMirror-scroll').present

    def replace_wiki_content(self, content):
        """
        Editor must be open already. This will replace any content in the editor
        with new content
        """
        type_in_codemirror(self, 0, content)

    def get_wiki_editor_content(self):
        """
        Returns the content currently in the wiki editor.
        """

        return get_codemirror_value(self, 0)

    def save_wiki_content(self):
        """
        When the editor is open, click save
        """
        self.q(css='button[name="save"]').click()
        self.wait_for_element_presence('.alert-success', 'wait for the article to be saved')


class CourseWikiHistoryPage(CourseWikiSubviewPage):
    """
    Course wiki change history page.
    """

    def is_browser_on_page(self):
        """
        Return if the browser is on the history page.
        """
        return self.q(css='section.history').present

    @property
    def url_path(self):
        """
        Construct a URL to the page within the course.
        """
        return "/wiki/" + self.article_name + "/_history"


class CourseWikiChildrenPage(CourseWikiSubviewPage):
    """
    Course wiki "All Children" page.
    """

    def is_browser_on_page(self):
        """
        Return if the browser is on the wiki children page (which contains a search widget).
        """
        return self.q(css='.form-search').present

    @property
    def url_path(self):
        """
        Construct a URL to the page within the course.
        """
        return "/wiki/" + self.article_name + "/_dir"
