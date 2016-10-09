from bok_choy.page_object import PageObject, PageLoadError, unguarded
from bok_choy.promise import BrokenPromise, EmptyPromise
from openedx.tests.acceptance.pages.lms.course_page import CoursePage
from openedx.tests.acceptance.pages.common.paging import PaginatedUIMixin
from openedx.tests.acceptance.tests.helpers import disable_animations
from selenium.webdriver.common.action_chains import ActionChains


class NoteChild(PageObject):
    url = None
    BODY_SELECTOR = None

    def __init__(self, browser, item_id):
        super(NoteChild, self).__init__(browser)
        self.item_id = item_id

    def is_browser_on_page(self):
        return self.q(css="{}#{}".format(self.BODY_SELECTOR, self.item_id)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `NoteChild` context
        """
        return "{}#{} {}".format(
            self.BODY_SELECTOR,
            self.item_id,
            selector,
        )

    def _get_element_text(self, selector):
        element = self.q(css=self._bounded_selector(selector)).first
        if element:
            return element.text[0]
        else:
            return None


class EdxNotesChapterGroup(NoteChild):
    """
    Helper class that works with chapter (section) grouping of notes in the Course Structure view on the Note page.
    """
    BODY_SELECTOR = ".note-group"

    @property
    def title(self):
        return self._get_element_text(".course-title")

    @property
    def subtitles(self):
        return [section.title for section in self.children]

    @property
    def children(self):
        children = self.q(css=self._bounded_selector('.note-section'))
        return [EdxNotesSubsectionGroup(self.browser, child.get_attribute("id")) for child in children]


class EdxNotesGroupMixin(object):
    """
    Helper mixin that works with note groups (used for subsection and tag groupings).
    """
    @property
    def title(self):
        return self._get_element_text(self.TITLE_SELECTOR)

    @property
    def children(self):
        children = self.q(css=self._bounded_selector('.note'))
        return [EdxNotesPageItem(self.browser, child.get_attribute("id")) for child in children]

    @property
    def notes(self):
        return [section.text for section in self.children]


class EdxNotesSubsectionGroup(NoteChild, EdxNotesGroupMixin):
    """
    Helper class that works with subsection grouping of notes in the Course Structure view on the Note page.
    """
    BODY_SELECTOR = ".note-section"
    TITLE_SELECTOR = ".course-subtitle"


class EdxNotesTagsGroup(NoteChild, EdxNotesGroupMixin):
    """
    Helper class that works with tags grouping of notes in the Tags view on the Note page.
    """
    BODY_SELECTOR = ".note-group"
    TITLE_SELECTOR = ".tags-title"

    def scrolled_to_top(self, group_index):
        """
        Returns True if the group with supplied group)index is scrolled near the top of the page
        (expects 10 px padding).

        The group_index must be supplied because JQuery must be used to get this information, and it
        does not have access to the bounded selector.
        """
        title_selector = "$('" + self.TITLE_SELECTOR + "')[" + str(group_index) + "]"
        top_script = "return " + title_selector + ".getBoundingClientRect().top;"
        EmptyPromise(
            lambda: 8 < self.browser.execute_script(top_script) < 12,
            "Expected tag title '{}' to scroll to top, but was at location {}".format(
                self.title, self.browser.execute_script(top_script)
            )
        ).fulfill()
        # Now also verify that focus has moved to this title (for screen readers):
        active_script = "return " + title_selector + " === document.activeElement;"
        return self.browser.execute_script(active_script)


class EdxNotesPageItem(NoteChild):
    """
    Helper class that works with note items on Note page of the course.
    """
    BODY_SELECTOR = ".note"
    UNIT_LINK_SELECTOR = "a.reference-unit-link"
    TAG_SELECTOR = "span.reference-tags"

    def go_to_unit(self, unit_page=None):
        self.q(css=self._bounded_selector(self.UNIT_LINK_SELECTOR)).click()
        if unit_page is not None:
            unit_page.wait_for_page()

    @property
    def unit_name(self):
        return self._get_element_text(self.UNIT_LINK_SELECTOR)

    @property
    def text(self):
        return self._get_element_text(".note-comment-p")

    @property
    def quote(self):
        return self._get_element_text(".note-excerpt")

    @property
    def time_updated(self):
        return self._get_element_text(".reference-updated-date")

    @property
    def tags(self):
        """ The tags associated with this note. """
        tag_links = self.q(css=self._bounded_selector(self.TAG_SELECTOR))
        if len(tag_links) == 0:
            return None
        return[tag_link.text for tag_link in tag_links]

    def go_to_tag(self, tag_name):
        """ Clicks a tag associated with the note to change to the tags view (and scroll to the tag group). """
        self.q(css=self._bounded_selector(self.TAG_SELECTOR)).filter(lambda el: tag_name in el.text).click()


class EdxNotesPageView(PageObject):
    """
    Base class for EdxNotes views: Recent Activity, Location in Course, Search Results.
    """
    url = None
    BODY_SELECTOR = ".tab-panel"
    TAB_SELECTOR = ".tab"
    CHILD_SELECTOR = ".note"
    CHILD_CLASS = EdxNotesPageItem

    @unguarded
    def visit(self):
        """
        Open the page containing this page object in the browser.

        Raises:
            PageLoadError: The page did not load successfully.

        Returns:
            PageObject
        """
        self.q(css=self.TAB_SELECTOR).first.click()
        try:
            return self.wait_for_page()
        except BrokenPromise:
            raise PageLoadError("Timed out waiting to load page '{!r}'".format(self))

    def is_browser_on_page(self):
        return all([
            self.q(css="{}".format(self.BODY_SELECTOR)).present,
            self.q(css="{}.is-active".format(self.TAB_SELECTOR)).present,
            not self.q(css=".ui-loading").visible,
        ])

    @property
    def is_closable(self):
        """
        Indicates if tab is closable or not.
        """
        return self.q(css="{} .action-close".format(self.TAB_SELECTOR)).present

    def close(self):
        """
        Closes the tab.
        """
        self.q(css="{} .action-close".format(self.TAB_SELECTOR)).first.click()

    @property
    def children(self):
        """
        Returns all notes on the page.
        """
        children = self.q(css=self.CHILD_SELECTOR)
        return [self.CHILD_CLASS(self.browser, child.get_attribute("id")) for child in children]


class RecentActivityView(EdxNotesPageView):
    """
    Helper class for Recent Activity view.
    """
    BODY_SELECTOR = "#recent-panel"
    TAB_SELECTOR = ".tab#view-recent-activity"


class CourseStructureView(EdxNotesPageView):
    """
    Helper class for Location in Course view.
    """
    BODY_SELECTOR = "#structure-panel"
    TAB_SELECTOR = ".tab#view-course-structure"
    CHILD_SELECTOR = ".note-group"
    CHILD_CLASS = EdxNotesChapterGroup


class TagsView(EdxNotesPageView):
    """
    Helper class for Tags view.
    """
    BODY_SELECTOR = "#tags-panel"
    TAB_SELECTOR = ".tab#view-tags"
    CHILD_SELECTOR = ".note-group"
    CHILD_CLASS = EdxNotesTagsGroup


class SearchResultsView(EdxNotesPageView):
    """
    Helper class for Search Results view.
    """
    BODY_SELECTOR = "#search-results-panel"
    TAB_SELECTOR = ".tab#view-search-results"


class EdxNotesPage(CoursePage, PaginatedUIMixin):
    """
    EdxNotes page.
    """
    url_path = "edxnotes/"
    MAPPING = {
        "recent": RecentActivityView,
        "structure": CourseStructureView,
        "tags": TagsView,
        "search": SearchResultsView,
    }

    def __init__(self, *args, **kwargs):
        super(EdxNotesPage, self).__init__(*args, **kwargs)
        self.current_view = self.MAPPING["recent"](self.browser)

    def is_browser_on_page(self):
        return self.q(css=".wrapper-student-notes .note-group").visible

    def switch_to_tab(self, tab_name):
        """
        Switches to the appropriate tab `tab_name(str)`.
        """
        self.current_view = self.MAPPING[tab_name](self.browser)
        self.current_view.visit()

    def close_tab(self):
        """
        Closes the current view.
        """
        self.current_view.close()
        self.current_view = self.MAPPING["recent"](self.browser)

    def search(self, text):
        """
        Runs search with `text(str)` query.
        """
        self.q(css="#search-notes-form #search-notes-input").first.fill(text)
        self.q(css='#search-notes-form .search-notes-submit').first.click()
        # Frontend will automatically switch to Search results tab when search
        # is running, so the view also needs to be changed.
        self.current_view = self.MAPPING["search"](self.browser)
        if text.strip():
            self.current_view.wait_for_page()

    @property
    def tabs(self):
        """
        Returns all tabs on the page.
        """
        tabs = self.q(css=".tabs .tab-label")
        if tabs:
            return map(lambda x: x.replace("Current tab\n", ""), tabs.text)
        else:
            return None

    @property
    def is_error_visible(self):
        """
        Indicates whether error message is visible or not.
        """
        return self.q(css=".inline-error").visible

    @property
    def error_text(self):
        """
        Returns error message.
        """
        element = self.q(css=".inline-error").first
        if element and self.is_error_visible:
            return element.text[0]
        else:
            return None

    @property
    def notes(self):
        """
        Returns all notes on the page.
        """
        children = self.q(css='.note')
        return [EdxNotesPageItem(self.browser, child.get_attribute("id")) for child in children]

    @property
    def chapter_groups(self):
        """
        Returns all chapter groups on the page.
        """
        children = self.q(css='.note-group')
        return [EdxNotesChapterGroup(self.browser, child.get_attribute("id")) for child in children]

    @property
    def subsection_groups(self):
        """
        Returns all subsection groups on the page.
        """
        children = self.q(css='.note-section')
        return [EdxNotesSubsectionGroup(self.browser, child.get_attribute("id")) for child in children]

    @property
    def tag_groups(self):
        """
        Returns all tag groups on the page.
        """
        children = self.q(css='.note-group')
        return [EdxNotesTagsGroup(self.browser, child.get_attribute("id")) for child in children]

    def count(self):
        """ Returns the total number of notes in the list """
        return len(self.q(css='div.wrapper-note-excerpts').results)


class EdxNotesPageNoContent(CoursePage):
    """
    EdxNotes page -- when no notes have been added.
    """
    url_path = "edxnotes/"

    def is_browser_on_page(self):
        return self.q(css=".wrapper-student-notes .is-empty").visible

    @property
    def no_content_text(self):
        """
        Returns no content message.
        """
        element = self.q(css=".is-empty").first
        if element:
            return element.text[0]
        else:
            return None


class EdxNotesUnitPage(CoursePage):
    """
    Page for the Unit with EdxNotes.
    """
    url_path = "courseware/"

    def is_browser_on_page(self):
        return self.q(css="body.courseware .edx-notes-wrapper").present

    def move_mouse_to(self, selector):
        """
        Moves mouse to the element that matches `selector(str)`.
        """
        body = self.q(css=selector)[0]
        ActionChains(self.browser).move_to_element(body).perform()
        return self

    def click(self, selector):
        """
        Clicks on the element that matches `selector(str)`.
        """
        self.q(css=selector).first.click()
        return self

    def toggle_visibility(self):
        """
        Clicks on the "Show notes" checkbox.
        """
        self.q(css=".action-toggle-notes").first.click()
        return self

    @property
    def components(self):
        """
        Returns a list of annotatable components.
        """
        components = self.q(css=".edx-notes-wrapper")
        return [AnnotatableComponent(self.browser, component.get_attribute("id")) for component in components]

    @property
    def notes(self):
        """
        Returns a list of notes for the page.
        """
        notes = []
        for component in self.components:
            notes.extend(component.notes)
        return notes

    def refresh(self):
        """
        Refreshes the page and returns a list of annotatable components.
        """
        self.browser.refresh()
        return self.components


class AnnotatableComponent(NoteChild):
    """
    Helper class that works with annotatable components.
    """
    BODY_SELECTOR = ".edx-notes-wrapper"

    @property
    def notes(self):
        """
        Returns a list of notes for the component.
        """
        notes = self.q(css=self._bounded_selector(".annotator-hl"))
        return [EdxNoteHighlight(self.browser, note, self.item_id) for note in notes]

    def create_note(self, selector=".annotate-id"):
        """
        Create the note by the selector, return a context manager that will
        show and save the note popup.
        """
        for element in self.q(css=self._bounded_selector(selector)):
            note = EdxNoteHighlight(self.browser, element, self.item_id)
            note.select_and_click_adder()
            yield note
            note.save()

    def edit_note(self, selector=".annotator-hl"):
        """
        Edit the note by the selector, return a context manager that will
        show and save the note popup.
        """
        for element in self.q(css=self._bounded_selector(selector)):
            note = EdxNoteHighlight(self.browser, element, self.item_id)
            note.show().edit()
            yield note
            note.save()

    def remove_note(self, selector=".annotator-hl"):
        """
        Removes the note by the selector.
        """
        for element in self.q(css=self._bounded_selector(selector)):
            note = EdxNoteHighlight(self.browser, element, self.item_id)
            note.show().remove()


class EdxNoteHighlight(NoteChild):
    """
    Helper class that works with notes.
    """
    BODY_SELECTOR = ""
    ADDER_SELECTOR = ".annotator-adder"
    VIEWER_SELECTOR = ".annotator-viewer"
    EDITOR_SELECTOR = ".annotator-editor"
    NOTE_SELECTOR = ".annotator-note"

    def __init__(self, browser, element, parent_id):
        super(EdxNoteHighlight, self).__init__(browser, parent_id)
        self.element = element
        self.item_id = parent_id
        disable_animations(self)

    @property
    def is_visible(self):
        """
        Returns True if the note is visible.
        """
        viewer_is_visible = self.q(css=self._bounded_selector(self.VIEWER_SELECTOR)).visible
        editor_is_visible = self.q(css=self._bounded_selector(self.EDITOR_SELECTOR)).visible
        return viewer_is_visible or editor_is_visible

    def wait_for_adder_visibility(self):
        """
        Waiting for visibility of note adder button.
        """
        self.wait_for_element_visibility(
            self._bounded_selector(self.ADDER_SELECTOR), "Adder is visible."
        )

    def wait_for_viewer_visibility(self):
        """
        Waiting for visibility of note viewer.
        """
        self.wait_for_element_visibility(
            self._bounded_selector(self.VIEWER_SELECTOR), "Note Viewer is visible."
        )

    def wait_for_editor_visibility(self):
        """
        Waiting for visibility of note editor.
        """
        self.wait_for_element_visibility(
            self._bounded_selector(self.EDITOR_SELECTOR), "Note Editor is visible."
        )

    def wait_for_notes_invisibility(self, text="Notes are hidden"):
        """
        Waiting for invisibility of all notes.
        """
        selector = self._bounded_selector(".annotator-outer")
        self.wait_for_element_invisibility(selector, text)

    def select_and_click_adder(self):
        """
        Creates selection for the element and clicks `add note` button.
        """
        ActionChains(self.browser).double_click(self.element).perform()
        self.wait_for_adder_visibility()
        self.q(css=self._bounded_selector(self.ADDER_SELECTOR)).first.click()
        self.wait_for_editor_visibility()
        return self

    def click_on_highlight(self):
        """
        Clicks on the highlighted text.
        """
        ActionChains(self.browser).move_to_element(self.element).click().perform()
        return self

    def click_on_viewer(self):
        """
        Clicks on the note viewer.
        """
        self.q(css=self.NOTE_SELECTOR).first.click()
        return self

    def show(self):
        """
        Hover over highlighted text -> shows note.
        """
        ActionChains(self.browser).move_to_element(self.element).perform()
        self.wait_for_viewer_visibility()
        return self

    def cancel(self):
        """
        Clicks cancel button.
        """
        self.q(css=self._bounded_selector(".annotator-close")).first.click()
        self.wait_for_notes_invisibility("Note is canceled.")
        return self

    def save(self):
        """
        Clicks save button.
        """
        self.q(css=self._bounded_selector(".annotator-save")).first.click()
        self.wait_for_notes_invisibility("Note is saved.")
        self.wait_for_ajax()
        return self

    def remove(self):
        """
        Clicks delete button.
        """
        self.q(css=self._bounded_selector(".annotator-delete")).first.click()
        self.wait_for_notes_invisibility("Note is removed.")
        self.wait_for_ajax()
        return self

    def edit(self):
        """
        Clicks edit button.
        """
        self.q(css=self._bounded_selector(".annotator-edit")).first.click()
        self.wait_for_editor_visibility()
        return self

    @property
    def text(self):
        """
        Returns text of the note.
        """
        self.show()
        element = self.q(css=self._bounded_selector(".annotator-annotation > div.annotator-note"))
        if element:
            text = element.text[0].strip()
        else:
            text = None
        self.cancel()
        return text

    @text.setter
    def text(self, value):
        """
        Sets text for the note.
        """
        self.q(css=self._bounded_selector(".annotator-item textarea")).first.fill(value)

    @property
    def tags(self):
        """
        Returns the tags associated with the note.

        Tags are returned as a list of strings, with each tag as an individual string.
        """
        tag_text = []
        self.show()
        tags = self.q(css=self._bounded_selector(".annotator-annotation > div.annotator-tags > span.annotator-tag"))
        if tags:
            for tag in tags:
                tag_text.append(tag.text)
        self.cancel()
        return tag_text

    @tags.setter
    def tags(self, tags):
        """
        Sets tags for the note. Tags should be supplied as a list of strings, with each tag as an individual string.
        """
        self.q(css=self._bounded_selector(".annotator-item input")).first.fill(" ".join(tags))

    def has_sr_label(self, sr_index, field_index, expected_text):
        """
        Returns true iff a screen reader label (of index sr_index) exists for the annotator field with
        the specified field_index and text.
        """
        label_exists = False
        EmptyPromise(
            lambda: len(self.q(css=self._bounded_selector("li.annotator-item > label.sr"))) > sr_index,
            "Expected more than '{}' sr labels".format(sr_index)
        ).fulfill()
        annotator_field_label = self.q(css=self._bounded_selector("li.annotator-item > label.sr"))[sr_index]
        for_attrib_correct = annotator_field_label.get_attribute("for") == "annotator-field-" + str(field_index)
        if for_attrib_correct and (annotator_field_label.text == expected_text):
            label_exists = True

        self.q(css="body").first.click()
        self.wait_for_notes_invisibility()

        return label_exists
