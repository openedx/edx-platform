from bok_choy.page_object import unguarded
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage


class DiscussionSingleThreadPage(CoursePage):
    def __init__(self, browser, course_id, thread_id):
        super(DiscussionSingleThreadPage, self).__init__(browser, course_id)
        self.thread_id = thread_id

    def is_browser_on_page(self):
        return self.q(css=
            "body.discussion .discussion-article[data-id='{thread_id}']".format(thread_id=self.thread_id)
        ).present

    @property
    @unguarded
    def url_path(self):
        return "discussion/forum/dummy/threads/" + self.thread_id

    def _get_element_text(self, selector):
        """
        Returns the text of the first element matching the given selector, or
        None if no such element exists
        """
        text_list = self.q(css=selector).text
        return text_list[0] if text_list else None

    def get_response_total_text(self):
        """Returns the response count text, or None if not present"""
        return self._get_element_text(".response-count")

    def get_num_displayed_responses(self):
        """Returns the number of responses actually rendered"""
        return len(self.q(css=".discussion-response").results)

    def get_shown_responses_text(self):
        """Returns the shown response count text, or None if not present"""
        return self._get_element_text(".response-display-count")

    def get_load_responses_button_text(self):
        """Returns the load more responses button text, or None if not present"""
        return self._get_element_text(".load-response-button")

    def load_more_responses(self):
        """Clicks the load more responses button and waits for responses to load"""
        self.q(css=".load-response-button").first.click()

        EmptyPromise(
            lambda: not self.q(css=".loading").present,
            "Loading more responses completed"
        ).fulfill()

    def has_add_response_button(self):
        """Returns true if the add response button is visible, false otherwise"""

        EmptyPromise(lambda: self.q(css=".add-response-btn").present, 'response button not available').fulfill()



        return self.q(css=".add-response-btn").present

    def click_add_response_button(self):
        """
        Clicks the add response button and ensures that the response text
        field receives focus
        """
        self.q(css=".add-response-btn").first.click()
        EmptyPromise(
            lambda: self.q(css="#wmd-input-reply-body-{thread_id}:focus".format(thread_id=self.thread_id)).present,
            "Response field received focus"
        ).fulfill()

    def _is_element_visible(self, selector):
        return (
            self.q(css=selector).present and
            self.q(css=selector).map(lambda el: el.is_displayed()).text[0]
        )

    def is_comment_visible(self, comment_id):
        """Returns true if the comment is viewable onscreen"""
        return self.q(css="#comment_{}".format(comment_id)).present

    def is_comment_deletable(self, comment_id):
        """Returns true if the delete comment button is present and visible, false otherwise"""
        return self.q(css="#comment_{} div.action-delete".format(comment_id)).visible

    def delete_comment(self, comment_id):
        with self.handle_alert():
            self.q(css="#comment_{} div.action-delete".format(comment_id)).first.click()
        EmptyPromise(
            lambda: not self.q(css=comment_id),
            "Deleted comment was removed"
        ).fulfill()
