import os
from uuid import uuid4
from datetime import datetime
from unittest import skipUnless
from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.edxnotes import EdxNotesUnitPage, EdxNotesPage
from ...fixtures.edxnotes import EdxNotesFixture, Note, Range


@skipUnless(os.environ.get("FEATURE_EDXNOTES"), "Requires Student Notes feature to be enabled")
class EdxNotesTestMixin(UniqueCourseTest):
    """
    Creates a course with initial data and contains useful helper methods.
    """
    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(EdxNotesTestMixin, self).setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.note_unit_page = EdxNotesUnitPage(self.browser, self.course_id)
        self.notes_page = EdxNotesPage(self.browser, self.course_id)

        self.username = str(uuid4().hex)[:5]
        self.email = "{}@email.com".format(self.username)

        self.selector = "annotate-id"
        self.edxnotes_fixture = EdxNotesFixture()
        self.course_fixture = CourseFixture(
            self.course_info["org"], self.course_info["number"],
            self.course_info["run"], self.course_info["display_name"]
        )

        self.course_fixture.add_advanced_settings({
            u"edxnotes": {u"value": True}
        })

        self.course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section 1").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection 1").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit 1").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 1",
                            data="""
                                <p><span class="{}">Annotate this text!</span></p>
                                <p>Annotate this text</p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 2",
                            data="""<p><span class="{}">Annotate this text!</span></p>""".format(self.selector)
                        ),
                    ),
                    XBlockFixtureDesc("vertical", "Test Unit 2").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 3",
                            data="""<p><span class="{}">Annotate this text!</span></p>""".format(self.selector)
                        ),
                    ),
                ),
                XBlockFixtureDesc("sequential", "Test Subsection 2").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit 3").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 4",
                            data="""
                                <p><span class="{}">Annotate this text!</span></p>
                            """.format(self.selector)
                        ),
                    ),
                ),
            ),
            XBlockFixtureDesc("chapter", "Test Section 2").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection 3").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit 4").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 5",
                            data="""
                                <p><span class="{}">Annotate this text!</span></p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 6",
                            data="""<p><span class="{}">Annotate this text!</span></p>""".format(self.selector)
                        ),
                    ),
                ),
            )).install()

        AutoAuthPage(self.browser, username=self.username, email=self.email, course_id=self.course_id).visit()

    def tearDown(self):
        self.edxnotes_fixture.cleanup()

    def _add_notes(self):
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        notes_list = []
        for index, xblock in enumerate(xblocks):
            notes_list.append(
                Note(
                    user=self.username,
                    usage_id=xblock.locator,
                    course_id=self.course_fixture._course_key,
                    ranges=[Range(startOffset=index, endOffset=index + 5)]
                )
            )

        self.edxnotes_fixture.create_notes(notes_list)
        self.edxnotes_fixture.install()


