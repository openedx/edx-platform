from .course_page import CoursePage
from selenium.webdriver.common.action_chains import ActionChains

SELECTORS = {
    'wrapper': '.edx-notes-wrapper',
    'highlight': '.annotator-hl',
    'adder': '.annotator-adder',
    'textarea': '.annotator-item textarea',
    'button_cancel': '.annotator-cancel',
    'button_save': '.annotator-save',
    'button_edit': '.annotator-edit',
    'button_delete': '.annotator-delete',
    'viewer': '.annotator-viewer',
    'editor': '.annotator-editor',
    'popup': '.annotator-outer',
}


class EdxNotesUnitPage(CoursePage):
    """
    Page for the Unit with EdxNotes.
    """
    url_path = "courseware/"
    _notes = []

    def __init__(self, browser, course_id):
        super(EdxNotesUnitPage, self).__init__(browser, course_id)
        self.edxnotes_selector = ("body.courseware .edx-notes-wrapper")

    def is_browser_on_page(self):
        return self.q(css=self.edxnotes_selector).present

    @property
    def components(self):
        """
        Returns a list of annotatable components.
        """
        return [AnnotatedComponent(ac, self) for ac in self.q(css=SELECTORS['wrapper'])]

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


class NotesMixin(object):
    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `AnnotatedComponent` context
        """
        return '#{} {}'.format(self.id, selector)

    def find_css(self, selector):
        return self.page.q(css=self._bounded_selector(selector))


class AnnotatedComponent(NotesMixin):
    """
    Helper class that works with annotated components.
    """
    def __init__(self, element, page):
        self.page = page
        self.element = element
        self.id = self.element.get_attribute('id')

    @property
    def notes(self):
        """
        Returns a list of notes for the component.
        """
        return [EdxNote(hl, self.page, self.id) for hl in self.find_css(SELECTORS['highlight'])]

    def create_note(self, selector=".annotate-id"):
        """
        Create the note by the selector, return a context manager that will
        show and save the note popup.
        """
        for element in self.find_css(selector):
            note = EdxNote(element, self.page, self.id)
            note.select_and_click_adder()
            yield note
            note.save()

    def edit_note(self, selector=".annotator-hl"):
        """
        Edit the note by the selector, return a context manager that will
        show and save the note popup.
        """
        for element in self.find_css(selector):
            note = EdxNote(element, self.page, self.id)
            note.show().edit()
            yield note
            note.save()

    def remove_note(self, selector=".annotator-hl"):
        """
        Removes the note by the selector.
        """
        for element in self.find_css(selector):
            note = EdxNote(element, self.page, self.id)
            note.show().remove()


class EdxNote(NotesMixin):
    """
    Helper class that works with notes.
    """
    def __init__(self, element, page, parent_id):
        self.page = page
        self.browser = page.browser
        self.element = element
        self.id = parent_id

    def wait_for_adder_visibility(self):
        """
        Waiting for visibility of note adder button.
        """
        self.page.wait_for_element_visibility(
            self._bounded_selector(SELECTORS['adder']), 'Adder is visible.'
        )

    def wait_for_viewer_visibility(self):
        """
        Waiting for visibility of note viewer.
        """
        self.page.wait_for_element_visibility(
            self._bounded_selector(SELECTORS['viewer']), 'Note Viewer is visible.'
        )

    def wait_for_editor_visibility(self):
        """
        Waiting for visibility of note editor.
        """
        self.page.wait_for_element_visibility(
            self._bounded_selector(SELECTORS['editor']), 'Note Editor is visible.'
        )

    def wait_for_notes_invisibility(self, text="Notes are hidden"):
        """
        Waiting for invisibility of all notes.
        """
        selector = self._bounded_selector(SELECTORS['popup'])
        self.page.wait_for_element_invisibility(selector, text)

    def select_and_click_adder(self):
        """
        Creates selection for the element and clicks `add note` button.
        """
        ActionChains(self.browser).double_click(self.element).release().perform()
        self.wait_for_adder_visibility()
        self.find_css(SELECTORS['adder']).first.click()
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
        self.find_css(SELECTORS['button_cancel']).first.click()
        self.wait_for_notes_invisibility('Note is canceled.')
        return self

    def save(self):
        """
        Clicks save button.
        """
        self.find_css(SELECTORS['button_save']).first.click()
        self.wait_for_notes_invisibility('Note is saved.')
        self.page.wait_for_ajax()
        return self

    def remove(self):
        """
        Clicks delete button.
        """
        self.find_css(SELECTORS['button_delete']).first.click()
        self.wait_for_notes_invisibility('Note is removed.')
        self.page.wait_for_ajax()
        return self

    def edit(self):
        """
        Clicks edit button.
        """
        self.find_css(SELECTORS['button_edit']).first.click()
        self.wait_for_editor_visibility()
        return self

    @property
    def text(self):
        """
        Returns text of the note.
        """
        self.show().edit()
        text = self.find_css(SELECTORS['textarea']).attrs('value')[0]
        self.cancel()
        return text

    @text.setter
    def text(self, value):
        """
        Sets text for the note.
        """
        self.find_css(SELECTORS['textarea']).first.fill(value)
