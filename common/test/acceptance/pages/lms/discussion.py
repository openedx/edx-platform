from contextlib import contextmanager

from bok_choy.javascript import wait_for_js
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise

from .course_page import CoursePage


class DiscussionPageMixin(object):

    def is_ajax_finished(self):
        return self.browser.execute_script("return jQuery.active") == 0


class DiscussionThreadPage(PageObject, DiscussionPageMixin):
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

    def get_group_visibility_label(self):
        """
        Returns the group visibility label shown for the thread.
        """
        return self._get_element_text(".group-visibility-label")

    def get_response_total_text(self):
        """Returns the response count text, or None if not present"""
        self.wait_for_ajax()
        return self._get_element_text(".response-count")

    def get_num_displayed_responses(self):
        """Returns the number of responses actually rendered"""
        return len(self._find_within(".discussion-response"))

    def get_shown_responses_text(self):
        """Returns the shown response count text, or None if not present"""
        return self._get_element_text(".response-display-count")

    def get_load_responses_button_text(self):
        """Returns the load more responses button text, or None if not present"""
        return self._get_element_text(".load-response-button")

    def load_more_responses(self):
        """Clicks the load more responses button and waits for responses to load"""
        self._find_within(".load-response-button").click()

        EmptyPromise(
            self.is_ajax_finished,
            "Loading more Responses"
        ).fulfill()

    def has_add_response_button(self):
        """Returns true if the add response button is visible, false otherwise"""
        return self.is_element_visible(".add-response-btn")

    def click_add_response_button(self):
        """
        Clicks the add response button and ensures that the response text
        field receives focus
        """
        self._find_within(".add-response-btn").first.click()
        EmptyPromise(
            lambda: self._find_within(".discussion-reply-new textarea:focus").present,
            "Response field received focus"
        ).fulfill()

    @wait_for_js
    def is_response_editor_visible(self, response_id):
        """Returns true if the response editor is present, false otherwise"""
        return self.is_element_visible(".response_{} .edit-post-body".format(response_id))

    @wait_for_js
    def is_discussion_body_visible(self):
        return self.is_element_visible(".post-body")

    def verify_mathjax_preview_available(self):
        """ Checks that MathJax Preview css class is present """
        self.wait_for(
            lambda: len(self.q(css=".MathJax_Preview").text) > 0 and self.q(css=".MathJax_Preview").text[0] == "",
            description="MathJax Preview is rendered"
        )

    def verify_mathjax_rendered(self):
        """ Checks that MathJax css class is present """
        self.wait_for(
            lambda: self.is_element_visible(".MathJax_SVG"),
            description="MathJax Preview is rendered"
        )

    def is_response_visible(self, comment_id):
        """Returns true if the response is viewable onscreen"""
        self.wait_for_ajax()
        return self.is_element_visible(".response_{} .response-body".format(comment_id))

    def is_response_editable(self, response_id):
        """Returns true if the edit response button is present, false otherwise"""
        with self.secondary_action_menu_open(".response_{} .discussion-response".format(response_id)):
            return self.is_element_visible(".response_{} .discussion-response .action-edit".format(response_id))

    def get_response_body(self, response_id):
        return self._get_element_text(".response_{} .response-body".format(response_id))

    def start_response_edit(self, response_id):
        """Click the edit button for the response, loading the editing view"""
        with self.secondary_action_menu_open(".response_{} .discussion-response".format(response_id)):
            self._find_within(".response_{} .discussion-response .action-edit".format(response_id)).first.click()
            EmptyPromise(
                lambda: self.is_response_editor_visible(response_id),
                "Response edit started"
            ).fulfill()

    def get_link_href(self):
        """Extracts href attribute of the referenced link"""
        link_href = self._find_within(".post-body p a").attrs('href')
        return link_href[0] if link_href else None

    def get_response_vote_count(self, response_id):
        return self._get_element_text(".response_{} .discussion-response .action-vote .vote-count".format(response_id))

    def vote_response(self, response_id):
        current_count = self._get_element_text(".response_{} .discussion-response .action-vote .vote-count".format(response_id))
        self._find_within(".response_{} .discussion-response .action-vote".format(response_id)).first.click()
        self.wait_for_ajax()
        EmptyPromise(
            lambda: current_count != self.get_response_vote_count(response_id),
            "Response is voted"
        ).fulfill()

    def cannot_vote_response(self, response_id):
        """Assert that the voting button is not visible on this response"""
        return not self.is_element_visible(".response_{} .discussion-response .action-vote".format(response_id))

    def is_response_reported(self, response_id):
        return self.is_element_visible(".response_{} .discussion-response .post-label-reported".format(response_id))

    def report_response(self, response_id):
        with self.secondary_action_menu_open(".response_{} .discussion-response".format(response_id)):
            self._find_within(".response_{} .discussion-response .action-report".format(response_id)).first.click()
            self.wait_for_ajax()
            EmptyPromise(
                lambda: self.is_response_reported(response_id),
                "Response is reported"
            ).fulfill()

    def cannot_report_response(self, response_id):
        """Assert that the reporting button is not visible on this response"""
        return not self.is_element_visible(".response_{} .discussion-response .action-report".format(response_id))

    def is_response_endorsed(self, response_id):
        return "endorsed" in self._get_element_text(".response_{} .discussion-response .posted-details".format(response_id))

    def endorse_response(self, response_id):
        self._find_within(".response_{} .discussion-response .action-endorse".format(response_id)).first.click()
        self.wait_for_ajax()
        EmptyPromise(
            lambda: self.is_response_endorsed(response_id),
            "Response edit started"
        ).fulfill()

    def set_response_editor_value(self, response_id, new_body):
        """Replace the contents of the response editor"""
        self._find_within(".response_{} .discussion-response .wmd-input".format(response_id)).fill(new_body)

    def verify_link_editor_error_messages_shown(self):
        """
        Confirm that the error messages are displayed in the editor.
        """
        def errors_visible():
            """
            Returns True if both errors are visible, False otherwise.
            """
            return (
                self.q(css="#new-url-input-field-message.has-error").visible and
                self.q(css="#new-url-desc-input-field-message.has-error").visible
            )

        self.wait_for(errors_visible, "Form errors should be visible.")

    def add_content_via_editor_button(self, content_type, response_id, url, description, is_decorative=False):
        """Replace the contents of the response editor"""
        self._find_within(
            "#wmd-{}-button-edit-post-body-{}".format(
                content_type,
                response_id,
            )
        ).click()
        self.q(css='#new-url-input').fill(url)
        self.q(css='#new-url-desc-input').fill(description)

        if is_decorative:
            self.q(css='#img-is-decorative').click()

        self.q(css='input[value="OK"]').click()

    def submit_response_edit(self, response_id, new_response_body):
        """Click the submit button on the response editor"""

        def submit_response_check_func():
            """
            Tries to click "Update post" and returns True if the post
            was successfully updated, False otherwise.
            """
            self._find_within(
                ".response_{} .discussion-response .post-update".format(
                    response_id
                )
            ).first.click()

            return (
                not self.is_response_editor_visible(response_id) and
                self.is_response_visible(response_id) and
                self.get_response_body(response_id) == new_response_body
            )

        self.wait_for(submit_response_check_func, "Comment edit succeeded")

    def is_show_comments_visible(self, response_id):
        """Returns true if the "show comments" link is visible for a response"""
        return self.is_element_visible(".response_{} .action-show-comments".format(response_id))

    def show_comments(self, response_id):
        """Click the "show comments" link for a response"""
        self._find_within(".response_{} .action-show-comments".format(response_id)).first.click()
        EmptyPromise(
            lambda: self.is_element_visible(".response_{} .comments".format(response_id)),
            "Comments shown"
        ).fulfill()

    def is_add_comment_visible(self, response_id):
        """Returns true if the "add comment" form is visible for a response"""
        return self.is_element_visible("#wmd-input-comment-body-{}".format(response_id))

    def is_comment_visible(self, comment_id):
        """Returns true if the comment is viewable onscreen"""
        return self.is_element_visible("#comment_{} .response-body".format(comment_id))

    def get_comment_body(self, comment_id):
        return self._get_element_text("#comment_{} .response-body".format(comment_id))

    def is_comment_deletable(self, comment_id):
        """Returns true if the delete comment button is present, false otherwise"""
        with self.secondary_action_menu_open("#comment_{}".format(comment_id)):
            return self.is_element_visible("#comment_{} .action-delete".format(comment_id))

    def delete_comment(self, comment_id):
        with self.handle_alert():
            with self.secondary_action_menu_open("#comment_{}".format(comment_id)):
                self._find_within("#comment_{} .action-delete".format(comment_id)).first.click()
        EmptyPromise(
            lambda: not self.is_comment_visible(comment_id),
            "Deleted comment was removed"
        ).fulfill()

    def is_comment_editable(self, comment_id):
        """Returns true if the edit comment button is present, false otherwise"""
        with self.secondary_action_menu_open("#comment_{}".format(comment_id)):
            return self.is_element_visible("#comment_{} .action-edit".format(comment_id))

    def is_comment_editor_visible(self, comment_id):
        """Returns true if the comment editor is present, false otherwise"""
        return self.is_element_visible(".edit-comment-body[data-id='{}']".format(comment_id))

    def _get_comment_editor_value(self, comment_id):
        return self._find_within("#wmd-input-edit-comment-body-{}".format(comment_id)).text[0]

    def start_comment_edit(self, comment_id):
        """Click the edit button for the comment, loading the editing view"""
        old_body = self.get_comment_body(comment_id)
        with self.secondary_action_menu_open("#comment_{}".format(comment_id)):
            self._find_within("#comment_{} .action-edit".format(comment_id)).first.click()
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
        self._find_within("#comment_{} .wmd-input".format(comment_id)).fill(new_body)

    def submit_comment_edit(self, comment_id, new_comment_body):
        """Click the submit button on the comment editor"""
        self._find_within("#comment_{} .post-update".format(comment_id)).first.click()
        self.wait_for_ajax()
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
        self._find_within("#comment_{} .post-cancel".format(comment_id)).first.click()
        EmptyPromise(
            lambda: (
                not self.is_comment_editor_visible(comment_id) and
                self.is_comment_visible(comment_id) and
                self.get_comment_body(comment_id) == original_body
            ),
            "Comment edit was canceled"
        ).fulfill()


