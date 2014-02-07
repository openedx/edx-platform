from bok_choy.page_object import unguarded
from bok_choy.promise import EmptyPromise, fulfill

from .course_page import CoursePage


class DiscussionSingleThreadPage(CoursePage):
    def __init__(self, browser, course_id, thread_id):
        super(DiscussionSingleThreadPage, self).__init__(browser, course_id)
        self.thread_id = thread_id

    def is_browser_on_page(self):
        return self.is_css_present(
            "body.discussion .discussion-article[data-id='{thread_id}']".format(thread_id=self.thread_id)
        )

    @property
    @unguarded
    def url_path(self):
        return "discussion/forum/dummy/threads/" + self.thread_id

    def _get_element_text(self, selector):
        """
        Returns the text of the first element matching the given selector, or
        None if no such element exists
        """
        text_list = self.css_text(selector)
        return text_list[0] if text_list else None

    def get_response_total_text(self):
        """Returns the response count text, or None if not present"""
        return self._get_element_text(".response-count")

    def get_num_displayed_responses(self):
        """Returns the number of responses actually rendered"""
        return self.css_count(".discussion-response")

    def get_shown_responses_text(self):
        """Returns the shown response count text, or None if not present"""
        return self._get_element_text(".response-display-count")

    def get_load_responses_button_text(self):
        """Returns the load more responses button text, or None if not present"""
        return self._get_element_text(".load-response-button")

    def load_more_responses(self):
        """Clicks the laod more responses button and waits for responses to load"""
        self.css_click(".load-response-button")
        fulfill(EmptyPromise(
            lambda: not self.is_css_present(".loading"),
            "Loading more responses completed"
        ))

    def has_add_response_button(self):
        """Returns true if the add response button is visible, false otherwise"""
        return (
            self.is_css_present(".add-response-btn") and
            self.css_map(".add-response-btn", lambda el: el.visible)[0]
        )

    def click_add_response_button(self):
        """
        Clicks the add response button and ensures that the response text
        field receives focus
        """
        self.css_click(".add-response-btn")
        fulfill(EmptyPromise(
            lambda: self.is_css_present("#wmd-input-reply-body-{thread_id}:focus".format(thread_id=self.thread_id)),
            "Response field received focus"
        ))