class EdxNotesDefaultInteractionsTest(EdxNotesTestMixin):
    """
    Tests for creation, editing, deleting annotations inside annotatable components in LMS.
    """
    def create_notes(self, components, offset=0):
        self.assertGreater(len(components), 0)
        index = offset
        for component in components:
            for note in component.create_note(".{}".format(self.selector)):
                note.text = "TEST TEXT {}".format(index)
                index += 1

    def edit_notes(self, components, offset=0):
        self.assertGreater(len(components), 0)
        index = offset
        for component in components:
            self.assertGreater(len(component.notes), 0)
            for note in component.edit_note():
                note.text = "TEST TEXT {}".format(index)
                index += 1

    def remove_notes(self, components):
        self.assertGreater(len(components), 0)
        for component in components:
            self.assertGreater(len(component.notes), 0)
            component.remove_note()

    def assert_notes_are_removed(self, components):
        for component in components:
            self.assertEqual(0, len(component.notes))

    def assert_text_in_notes(self, notes):
        actual = [note.text for note in notes]
        expected = ["TEST TEXT {}".format(i) for i in xrange(len(notes))]
        self.assertEqual(expected, actual)

    def test_can_create_notes(self):
        """
        Scenario: User can create notes.
        Given I have a course with 3 annotatable components
        And I open the unit with 2 annotatable components
        When I add 2 notes for the first component and 1 note for the second
        Then I see that notes were correctly created
        When I change sequential position to "2"
        And I add note for the annotatable component on the page
        Then I see that note was correctly created
        When I refresh the page
        Then I see that note was correctly stored
        When I change sequential position to "1"
        Then I see that notes were correctly stored on the page
        """
        self.note_unit_page.visit()

        components = self.note_unit_page.components
        self.create_notes(components)
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.create_notes(components)

        components = self.note_unit_page.refresh()
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_unit_page.components
        self.assert_text_in_notes(self.note_unit_page.notes)

    def test_can_edit_notes(self):
        """
        Scenario: User can edit notes.
        Given I have a course with 3 components with notes
        And I open the unit with 2 annotatable components
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
        self.note_unit_page.visit()

        components = self.note_unit_page.components
        self.edit_notes(components)
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.edit_notes(components)
        self.assert_text_in_notes(self.note_unit_page.notes)

        components = self.note_unit_page.refresh()
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_unit_page.components
        self.assert_text_in_notes(self.note_unit_page.notes)

    def test_can_delete_notes(self):
        """
        Scenario: User can delete notes.
        Given I have a course with 3 components with notes
        And I open the unit with 2 annotatable components
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
        self.note_unit_page.visit()

        components = self.note_unit_page.components
        self.remove_notes(components)
        self.assert_notes_are_removed(components)

        self.course_nav.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.remove_notes(components)
        self.assert_notes_are_removed(components)

        components = self.note_unit_page.refresh()
        self.assert_notes_are_removed(components)

        self.course_nav.go_to_sequential_position(1)
        components = self.note_unit_page.components
        self.assert_notes_are_removed(components)


