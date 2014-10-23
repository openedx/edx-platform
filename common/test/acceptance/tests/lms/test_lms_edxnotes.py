from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.edxnotes import EdxNotesUnitPage
from ...fixtures.edxnotes import EdxNotesFixture, Note, Range


class EdxNotesTest(UniqueCourseTest):
    """
    Tests for annotation inside HTML components in LMS.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(EdxNotesTest, self).setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.note_page = EdxNotesUnitPage(self.browser, self.course_id)

        self.edxnotes_fix = EdxNotesFixture()
        self.course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.selector = "annotate-id"
        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Vertical').add_children(
                        XBlockFixtureDesc(
                            'html',
                            'Test HTML 1',
                            data="""
                                <p><span class="{0}">Annotate</span> this text!</p>
                                <p>Annotate this <span class="{0}">text</span></p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            'html',
                            'Test HTML 2',
                            data="""<p>Annotate <span class="{}">this text!</span></p>""".format(self.selector)
                        ),
                    ),
                    XBlockFixtureDesc(
                        'html',
                        'Test HTML 3',
                        data="""<p><span class="{}">Annotate this text!</span></p>""".format(self.selector)
                    ),
                ),
            )).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def _add_notes(self):
        xblocks = self.course_fix.get_nested_xblocks(category="html")
        for index, xblock in enumerate(xblocks):
            self.edxnotes_fix.create_note(
                Note(
                    usage_id=xblock.locator,
                    user="edx_user",
                    course_id=self.course_fix._course_key,
                    ranges=[Range(startOffset=index, endOffset=index + 5)]
                )
            )
        self.edxnotes_fix.install()

    def create_notes(self, components, offset=0):
        self.assertGreater(len(components), 0)
        index = offset
        for component in components:
            for note in component.create_note(".annotate-id"):
                note.text = 'TEST TEXT {}'.format(index)
                index += 1

    def edit_notes(self, components, offset=0):
        self.assertGreater(len(components), 0)
        index = offset
        for component in components:
            for note in component.edit_note():
                note.text = 'TEST TEXT {}'.format(index)
                index += 1

    def remove_notes(self, components):
        self.assertGreater(len(components), 0)
        for component in components:
            component.remove_note()

    def assert_notes_are_removed(self, components):
        for component in components:
            self.assertEqual(0, len(component.notes))

    def assert_text_in_notes(self, components, offset=0):
        index = offset
        for component in components:
            actual = [note.text for note in component.notes]
            expected = ['TEST TEXT {}'.format(i + index) for i in xrange(len(actual))]
            index += len(actual)
            self.assertItemsEqual(expected, actual)

    def test_can_create_notes(self):
        """
        Scenario: User can create notes.
        Given I have a course with 3 annotatatble components
        And I open the unit with 2 annotatatble components
        When I add 2 notes for the first component and 1 note for the second
        Then I see that notes were correctly created
        When I change sequential position to "2"
        And I add note for the annotatatble component on the page
        Then I see that note was correctly created
        When I refresh the page
        Then I see that note was correctly stored
        When I change sequential position to "1"
        Then I see that notes were correctly stored on the page
        """
        self.note_page.visit()

        components = self.note_page.components
        self.create_notes(components)
        self.assert_text_in_notes(components)
        offset = len(self.note_page.notes)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_page.components
        self.create_notes(components, offset)
        self.assert_text_in_notes(components, offset)

        components = self.note_page.refresh()
        self.assert_text_in_notes(components, offset)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_page.components
        self.assert_text_in_notes(components)

    def test_can_edit_notes(self):
        """
        Scenario: User can edit notes.
        Given I have a course with 3 components with notes
        And I open the unit with 2 annotatatble components
        When I change text in the notes
        Then I see that notes were correctly changed
        When I change sequential position to "2"
        And I change the note on the page
        Then I see that note was correctly changed
        When I refresh the page
        Then I see that edited note was correctly stored
        When I change sequential position to "1"
        Then I see that edited notes were correctly stored on the page
        """
        self._add_notes()
        self.note_page.visit()

        components = self.note_page.components
        self.edit_notes(components)
        self.assert_text_in_notes(components)
        offset = len(self.note_page.notes)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_page.components
        self.edit_notes(components, offset)
        self.assert_text_in_notes(components, offset)

        components = self.note_page.refresh()
        self.assert_text_in_notes(components, offset)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_page.components
        self.assert_text_in_notes(components)

    def test_can_delete_notes(self):
        """
        Scenario: User can delete notes.
        Given I have a course with 3 components with notes
        And I open the unit with 2 annotatatble components
        When I remove all notes on the page
        Then I do not see any notes on the page
        When I change sequential position to "2"
        And I remove all notes on the page
        Then I do not see any notes on the page
        When I refresh the page
        Then I do not see any notes on the page
        When I change sequential position to "1"
        Then I do not see any notes on the page
        """
        self._add_notes()
        self.note_page.visit()

        components = self.note_page.components
        self.remove_notes(components)
        self.assert_notes_are_removed(components)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_page.components
        self.remove_notes(components)
        self.assert_notes_are_removed(components)

        components = self.note_page.refresh()
        self.assert_notes_are_removed(components)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_page.components
        self.assert_notes_are_removed(components)
