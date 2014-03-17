from bok_choy.page_object import unguarded
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage


class DiscussionSingleThreadPage(CoursePage):
    def __init__(self, browser, course_id, thread_id):
        super(DiscussionSingleThreadPage, self).__init__(browser, course_id)
        self.thread_id = thread_id

    def is_browser_on_page(self):
        return self.q(
            css="body.discussion .discussion-article[data-id='{thread_id}']".format(thread_id=self.thread_id)
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
        return len(self.q(css=".discussion-response").text)

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
        return self._is_element_visible(".add-response-btn")

    def click_add_response_button(self):
        """
        Clicks the add response button and ensures that the response text
        field receives focus
        """
        self.q(css=".add-response-btn").first.click()
        EmptyPromise(
            lambda: self.q(css="#wmd-input-reply-body-{thread_id}:focus".format(thread_id=self.thread_id)),
            "Response field received focus"
        ).fulfill()

    def _is_element_visible(self, selector):
        return (
            self.q(css=selector).present and
            self.q(css=selector).visible
        )

    def is_response_editor_visible(self, response_id):
        """Returns true if the response editor is present, false otherwise"""
        return self._is_element_visible(".response_{} .edit-post-body".format(response_id))

    def start_response_edit(self, response_id):
        """Click the edit button for the response, loading the editing view"""
        from nose.tools import set_trace; set_trace()
        self.q(css=".response_{} .discussion-response .action-edit".format(response_id)).first.click()
        EmptyPromise(
            lambda: self.is_response_editor_visible(response_id),
            "Response edit started"
        ).fulfill()

    def is_add_comment_visible(self, response_id):
        """Returns true if the "add comment" form is visible for a response"""
        return self._is_element_visible("#wmd-input-comment-body-{}".format(response_id))

    def is_comment_visible(self, comment_id):
        """Returns true if the comment is viewable onscreen"""
        result = self._is_element_visible("#comment_{} .response-body".format(comment_id))
        return result

    def get_comment_body(self, comment_id):
        return self._get_element_text("#comment_{} .response-body".format(comment_id))

    def is_comment_deletable(self, comment_id):
        """Returns true if the delete comment button is present, false otherwise"""
        return self._is_element_visible("#comment_{} div.action-delete".format(comment_id))

    def delete_comment(self, comment_id):
        with self.handle_alert():
            self.q(css="#comment_{} div.action-delete".format(comment_id)).first.click()
        EmptyPromise(
            lambda: not self.is_comment_visible(comment_id),
            "Deleted comment was removed"
        ).fulfill()

    def is_comment_editable(self, comment_id):
        """Returns true if the edit comment button is present, false otherwise"""
        return self._is_element_visible("#comment_{} .action-edit".format(comment_id))

    def is_comment_editor_visible(self, comment_id):
        """Returns true if the comment editor is present, false otherwise"""
        return self._is_element_visible(".edit-comment-body[data-id='{}']".format(comment_id))

    def _get_comment_editor_value(self, comment_id):
        return self.q(css="#wmd-input-edit-comment-body-{}".format(comment_id)).text[0]

    def start_comment_edit(self, comment_id):
        """Click the edit button for the comment, loading the editing view"""
        old_body = self.get_comment_body(comment_id)
        self.q(css="#comment_{} .action-edit".format(comment_id)).first.click()
        EmptyPromise(
            lambda: (
                self.is_comment_editor_visible(comment_id) and
                not self.is_comment_visible(comment_id) and
                self._get_comment_editor_value(comment_id) == old_body
            ),
            "Comment edit started"
        ).fulfill()

    def set_comment_editor_value(self, comment_id, new_body):
        """Replace the contents of the comment editor"""
        self.q(css="#comment_{} .wmd-input".format(comment_id)).fill(new_body)

    #def submit_comment_edit(self, comment_id):
        #"""Click the submit button on the comment editor"""
        #new_body = self._get_comment_editor_value(comment_id)
        #self.q(css="#comment_{} .post-update".format(comment_id)).first.click()
        #EmptyPromise(
            #lambda: (
                #not self.is_comment_editor_visible(comment_id) and
                #self.is_comment_visible(comment_id) and
                #self.get_comment_body(comment_id) == new_body
            #),
            #"Comment edit succeeded"
        #).fulfill()


    def submit_comment_edit(self, comment_id, new_comment_body):
        """Click the submit button on the comment editor"""
        self.q(css="#comment_{} .post-update".format(comment_id)).first.click()
        EmptyPromise(
            lambda: (
                not self.is_comment_editor_visible(comment_id) and
                self.is_comment_visible(comment_id) and
                self.get_comment_body(comment_id) == new_comment_body
            ),
            "Comment edit succeeded"
        ).fulfill()


    def cancel_comment_edit(self, comment_id, original_body):
        """Click the cancel button on the comment editor"""
        self.q(css="#comment_{} .post-cancel".format(comment_id)).first.click()
        EmptyPromise(
            lambda: (
                not self.is_comment_editor_visible(comment_id) and
                self.is_comment_visible(comment_id) and
                self.get_comment_body(comment_id) == original_body
            ),
            "Comment edit was canceled"
        ).fulfill()