class EdxNotesPageTest(EdxNotesTestMixin):
    """
    Tests for Notes page.
    """
    def _add_notes(self, notes_list):
        self.edxnotes_fixture.create_notes(notes_list)
        self.edxnotes_fixture.install()

    def _add_default_notes(self):
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        self._add_notes([
            Note(
                usage_id=xblocks[4].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="First note",
                quote="Annotate this text",
                updated=datetime(2011, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
            Note(
                usage_id=xblocks[2].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="",
                quote=u"Annotate this text",
                updated=datetime(2012, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Third note",
                quote="Annotate this text",
                updated=datetime(2013, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=18)],
            ),
            Note(
                usage_id=xblocks[3].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Fourth note",
                quote="",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Fifth note",
                quote="Annotate this text",
                updated=datetime(2015, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
        ])

    def assertNoteContent(self, item, text=None, quote=None, unit_name=None, time_updated=None):
        if item.text is not None:
            self.assertEqual(text, item.text)
        else:
            self.assertIsNone(text)
        if item.quote is not None:
            self.assertIn(quote, item.quote)
        else:
            self.assertIsNone(quote)
        self.assertEqual(unit_name, item.unit_name)
        self.assertEqual(time_updated, item.time_updated)

    def assertGroupContent(self, item, title=None, subtitles=None):
        self.assertEqual(item.title, title)
        self.assertEqual(item.subtitles, subtitles)

    def assertSectionContent(self, item, title=None, notes=None):
        self.assertEqual(item.title, title)
        self.assertEqual(item.notes, notes)

    def test_no_content(self):
        """
        Scenario: User can see `No content` message.
        Given I have a course without notes
        When I open Notes page
        Then I see only "You do not have any notes within the course." message
        """
        self.notes_page.visit()
        self.assertIn(
            "You have not made any notes in this course yet. Other students in this course are using notes to:",
            self.notes_page.no_content_text)

    def test_recent_activity_view(self):
        """
        Scenario: User can view all notes by recent activity.
        Given I have a course with 5 notes
        When I open Notes page
        Then I see 5 notes sorted by the updated date
        And I see correct content in the notes
        """
        self._add_default_notes()
        self.notes_page.visit()
        notes = self.notes_page.notes
        self.assertEqual(len(notes), 5)

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this text",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[1],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[2],
            quote="Annotate this text",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[3],
            quote=u"Annotate this text",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[4],
            quote=u"Annotate this text",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

    def test_course_structure_view(self):
        """
        Scenario: User can view all notes by location in Course.
        Given I have a course with 5 notes
        When I open Notes page
        And I switch to "Location in Course" view
        Then I see 2 groups, 3 sections and 5 notes
        And I see correct content in the notes and groups
        """
        self._add_default_notes()
        self.notes_page.visit().switch_to_tab("structure")

        notes = self.notes_page.notes
        groups = self.notes_page.groups
        sections = self.notes_page.sections
        self.assertEqual(len(notes), 5)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(sections), 3)

        self.assertGroupContent(
            groups[0],
            title=u"Test Section 1",
            subtitles=[u"Test Subsection 1", u"Test Subsection 2"]
        )

        self.assertSectionContent(
            sections[0],
            title=u"Test Subsection 1",
            notes=[u"Fifth note", u"Third note", None]
        )

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this text",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[1],
            quote=u"Annotate this text",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[2],
            quote=u"Annotate this text",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC"
        )

        self.assertSectionContent(
            sections[1],
            title=u"Test Subsection 2",
            notes=[u"Fourth note"]
        )

        self.assertNoteContent(
            notes[3],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC"
        )

        self.assertGroupContent(
            groups[1],
            title=u"Test Section 2",
            subtitles=[u"Test Subsection 3"],
        )

        self.assertSectionContent(
            sections[2],
            title=u"Test Subsection 3",
            notes=[u"First note"]
        )

        self.assertNoteContent(
            notes[4],
            quote=u"Annotate this text",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

    def test_easy_access_from_notes_page(self):
        """
        Scenario: Ensure that the link to the Unit works correctly.
        Given I have a course with 5 notes
        When I open Notes page
        And I click on the first unit link
        Then I see correct text on the unit page
        When go back to the Notes page
        And I switch to "Location in Course" view
        And I click on the second unit link
        Then I see correct text on the unit page
        When go back to the Notes page
        And I run the search with "Fifth" query
        And I click on the first unit link
        Then I see correct text on the unit page
        """
        def assert_page(note):
            quote = note.quote
            note.go_to_unit()
            self.courseware_page.wait_for_page()
            self.assertIn(quote, self.courseware_page.xblock_component_html_content())

        self._add_default_notes()
        self.notes_page.visit()
        note = self.notes_page.notes[0]
        assert_page(note)

        self.notes_page.visit().switch_to_tab("structure")
        note = self.notes_page.notes[1]
        assert_page(note)

        self.notes_page.visit().search("Fifth")
        note = self.notes_page.notes[0]
        assert_page(note)

    def test_search_behaves_correctly(self):
        """
        Scenario: Searching behaves correctly.
        Given I have a course with 5 notes
        When I open Notes page
        When I run the search with "   " query
        Then I see the following error message "Please enter a term in the search field."
        And I do not see "Search Results" tab
        When I run the search with "note" query
        Then I see that error message disappears
        And I see that "Search Results" tab appears with 4 notes found
        """
        self._add_default_notes()
        self.notes_page.visit()
        # Run the search with whitespaces only
        self.notes_page.search("   ")
        # Displays error message
        self.assertTrue(self.notes_page.is_error_visible)
        self.assertEqual(self.notes_page.error_text, u"Please enter a term in the search field.")
        # Search results tab does not appear
        self.assertNotIn(u"Search Results", self.notes_page.tabs)
        # Run the search with correct query
        self.notes_page.search("note")
        # Error message disappears
        self.assertFalse(self.notes_page.is_error_visible)
        self.assertIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.notes), 4)

    def test_tabs_behaves_correctly(self):
        """
        Scenario: Tabs behaves correctly.
        Given I have a course with 5 notes
        When I open Notes page
        Then I see only "Recent Activity" and "Location in Course" tabs
        When I run the search with "note" query
        And I see that "Search Results" tab appears with 4 notes found
        Then I switch to "Recent Activity" tab
        And I see all 5 notes
        Then I switch to "Location in Course" tab
        And I see all 2 groups and 5 notes
        When I switch back to "Search Results" tab
        Then I can still see 4 notes found
        When I close "Search Results" tab
        Then I see that "Recent Activity" tab becomes active
        And "Search Results" tab disappears
        And I see all 5 notes
        """
        self._add_default_notes()
        self.notes_page.visit()

        # We're on Recent Activity tab.
        self.assertEqual(len(self.notes_page.tabs), 2)
        self.assertEqual([u"Recent Activity", u"Location in Course"], self.notes_page.tabs)
        self.notes_page.search("note")
        # We're on Search Results tab
        self.assertEqual(len(self.notes_page.tabs), 3)
        self.assertIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.notes), 4)
        # We can switch on Recent Activity tab and back.
        self.notes_page.switch_to_tab("recent")
        self.assertEqual(len(self.notes_page.notes), 5)
        self.notes_page.switch_to_tab("structure")
        self.assertEqual(len(self.notes_page.groups), 2)
        self.assertEqual(len(self.notes_page.notes), 5)
        self.notes_page.switch_to_tab("search")
        self.assertEqual(len(self.notes_page.notes), 4)
        # Can close search results page
        self.notes_page.close_tab("search")
        self.assertEqual(len(self.notes_page.tabs), 2)
        self.assertNotIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.notes), 5)

    def test_open_note_when_accessed_from_notes_page(self):
        """
        Scenario: Ensure that the link to the Unit opens a note only once.
        Given I have a course with 2 sequentials that contain respectively one note and two notes
        When I open Notes page
        And I click on the first unit link
        Then I see the note opened on the unit page
        When I switch to the second sequential
        I do not see any note opened
        When I switch back to first sequential
        I do not see any note opened
        """
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        self._add_notes([
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Third note",
                quote="Annotate this text",
                updated=datetime(2012, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=19)],
            ),
            Note(
                usage_id=xblocks[2].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Second note",
                quote="Annotate this text",
                updated=datetime(2013, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=19)],
            ),
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="First note",
                quote="Annotate this text",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=19)],
            ),
        ])
        self.notes_page.visit()
        item = self.notes_page.notes[0]
        item.go_to_unit()
        self.courseware_page.wait_for_page()
        note = self.note_unit_page.notes[0]
        self.assertTrue(note.is_visible)
        note = self.note_unit_page.notes[1]
        self.assertFalse(note.is_visible)
        self.course_nav.go_to_sequential_position(2)
        note = self.note_unit_page.notes[0]
        self.assertFalse(note.is_visible)
        self.course_nav.go_to_sequential_position(1)
        note = self.note_unit_page.notes[0]
        self.assertFalse(note.is_visible)


