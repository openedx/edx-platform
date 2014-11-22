from uuid import uuid4
from datetime import datetime
from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.edxnotes import EdxNotesUnitPage, EdxNotesPage
from ...fixtures.edxnotes import EdxNotesFixture, Note, Range


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
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Vertical").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 1",
                            data="""
                                <p><span class="{0}">Annotate</span> this text!</p>
                                <p>Annotate this text</p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 2",
                            data="""<p>Annotate <span class="{}">this text!</span></p>""".format(self.selector)
                        ),
                    ),
                    XBlockFixtureDesc(
                        "html",
                        "Test HTML 3",
                        data="""<p><span class="{}">Annotate this text!</span></p>""".format(self.selector)
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


class EdxNotesPageTest(UniqueCourseTest):
    """
    Tests for Notes page.
    """
    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(EdxNotesPageTest, self).setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.notes_page = EdxNotesPage(self.browser, self.course_id)

        self.username = str(uuid4().hex)[:5]
        self.email = "{}@email.com".format(self.username)

        self.edxnotes_fixture = EdxNotesFixture()
        self.course_fixture = CourseFixture(
            self.course_info["org"], self.course_info["number"],
            self.course_info["run"], self.course_info["display_name"]
        )

        self.course_fixture.add_advanced_settings({
            u"edxnotes": {u"value": True}
        })

        self.course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit 1").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 1",
                            data="""<p>Annotate this text!</p>"""
                        ),
                    ),
                    XBlockFixtureDesc("vertical", "Test Unit 2").add_children(
                        XBlockFixtureDesc("vertical", "Test Unit 2").add_children(
                            XBlockFixtureDesc(
                                "html",
                                "Test HTML 2",
                                data="""<p>Third text!</p>"""
                            ),
                        ),
                    ),
                ),
            )).install()

        AutoAuthPage(self.browser, username=self.username, email=self.email, course_id=self.course_id).visit()

    def tearDown(self):
        self.edxnotes_fixture.cleanup()

    def _add_notes(self, notes_list):
        self.edxnotes_fixture.create_notes(notes_list)
        self.edxnotes_fixture.install()

    def _add_default_notes(self):
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        self._add_notes([
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Third text",
                quote="",
                updated=datetime(2012, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Annotate this text!",
                quote="Second note",
                updated=datetime(2013, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=19)],
            ),
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="",
                quote="First note",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
        ])

    def test_no_content(self):
        """
        Scenario: User can see `No content` message.
        Given I have a course without notes
        When I open Notes page
        Then I see only "You do not have any notes within the course." message
        """
        self.notes_page.visit()
        self.assertEqual("You do not have any notes within the course.", self.notes_page.no_content_text)

    def test_recent_activity_view(self):
        """
        Scenario: User can view all notes by recent activity.
        Given I have a course with 3 notes
        When I open Notes page
        Then I see 3 notes sorted by the day
        And I see correct content in the notes
        """
        self._add_default_notes()

        def assertContent(item, text=None, quote=None, unit_name=None, time_updated=None):
            self.assertEqual(item.text, text)
            self.assertEqual(item.quote, quote)
            self.assertEqual(item.unit_name, unit_name)
            self.assertEqual(item.time_updated, time_updated)
            if text is not None and quote is not None:
                self.assertEqual(item.title_highlighted, "HIGHLIGHTED & NOTED IN:")
            elif text is not None:
                self.assertEqual(item.title_highlighted, "HIGHLIGHTED IN:")
            elif quote is not None:
                self.assertEqual(item.title_highlighted, "NOTED IN:")

        self.notes_page.visit()
        items = self.notes_page.children
        self.assertEqual(len(items), 3)
        assertContent(
            items[0],
            quote=u"First note",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2014 at 01:01 UTC"
        )

        assertContent(
            items[1],
            text="Annotate this text!",
            quote=u"Second note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC"
        )

        assertContent(
            items[2],
            text=u"Third text",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC"
        )

    def test_easy_access_from_notes_page(self):
        """
        Scenario: Ensure that the link to the Unit works correctly.
        Given I have a course with 3 notes
        When I open Notes page
        And I click on the second unit link
        Then I see correct text on the unit page
        """
        self._add_default_notes()
        self.notes_page.visit()
        item = self.notes_page.children[1]
        text = item.text
        item.go_to_unit()
        self.courseware_page.wait_for_page()
        self.assertIn(text, self.courseware_page.xblock_component_html_content())

    def test_search_behaves_correctly(self):
        """
        Scenario: Searching behaves correctly.
        Given I have a course with 3 notes
        When I open Notes page
        When I run the search with "   " query
        Then I see the following error message "Search field cannot be blank."
        And I still can see only "Recent Activity" tab
        When I run the search with "text" query
        Then I see that error message disappears
        And I see that "Search Results" tab appears with 2 notes found
        """
        self._add_default_notes()
        self.notes_page.visit()
        # Run the search with whitespaces only
        self.notes_page.search("   ")
        # Displays error message
        self.assertTrue(self.notes_page.is_error_visible)
        self.assertEqual(self.notes_page.error_text, u"Search field cannot be blank.")
        # Search results tab does not appear
        self.assertEqual(len(self.notes_page.tabs), 1)
        # Run the search with correct query
        self.notes_page.search("text")
        # Error message disappears
        self.assertFalse(self.notes_page.is_error_visible)
        self.assertIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.children), 2)

    def test_tabs_behaves_correctly(self):
        """
        Scenario: Tabs behaves correctly.
        Given I have a course with 3 notes
        When I open Notes page
        Then I see only "Recent Activity" tab with 3 notes
        When I run the search with "text" query
        And I see that "Search Results" tab appears with 2 notes found
        Then I switch to "Recent Activity" tab
        And I see all 3 notes
        When I switch back to "Search Results" tab
        Then I can still see 2 notes found
        When I close "Search Results" tab
        Then I see that "Recent Activity" tab becomes active
        And "Search Results" tab disappears
        And I see all 3 notes
        """
        self._add_default_notes()
        self.notes_page.visit()

        # We're on Recent Activity tab.
        self.assertEqual(len(self.notes_page.tabs), 1)
        self.assertIn(u"Recent Activity", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.children), 3)
        self.notes_page.search("text")
        # We're on Search Results tab
        self.assertEqual(len(self.notes_page.tabs), 2)
        self.assertIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.children), 2)
        # We can switch on Recent Activity tab and back.
        self.notes_page.switch_to_tab("recent")
        self.assertEqual(len(self.notes_page.children), 3)
        self.notes_page.switch_to_tab("search")
        self.assertEqual(len(self.notes_page.children), 2)
        # Can close search results page
        self.notes_page.close_tab("search")
        self.assertEqual(len(self.notes_page.tabs), 1)
        self.assertIn(u"Recent Activity", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.children), 3)


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