class DiscussionSortPreferencePage(CoursePage):
    """
    Page that contain the discussion board with sorting options
    """
    def __init__(self, browser, course_id):
        super(DiscussionSortPreferencePage, self).__init__(browser, course_id)
        self.url_path = "discussion/forum"

    def is_browser_on_page(self):
        """
        Return true if the browser is on the right page else false.
        """
        return self.q(css="body.discussion .forum-nav-sort-control").present

    def show_all_discussions(self):
        """ Show the list of all discussions. """
        self.q(css=".forum-nav-browse").click()

    def get_selected_sort_preference(self):
        """
        Return the text of option that is selected for sorting.
        """
        options = self.q(css="body.discussion .forum-nav-sort-control option")
        return options.filter(lambda el: el.is_selected())[0].get_attribute("value")

    def change_sort_preference(self, sort_by):
        """
        Change the option of sorting by clicking on new option.
        """
        self.q(css="body.discussion .forum-nav-sort-control option[value='{0}']".format(sort_by)).click()

    def refresh_page(self):
        """
        Reload the page.
        """
        self.browser.refresh()


class DiscussionTabSingleThreadPage(CoursePage):
    def __init__(self, browser, course_id, discussion_id, thread_id):
        super(DiscussionTabSingleThreadPage, self).__init__(browser, course_id)
        self.thread_page = DiscussionThreadPage(
            browser,
            "body.discussion .discussion-article[data-id='{thread_id}']".format(thread_id=thread_id)
        )
        self.url_path = "discussion/forum/{discussion_id}/threads/{thread_id}".format(
            discussion_id=discussion_id, thread_id=thread_id
        )

    def is_browser_on_page(self):
        return self.thread_page.is_browser_on_page()

    def __getattr__(self, name):
        return getattr(self.thread_page, name)

    def show_all_discussions(self):
        """ Show the list of all discussions. """
        self.q(css=".forum-nav-browse").click()

    def close_open_thread(self):
        with self.thread_page.secondary_action_menu_open(".thread-main-wrapper"):
            self._find_within(".thread-main-wrapper .action-close").first.click()

    def is_focused_on_element(self, selector):
        """
        Check if the focus is on element
        """
        return self.browser.execute_script("return $('{}').is(':focus')".format(selector))

    def _thread_is_rendered_successfully(self, thread_id):
        return self.q(css=".discussion-article[data-id='{}']".format(thread_id)).visible

    def click_and_open_thread(self, thread_id):
        """
        Click specific thread on the list.
        """
        thread_selector = "li[data-id='{}']".format(thread_id)
        self.q(css=thread_selector).first.click()
        EmptyPromise(
            lambda: self._thread_is_rendered_successfully(thread_id),
            "Thread has been rendered"
        ).fulfill()

    def check_threads_rendered_successfully(self, thread_count):
        """
        Count the number of threads available on page.
        """
        return len(self.q(css=".forum-nav-thread").results) == thread_count

    def check_focus_is_set(self, selector):
        """
        Check focus is set
        """
        EmptyPromise(
            lambda: self.is_focused_on_element(selector),
            "Focus is on other element"
        ).fulfill()