class EdxNotesToggleSingleNoteTest(EdxNotesTestMixin):
    """
    Tests for toggling single annotation.
    """

    def setUp(self):
        super(EdxNotesToggleSingleNoteTest, self).setUp()
        self._add_notes()
        self.note_unit_page.visit()

    def test_can_toggle_by_clicking_on_highlighted_text(self):
        """
        Scenario: User can toggle a single note by clicking on highlighted text.
        Given I have a course with components with notes
        When I click on highlighted text
        And I move mouse out of the note
        Then I see that the note is still shown
        When I click outside the note
        Then I see the the note is closed
        """
        note = self.note_unit_page.notes[0]

        note.click_on_highlight()
        self.note_unit_page.move_mouse_to("body")
        self.assertTrue(note.is_visible)
        self.note_unit_page.click("body")
        self.assertFalse(note.is_visible)

    def test_can_toggle_by_clicking_on_the_note(self):
        """
        Scenario: User can toggle a single note by clicking on the note.
        Given I have a course with components with notes
        When I click on the note
        And I move mouse out of the note
        Then I see that the note is still shown
        When I click outside the note
        Then I see the the note is closed
        """
        note = self.note_unit_page.notes[0]

        note.show().click_on_viewer()
        self.note_unit_page.move_mouse_to("body")
        self.assertTrue(note.is_visible)
        self.note_unit_page.click("body")
        self.assertFalse(note.is_visible)

    def test_interaction_between_notes(self):
        """
        Scenario: Interactions between notes works well.
        Given I have a course with components with notes
        When I click on highlighted text in the first component
        And I move mouse out of the note
        Then I see that the note is still shown
        When I click on highlighted text in the second component
        Then I do not see any notes
        When I click again on highlighted text in the second component
        Then I see appropriate note
        """
        note_1 = self.note_unit_page.notes[0]
        note_2 = self.note_unit_page.notes[1]

        note_1.click_on_highlight()
        self.note_unit_page.move_mouse_to("body")
        self.assertTrue(note_1.is_visible)

        note_2.click_on_highlight()
        self.assertFalse(note_1.is_visible)
        self.assertFalse(note_2.is_visible)

        note_2.click_on_highlight()
        self.assertTrue(note_2.is_visible)


