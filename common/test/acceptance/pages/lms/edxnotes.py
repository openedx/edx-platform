from bok_choy.page_object import PageObject
from .course_page import CoursePage
from ...tests.helpers import disable_animations
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


class EdxNotesPage(CoursePage):
    """
    EdxNotes page.
    """
    url_path = "edxnotes"

    def __init__(self, *args, **kwargs):
        super(EdxNotesPage, self).__init__(*args, **kwargs)
        self.current_view = EdxNotesPageView(self.browser, "edx-notes-page-recent-activity")

    def is_browser_on_page(self):
        return self.q(css=".edx-notes-page-wrapper").present

    @property
    def children(self):
        return self.current_view.children

    @property
    def no_content_text(self):
        element = self.q(css=".no-content").first
        if element:
            return element.text[0]
        else:
            return None


class EdxNotesPageView(NoteChild):
    """
    Base class for EdxNotes views: Recent Activity, Course Structure.
    """
    BODY_SELECTOR = ".edx-notes-page-items-list"
    CHILD_SELECTOR = ".edx-notes-page-item"

    def is_browser_on_page(self):
        return all([
            self.q(css="{}#{}".format(self.BODY_SELECTOR, self.item_id)).present,
            not self.q(css=".ui-loading").visible,
        ])

    @property
    def children(self):
        children = self.q(css=self._bounded_selector(self.CHILD_SELECTOR))
        return [EdxNotesPageItem(self.browser, child.get_attribute("id")) for child in children]


class EdxNotesPageItem(NoteChild):
    """
    Helper class that works with note items on Note page of the course.
    """
    BODY_SELECTOR = ".edx-notes-page-item"
    UNIT_LINK_SELECTOR = "a.edx-notes-item-unit-link"

    def _get_element_text(self, selector):
        element = self.q(css=self._bounded_selector(selector)).first
        if element:
            return element.text[0]
        else:
            return None

    def go_to_unit(self, unit_page=None):
        self.q(css=self._bounded_selector(self.UNIT_LINK_SELECTOR)).click()
        if unit_page is not None:
            unit_page.wait_for_page()

    @property
    def unit_name(self):
        return self._get_element_text(self.UNIT_LINK_SELECTOR)

    @property
    def text(self):
        return self._get_element_text(".edx-notes-item-text")

    @property
    def quote(self):
        return self._get_element_text(".edx-notes-item-quote")

    @property
    def time_updated(self):
        return self._get_element_text(".edx-notes-item-last-edited-value")

    @property
    def title_highlighted(self):
        return self._get_element_text(".edx-notes-item-highlight-title")


class EdxNotesUnitPage(CoursePage):
    """
    Page for the Unit with EdxNotes.
    """
    url_path = "courseware/"

    def is_browser_on_page(self):
        return self.q(css="body.courseware .edx-notes-wrapper").present

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

    def __init__(self, browser, element, parent_id):
        super(EdxNoteHighlight, self).__init__(browser, parent_id)
        self.element = element
        self.item_id = parent_id
        disable_animations(self)

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
            self._bounded_selector(".annotator-viewer"), "Note Viewer is visible."
        )

    def wait_for_editor_visibility(self):
        """
        Waiting for visibility of note editor.
        """
        self.wait_for_element_visibility(
            self._bounded_selector(".annotator-editor"), "Note Editor is visible."
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
        ActionChains(self.browser).double_click(self.element).release().perform()
        self.wait_for_adder_visibility()
        self.q(css=self._bounded_selector(self.ADDER_SELECTOR)).first.click()
        self.wait_for_editor_visibility()
        return self

    def show(self):
        """
        Hover over highlighted text -> shows note.
        """
        ActionChains(self.browser).move_to_element(self.element).release().perform()
        self.wait_for_viewer_visibility()
        return self

    def cancel(self):
        """
        Clicks cancel button.
        """
        self.q(css=self._bounded_selector(".annotator-cancel")).first.click()
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
        element = self.q(css=self._bounded_selector(".annotator-annotation > div"))
        if element:
            text = element.text[0].strip()
        else:
            text = None
        self.q(css=("body")).first.click()
        self.wait_for_notes_invisibility()
        return text

    @text.setter
    def text(self, value):
        """
        Sets text for the note.
        """
        self.q(css=self._bounded_selector(".annotator-item textarea")).first.fill(value)
