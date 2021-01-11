"""
LMS discussion page
"""


from contextlib import contextmanager

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.lms.course_page import CoursePage


class DiscussionThreadPage(PageObject):
    """
    Discussion thread page
    """
    url = None

    def __init__(self, browser, thread_selector):
        super(DiscussionThreadPage, self).__init__(browser)
        self.thread_selector = thread_selector

    def _find_within(self, selector):
        """
        Returns a query corresponding to the given CSS selector within the scope
        of this thread page
        """
        return self.q(css=self.thread_selector + " " + selector)

    def is_browser_on_page(self):
        return self.q(css=self.thread_selector).visible

    def _get_element_text(self, selector):
        """
        Returns the text of the first element matching the given selector, or
        None if no such element exists
        """
        text_list = self._find_within(selector).text
        return text_list[0] if text_list else None

    def is_element_visible(self, selector):
        """
        Returns true if the element matching the specified selector is visible.

        Args:
            selector (str): The CSS selector that matches the desired element.

        Returns:
            bool: True if the element is visible.

        """
        query = self._find_within(selector)
        return query.present and query.visible

    @contextmanager
    def secondary_action_menu_open(self, ancestor_selector):
        """
        Given the selector for an ancestor of a secondary menu, return a context
        manager that will open and close the menu
        """
        self.wait_for_ajax()
        self._find_within(ancestor_selector + " .action-more").click()
        EmptyPromise(
            lambda: self.is_element_visible(ancestor_selector + " .actions-dropdown"),
            "Secondary action menu opened"
        ).fulfill()
        yield
        if self.is_element_visible(ancestor_selector + " .actions-dropdown"):
            self._find_within(ancestor_selector + " .action-more").click()
            EmptyPromise(
                lambda: not self.is_element_visible(ancestor_selector + " .actions-dropdown"),
                "Secondary action menu closed"
            ).fulfill()


class DiscussionTabSingleThreadPage(CoursePage):
    def __init__(self, browser, course_id, discussion_id, thread_id):
        super(DiscussionTabSingleThreadPage, self).__init__(browser, course_id)
        self.thread_page = DiscussionThreadPage(
            browser,
            u"body.discussion .discussion-article[data-id='{thread_id}']".format(thread_id=thread_id)
        )
        self.url_path = "discussion/forum/{discussion_id}/threads/{thread_id}".format(
            discussion_id=discussion_id, thread_id=thread_id
        )

    def is_browser_on_page(self):
        return self.thread_page.is_browser_on_page()

    def __getattr__(self, name):
        return getattr(self.thread_page, name)

    def close_open_thread(self):
        with self.thread_page.secondary_action_menu_open(".thread-main-wrapper"):
            self._find_within(".thread-main-wrapper .action-close").first.click()


class DiscussionTabHomePage(CoursePage):
    """
    Discussion tab home page
    """
    ALERT_SELECTOR = ".discussion-body .forum-nav .search-alert"

    def __init__(self, browser, course_id):
        super(DiscussionTabHomePage, self).__init__(browser, course_id)
        self.url_path = "discussion/forum/"
        self.root_selector = None

    def is_browser_on_page(self):
        return self.q(css=".discussion-body section.home-header").present