class EdxNotesToggleNotesTest(EdxNotesTestMixin):
    """
    Tests for toggling visibility of all notes.
    """

    def setUp(self):
        super(EdxNotesToggleNotesTest, self).setUp()
        self._add_notes()
        self.note_unit_page.visit()

    def test_can_disable_all_notes(self):
        """
        Scenario: User can disable all notes.
        Given I have a course with components with notes
        And I open the unit with annotatable components
        When I click on "Show notes" checkbox
        Then I do not see any notes on the sequential position
        When I change sequential position to "2"
        Then I still do not see any notes on the sequential position
        When I go to "Test Subsection 2" subsection
        Then I do not see any notes on the subsection
        """
        # Disable all notes
        self.note_unit_page.toggle_visibility()
        self.assertEqual(len(self.note_unit_page.notes), 0)
        self.course_nav.go_to_sequential_position(2)
        self.assertEqual(len(self.note_unit_page.notes), 0)
        self.course_nav.go_to_section(u"Test Section 1", u"Test Subsection 2")
        self.assertEqual(len(self.note_unit_page.notes), 0)

    def test_can_reenable_all_notes(self):
        """
        Scenario: User can toggle notes visibility.
        Given I have a course with components with notes
        And I open the unit with annotatable components
        When I click on "Show notes" checkbox
        Then I do not see any notes on the sequential position
        When I click on "Show notes" checkbox again
        Then I see that all notes appear
        When I change sequential position to "2"
        Then I still can see all notes on the sequential position
        When I go to "Test Subsection 2" subsection
        Then I can see all notes on the subsection
        """
        # Disable notes
        self.note_unit_page.toggle_visibility()
        self.assertEqual(len(self.note_unit_page.notes), 0)
        # Enable notes to make sure that I can enable notes without refreshing
        # the page.
        self.note_unit_page.toggle_visibility()
        self.assertGreater(len(self.note_unit_page.notes), 0)
        self.course_nav.go_to_sequential_position(2)
        self.assertGreater(len(self.note_unit_page.notes), 0)
        self.course_nav.go_to_section(u"Test Section 1", u"Test Subsection 2")
        self.assertGreater(len(self.note_unit_page.notes), 0)