class InlineDiscussionPage(PageObject):
    url = None

    def __init__(self, browser, discussion_id):
        super(InlineDiscussionPage, self).__init__(browser)
        self._discussion_selector = (
            ".discussion-module[data-discussion-id='{discussion_id}'] ".format(
                discussion_id=discussion_id
            )
        )

    def _find_within(self, selector):
        """
        Returns a query corresponding to the given CSS selector within the scope
        of this discussion page
        """
        return self.q(css=self._discussion_selector + " " + selector)

    def is_browser_on_page(self):
        self.wait_for_ajax()
        return self.q(css=self._discussion_selector).present

    def is_discussion_expanded(self):
        return self._find_within(".discussion").present

    def expand_discussion(self):
        """Click the link to expand the discussion"""
        self._find_within(".discussion-show").first.click()
        EmptyPromise(
            self.is_discussion_expanded,
            "Discussion expanded"
        ).fulfill()

    def get_num_displayed_threads(self):
        return len(self._find_within(".discussion-thread"))

    def has_thread(self, thread_id):
        """Returns true if this page is showing the thread with the specified id."""
        return self._find_within('.discussion-thread#thread_{}'.format(thread_id)).present

    def element_exists(self, selector):
        return self.q(css=self._discussion_selector + " " + selector).present

    def is_new_post_opened(self):
        return self._find_within(".new-post-article").visible

    def click_element(self, selector):
        self.wait_for_element_presence(
            "{discussion} {selector}".format(discussion=self._discussion_selector, selector=selector),
            "{selector} is visible".format(selector=selector)
        )
        self._find_within(selector).click()

    def click_cancel_new_post(self):
        self.click_element(".cancel")
        EmptyPromise(
            lambda: not self.is_new_post_opened(),
            "New post closed"
        ).fulfill()

    def click_new_post_button(self):
        self.click_element(".new-post-btn")
        EmptyPromise(
            self.is_new_post_opened,
            "New post opened"
        ).fulfill()

    @wait_for_js
    def _is_element_visible(self, selector):
        query = self._find_within(selector)
        return query.present and query.visible


class InlineDiscussionThreadPage(DiscussionThreadPage):
    def __init__(self, browser, thread_id):
        super(InlineDiscussionThreadPage, self).__init__(
            browser,
            "body.courseware .discussion-module #thread_{thread_id}".format(thread_id=thread_id)
        )

    def expand(self):
        """Clicks the link to expand the thread"""
        self._find_within(".forum-thread-expand").first.click()
        EmptyPromise(
            lambda: bool(self.get_response_total_text()),
            "Thread expanded"
        ).fulfill()

    def is_thread_anonymous(self):
        return not self.q(css=".posted-details > .username").present

    @wait_for_js
    def check_if_selector_is_focused(self, selector):
        """
        Check if selector is focused
        """
        return self.browser.execute_script("return $('{}').is(':focus')".format(selector))


class DiscussionUserProfilePage(CoursePage):

    TEXT_NEXT = u'Next >'
    TEXT_PREV = u'< Previous'
    PAGING_SELECTOR = "a.discussion-pagination[data-page-number]"

    def __init__(self, browser, course_id, user_id, username, page=1):
        super(DiscussionUserProfilePage, self).__init__(browser, course_id)
        self.url_path = "discussion/forum/dummy/users/{}?page={}".format(user_id, page)
        self.username = username

    def is_browser_on_page(self):
        return (
            self.q(css='.discussion-user-threads[data-course-id="{}"]'.format(self.course_id)).present
            and
            self.q(css='.user-profile .learner-profile-link').present
            and
            self.q(css='.user-profile .learner-profile-link').text[0] == self.username
        )

    @wait_for_js
    def is_window_on_top(self):
        return self.browser.execute_script("return $('html, body').offset().top") == 0

    def get_shown_thread_ids(self):
        elems = self.q(css="article.discussion-thread")
        return [elem.get_attribute("id")[7:] for elem in elems]

    def get_current_page(self):
        def check_func():
            try:
                current_page = int(self.q(css="nav.discussion-paginator li.current-page").text[0])
            except:
                return False, None
            return True, current_page

        return Promise(
            check_func, 'discussion-paginator current page has text', timeout=5,
        ).fulfill()

    def _check_pager(self, text, page_number=None):
        """
        returns True if 'text' matches the text in any of the pagination elements.  If
        page_number is provided, only return True if the element points to that result
        page.
        """
        elems = self.q(css=self.PAGING_SELECTOR).filter(lambda elem: elem.text == text)
        if page_number:
            elems = elems.filter(lambda elem: int(elem.get_attribute('data-page-number')) == page_number)
        return elems.present

    def get_clickable_pages(self):
        return sorted([
            int(elem.get_attribute('data-page-number'))
            for elem in self.q(css=self.PAGING_SELECTOR)
            if str(elem.text).isdigit()
        ])

    def is_prev_button_shown(self, page_number=None):
        return self._check_pager(self.TEXT_PREV, page_number)

    def is_next_button_shown(self, page_number=None):
        return self._check_pager(self.TEXT_NEXT, page_number)

    def _click_pager_with_text(self, text, page_number):
        """
        click the first pagination element with whose text is `text` and ensure
        the resulting page number matches `page_number`.
        """
        targets = [elem for elem in self.q(css=self.PAGING_SELECTOR) if elem.text == text]
        targets[0].click()
        EmptyPromise(
            lambda: self.get_current_page() == page_number,
            "navigated to desired page"
        ).fulfill()

    def click_prev_page(self):
        self._click_pager_with_text(self.TEXT_PREV, self.get_current_page() - 1)
        EmptyPromise(
            self.is_window_on_top,
            "Window is on top"
        ).fulfill()

    def click_next_page(self):
        self._click_pager_with_text(self.TEXT_NEXT, self.get_current_page() + 1)
        EmptyPromise(
            self.is_window_on_top,
            "Window is on top"
        ).fulfill()

    def click_on_page(self, page_number):
        self._click_pager_with_text(unicode(page_number), page_number)
        EmptyPromise(
            self.is_window_on_top,
            "Window is on top"
        ).fulfill()

    def click_on_sidebar_username(self):
        self.wait_for_page()
        self.q(css='.learner-profile-link').first.click()


class DiscussionTabHomePage(CoursePage, DiscussionPageMixin):

    ALERT_SELECTOR = ".discussion-body .forum-nav .search-alert"

    def __init__(self, browser, course_id):
        super(DiscussionTabHomePage, self).__init__(browser, course_id)
        self.url_path = "discussion/forum/"

    def is_browser_on_page(self):
        return self.q(css=".discussion-body section.home-header").present

    def perform_search(self, text="dummy"):
        self.q(css=".forum-nav-search-input").fill(text + chr(10))
        EmptyPromise(
            self.is_ajax_finished,
            "waiting for server to return result"
        ).fulfill()

    def get_search_alert_messages(self):
        return self.q(css=self.ALERT_SELECTOR + " .message").text

    def get_search_alert_links(self):
        return self.q(css=self.ALERT_SELECTOR + " .link-jump")

    def dismiss_alert_message(self, text):
        """
        dismiss any search alert message containing the specified text.
        """
        def _match_messages(text):
            return self.q(css=".search-alert").filter(lambda elem: text in elem.text)

        for alert_id in _match_messages(text).attrs("id"):
            self.q(css="{}#{} a.dismiss".format(self.ALERT_SELECTOR, alert_id)).click()
        EmptyPromise(
            lambda: _match_messages(text).results == [],
            "waiting for dismissed alerts to disappear"
        ).fulfill()

    def click_new_post_button(self):
        """
        Clicks the 'New Post' button.
        """
        self.new_post_button.click()
        EmptyPromise(
            lambda: (
                self.new_post_form
            ),
            "New post action succeeded"
        ).fulfill()

    @property
    def new_post_button(self):
        """
        Returns the new post button.
        """
        elements = self.q(css=".new-post-btn")
        return elements.first if elements.visible and len(elements) == 1 else None

    @property
    def new_post_form(self):
        """
        Returns the new post form.
        """
        elements = self.q(css=".forum-new-post-form")
        return elements[0] if elements.visible and len(elements) == 1 else None
