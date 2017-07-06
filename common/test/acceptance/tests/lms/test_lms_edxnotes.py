"""
Test LMS Notes
"""
from unittest import skip
import random
from uuid import uuid4
from datetime import datetime
from nose.plugins.attrib import attr
from ..helpers import UniqueCourseTest, EventsTestMixin
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.edxnotes import EdxNotesUnitPage, EdxNotesPage, EdxNotesPageNoContent
from ...fixtures.edxnotes import EdxNotesFixture, Note, Range
from flaky import flaky


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
                                <p><span class="{}">Annotate this!</span></p>
                                <p>Annotate this</p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 2",
                            data="""<p><span class="{}">Annotate this!</span></p>""".format(self.selector)
                        ),
                    ),
                    XBlockFixtureDesc("vertical", "Test Unit 2").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 3",
                            data="""<p><span class="{}">Annotate this!</span></p>""".format(self.selector)
                        ),
                    ),
                ),
                XBlockFixtureDesc("sequential", "Test Subsection 2").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit 3").add_children(
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 4",
                            data="""
                                <p><span class="{}">Annotate this!</span></p>
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
                                <p><span class="{}">Annotate this!</span></p>
                            """.format(self.selector)
                        ),
                        XBlockFixtureDesc(
                            "html",
                            "Test HTML 6",
                            data="""<p><span class="{}">Annotate this!</span></p>""".format(self.selector)
                        ),
                    ),
                ),
            )).install()

        self.addCleanup(self.edxnotes_fixture.cleanup)

        AutoAuthPage(self.browser, username=self.username, email=self.email, course_id=self.course_id).visit()

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


@attr('shard_4')
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

    def edit_tags_in_notes(self, components, tags):
        self.assertGreater(len(components), 0)
        index = 0
        for component in components:
            self.assertGreater(len(component.notes), 0)
            for note in component.edit_note():
                note.tags = tags[index]
                index += 1
        self.assertEqual(index, len(tags), "Number of supplied tags did not match components")

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

    def assert_tags_in_notes(self, notes, expected_tags):
        actual = [note.tags for note in notes]
        expected = [expected_tags[i] for i in xrange(len(notes))]
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

        self.courseware_page.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.create_notes(components)

        components = self.note_unit_page.refresh()
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.courseware_page.go_to_sequential_position(1)
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

        self.courseware_page.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.edit_notes(components)
        self.assert_text_in_notes(self.note_unit_page.notes)

        components = self.note_unit_page.refresh()
        self.assert_text_in_notes(self.note_unit_page.notes)

        self.courseware_page.go_to_sequential_position(1)
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

        self.courseware_page.go_to_sequential_position(2)
        components = self.note_unit_page.components
        self.remove_notes(components)
        self.assert_notes_are_removed(components)

        components = self.note_unit_page.refresh()
        self.assert_notes_are_removed(components)

        self.courseware_page.go_to_sequential_position(1)
        components = self.note_unit_page.components
        self.assert_notes_are_removed(components)

    def test_can_create_note_with_tags(self):
        """
        Scenario: a user of notes can define one with tags
        Given I have a course with 3 annotatable components
        And I open the unit with 2 annotatable components
        When I add a note with tags for the first component
        And I refresh the page
        Then I see that note was correctly stored with its tags
        """
        self.note_unit_page.visit()

        components = self.note_unit_page.components
        for note in components[0].create_note(".{}".format(self.selector)):
            note.tags = ["fruit", "tasty"]

        self.note_unit_page.refresh()
        self.assertEqual(["fruit", "tasty"], self.note_unit_page.notes[0].tags)

    def test_can_change_tags(self):
        """
        Scenario: a user of notes can edit tags on notes
        Given I have a course with 3 components with notes
        When I open the unit with 2 annotatable components
        And I edit tags on the notes for the 2 annotatable components
        Then I see that the tags were correctly changed
        And I again edit tags on the notes for the 2 annotatable components
        And I refresh the page
        Then I see that the tags were correctly changed
        """
        self._add_notes()
        self.note_unit_page.visit()

        components = self.note_unit_page.components
        self.edit_tags_in_notes(components, [["hard"], ["apple", "pear"]])
        self.assert_tags_in_notes(self.note_unit_page.notes, [["hard"], ["apple", "pear"]])

        self.edit_tags_in_notes(components, [[], ["avocado"]])
        self.assert_tags_in_notes(self.note_unit_page.notes, [[], ["avocado"]])

        self.note_unit_page.refresh()
        self.assert_tags_in_notes(self.note_unit_page.notes, [[], ["avocado"]])

    def test_sr_labels(self):
        """
        Scenario: screen reader labels exist for text and tags fields
        Given I have a course with 3 components with notes
        When I open the unit with 2 annotatable components
        And I open the editor for each note
        Then the text and tags fields both have screen reader labels
        """
        self._add_notes()
        self.note_unit_page.visit()

        # First note is in the first annotatable component, will have field indexes 0 and 1.
        for note in self.note_unit_page.components[0].edit_note():
            self.assertTrue(note.has_sr_label(0, 0, "Note"))
            self.assertTrue(note.has_sr_label(1, 1, "Tags (space-separated)"))

        # Second note is in the second annotatable component, will have field indexes 2 and 3.
        for note in self.note_unit_page.components[1].edit_note():
            self.assertTrue(note.has_sr_label(0, 2, "Note"))
            self.assertTrue(note.has_sr_label(1, 3, "Tags (space-separated)"))


@attr('shard_4')
class EdxNotesPageTest(EventsTestMixin, EdxNotesTestMixin):
    """
    Tests for Notes page.
    """
    def _add_notes(self, notes_list):
        self.edxnotes_fixture.create_notes(notes_list)
        self.edxnotes_fixture.install()

    def _add_default_notes(self, tags=None, extra_notes=0):
        """
        Creates 5 test notes by default & number of extra_notes will be created if specified.
        If tags are not specified, will populate the notes with some test tag data.
        If tags are specified, they will be used for each of the 3 notes that have tags.
        """
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        # pylint: disable=attribute-defined-outside-init
        self.raw_note_list = [
            Note(
                usage_id=xblocks[4].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="First note",
                quote="Annotate this",
                updated=datetime(2011, 1, 1, 1, 1, 1, 1).isoformat(),
            ),
            Note(
                usage_id=xblocks[2].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="",
                quote=u"Annotate this",
                updated=datetime(2012, 1, 1, 1, 1, 1, 1).isoformat(),
                tags=["Review", "cool"] if tags is None else tags
            ),
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Third note",
                quote="Annotate this",
                updated=datetime(2013, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=18)],
                tags=["Cool", "TODO"] if tags is None else tags
            ),
            Note(
                usage_id=xblocks[3].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Fourth note",
                quote="",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
                tags=["review"] if tags is None else tags
            ),
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Fifth note",
                quote="Annotate this",
                updated=datetime(2015, 1, 1, 1, 1, 1, 1).isoformat()
            ),
        ]
        if extra_notes > 0:
            for __ in range(extra_notes):
                self.raw_note_list.append(
                    Note(
                        usage_id=xblocks[random.choice([0, 1, 2, 3, 4, 5])].locator,
                        user=self.username,
                        course_id=self.course_fixture._course_key,  # pylint: disable=protected-access
                        text="Fourth note",
                        quote="",
                        updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
                        tags=["review"] if tags is None else tags
                    )
                )
        self._add_notes(self.raw_note_list)

    def assertNoteContent(self, item, text=None, quote=None, unit_name=None, time_updated=None, tags=None):
        """ Verifies the expected properties of the note. """
        self.assertEqual(text, item.text)
        if item.quote is not None:
            self.assertIn(quote, item.quote)
        else:
            self.assertIsNone(quote)
        self.assertEqual(unit_name, item.unit_name)
        self.assertEqual(time_updated, item.time_updated)
        self.assertEqual(tags, item.tags)

    def assertChapterContent(self, item, title=None, subtitles=None):
        """
        Verifies the expected title and subsection titles (subtitles) for the given chapter.
        """
        self.assertEqual(item.title, title)
        self.assertEqual(item.subtitles, subtitles)

    def assertGroupContent(self, item, title=None, notes=None):
        """
        Verifies the expected title and child notes for the given group.
        """
        self.assertEqual(item.title, title)
        self.assertEqual(item.notes, notes)

    def assert_viewed_event(self, view=None):
        """
        Verifies that the correct view event was captured for the Notes page.
        """
        # There will always be an initial event for "Recent Activity" because that is the default view.
        # If view is something besides "Recent Activity", expect 2 events, with the second one being
        # the view name passed in.
        if view == 'Recent Activity':
            view = None
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.course.student_notes.notes_page_viewed'},
            number_of_matches=1 if view is None else 2
        )
        expected_events = [{'event': {'view': 'Recent Activity'}}]
        if view:
            expected_events.append({'event': {'view': view}})
        self.assert_events_match(expected_events, actual_events)

    def assert_unit_link_event(self, usage_id, view):
        """
        Verifies that the correct used_unit_link event was captured for the Notes page.
        """
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.course.student_notes.used_unit_link'},
            number_of_matches=1
        )
        expected_events = [
            {'event': {'component_usage_id': usage_id, 'view': view}}
        ]
        self.assert_events_match(expected_events, actual_events)

    def assert_search_event(self, search_string, number_of_results):
        """
        Verifies that the correct searched event was captured for the Notes page.
        """
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.course.student_notes.searched'},
            number_of_matches=1
        )
        expected_events = [
            {'event': {'search_string': search_string, 'number_of_results': number_of_results}}
        ]
        self.assert_events_match(expected_events, actual_events)

    def _verify_pagination_info(
            self,
            notes_count_on_current_page,
            header_text,
            previous_button_enabled,
            next_button_enabled,
            current_page_number,
            total_pages
    ):
        """
        Verify pagination info
        """
        self.assertEqual(self.notes_page.count(), notes_count_on_current_page)
        self.assertEqual(self.notes_page.get_pagination_header_text(), header_text)

        if total_pages > 1:
            self.assertEqual(self.notes_page.footer_visible, True)
            self.assertEqual(self.notes_page.is_previous_page_button_enabled(), previous_button_enabled)
            self.assertEqual(self.notes_page.is_next_page_button_enabled(), next_button_enabled)
            self.assertEqual(self.notes_page.get_current_page_number(), current_page_number)
            self.assertEqual(self.notes_page.get_total_pages, total_pages)
        else:
            self.assertEqual(self.notes_page.footer_visible, False)

    def search_and_verify(self):
        """
        Add, search and verify notes.
        """
        self._add_default_notes(extra_notes=22)
        self.notes_page.visit()
        # Run the search
        self.notes_page.search("note")
        # No error message appears
        self.assertFalse(self.notes_page.is_error_visible)
        self.assertIn(u"Search Results", self.notes_page.tabs)

        self.assertEqual(self.notes_page.get_total_pages, 2)

    def test_no_content(self):
        """
        Scenario: User can see `No content` message.
        Given I have a course without notes
        When I open Notes page
        Then I see only "You do not have any notes within the course." message
        """
        notes_page_empty = EdxNotesPageNoContent(self.browser, self.course_id)
        notes_page_empty.visit()
        self.assertIn(
            "You have not made any notes in this course yet. Other students in this course are using notes to:",
            notes_page_empty.no_content_text)

    def test_notes_works_correctly_with_xss(self):
        """
        Scenario: Note text & tags should be HTML and JS escaped
        Given I am enrolled in a course with notes enabled
        When I visit the Notes page, with a Notes text and tag containing HTML characters like < and >
        Then the text and tags appear as expected due to having been properly escaped
        """
        xblocks = self.course_fixture.get_nested_xblocks(category="html")
        self._add_notes([
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,  # pylint: disable=protected-access
                text='<script>alert("XSS")</script>',
                quote="quote",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
                tags=['<script>alert("XSS")</script>']
            ),
            Note(
                usage_id=xblocks[1].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,  # pylint: disable=protected-access
                text='<b>bold</b>',
                quote="quote",
                updated=datetime(2014, 2, 1, 1, 1, 1, 1).isoformat(),
                tags=['<i>bold</i>']
            )
        ])
        self.notes_page.visit()

        notes = self.notes_page.notes
        self.assertEqual(len(notes), 2)

        self.assertNoteContent(
            notes[0],
            quote=u"quote",
            text='<b>bold</b>',
            unit_name="Test Unit 1",
            time_updated="Feb 01, 2014 at 01:01 UTC",
            tags=['<i>bold</i>']
        )

        self.assertNoteContent(
            notes[1],
            quote=u"quote",
            text='<script>alert("XSS")</script>',
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2014 at 01:01 UTC",
            tags=['<script>alert("XSS")</script>']
        )

    def test_recent_activity_view(self):
        """
        Scenario: User can view all notes by recent activity.
        Given I have a course with 5 notes
        When I open Notes page
        Then I see 5 notes sorted by the updated date
        And I see correct content in the notes
        And an event has fired indicating that the Recent Activity view was selected
        """
        self._add_default_notes()
        self.notes_page.visit()
        notes = self.notes_page.notes
        self.assertEqual(len(notes), 5)

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[1],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC",
            tags=["review"]
        )

        self.assertNoteContent(
            notes[2],
            quote="Annotate this",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC",
            tags=["Cool", "TODO"]
        )

        self.assertNoteContent(
            notes[3],
            quote=u"Annotate this",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC",
            tags=["Review", "cool"]
        )

        self.assertNoteContent(
            notes[4],
            quote=u"Annotate this",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

        self.assert_viewed_event()

    def test_course_structure_view(self):
        """
        Scenario: User can view all notes by location in Course.
        Given I have a course with 5 notes
        When I open Notes page
        And I switch to "Location in Course" view
        Then I see 2 groups, 3 sections and 5 notes
        And I see correct content in the notes and groups
        And an event has fired indicating that the Location in Course view was selected
        """
        self._add_default_notes()
        self.notes_page.visit().switch_to_tab("structure")

        notes = self.notes_page.notes
        groups = self.notes_page.chapter_groups
        sections = self.notes_page.subsection_groups
        self.assertEqual(len(notes), 5)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(sections), 3)

        self.assertChapterContent(
            groups[0],
            title=u"Test Section 1",
            subtitles=[u"Test Subsection 1", u"Test Subsection 2"]
        )

        self.assertGroupContent(
            sections[0],
            title=u"Test Subsection 1",
            notes=[u"Fifth note", u"Third note", None]
        )

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[1],
            quote=u"Annotate this",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC",
            tags=["Cool", "TODO"]
        )

        self.assertNoteContent(
            notes[2],
            quote=u"Annotate this",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC",
            tags=["Review", "cool"]
        )

        self.assertGroupContent(
            sections[1],
            title=u"Test Subsection 2",
            notes=[u"Fourth note"]
        )

        self.assertNoteContent(
            notes[3],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC",
            tags=["review"]
        )

        self.assertChapterContent(
            groups[1],
            title=u"Test Section 2",
            subtitles=[u"Test Subsection 3"],
        )

        self.assertGroupContent(
            sections[2],
            title=u"Test Subsection 3",
            notes=[u"First note"]
        )

        self.assertNoteContent(
            notes[4],
            quote=u"Annotate this",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

        self.assert_viewed_event('Location in Course')

    def test_tags_view(self):
        """
        Scenario: User can view all notes by associated tags.
        Given I have a course with 5 notes and I am viewing the Notes page
        When I switch to the "Tags" view
        Then I see 4 tag groups
        And I see correct content in the notes and groups
        And an event has fired indicating that the Tags view was selected
        """
        self._add_default_notes()
        self.notes_page.visit().switch_to_tab("tags")

        notes = self.notes_page.notes
        groups = self.notes_page.tag_groups
        self.assertEqual(len(notes), 7)
        self.assertEqual(len(groups), 4)

        # Tag group "cool"
        self.assertGroupContent(
            groups[0],
            title=u"cool (2)",
            notes=[u"Third note", None]
        )

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC",
            tags=["Cool", "TODO"]
        )

        self.assertNoteContent(
            notes[1],
            quote=u"Annotate this",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC",
            tags=["Review", "cool"]
        )

        # Tag group "review"
        self.assertGroupContent(
            groups[1],
            title=u"review (2)",
            notes=[u"Fourth note", None]
        )

        self.assertNoteContent(
            notes[2],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC",
            tags=["review"]
        )

        self.assertNoteContent(
            notes[3],
            quote=u"Annotate this",
            unit_name="Test Unit 2",
            time_updated="Jan 01, 2012 at 01:01 UTC",
            tags=["Review", "cool"]
        )

        # Tag group "todo"
        self.assertGroupContent(
            groups[2],
            title=u"todo (1)",
            notes=["Third note"]
        )

        self.assertNoteContent(
            notes[4],
            quote=u"Annotate this",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC",
            tags=["Cool", "TODO"]
        )

        # Notes with no tags
        self.assertGroupContent(
            groups[3],
            title=u"[no tags] (2)",
            notes=["Fifth note", "First note"]
        )

        self.assertNoteContent(
            notes[5],
            quote=u"Annotate this",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[6],
            quote=u"Annotate this",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

        self.assert_viewed_event('Tags')

    @flaky  # TNL-4590
    def test_easy_access_from_notes_page(self):
        """
        Scenario: Ensure that the link to the Unit works correctly.
        Given I have a course with 5 notes
        When I open Notes page
        And I click on the first unit link
        Then I see correct text on the unit page and a unit link event was fired
        When go back to the Notes page
        And I switch to "Location in Course" view
        And I click on the second unit link
        Then I see correct text on the unit page and a unit link event was fired
        When go back to the Notes page
        And I switch to "Tags" view
        And I click on the first unit link
        Then I see correct text on the unit page and a unit link event was fired
        When go back to the Notes page
        And I run the search with "Fifth" query
        And I click on the first unit link
        Then I see correct text on the unit page  and a unit link event was fired
        """
        def assert_page(note, usage_id, view):
            """ Verify that clicking on the unit link works properly. """
            quote = note.quote
            note.go_to_unit()
            self.courseware_page.wait_for_page()
            self.assertIn(quote, self.courseware_page.xblock_component_html_content())
            self.assert_unit_link_event(usage_id, view)
            self.reset_event_tracking()

        self._add_default_notes()
        self.notes_page.visit()
        # visiting the page results in an ajax request to fetch the notes
        self.notes_page.wait_for_ajax()
        note = self.notes_page.notes[0]
        assert_page(note, self.raw_note_list[4]['usage_id'], "Recent Activity")

        self.notes_page.visit().switch_to_tab("structure")
        # visiting the page results in an ajax request to fetch the notes
        self.notes_page.wait_for_ajax()
        note = self.notes_page.notes[1]
        assert_page(note, self.raw_note_list[2]['usage_id'], "Location in Course")

        self.notes_page.visit().switch_to_tab("tags")
        # visiting the page results in an ajax request to fetch the notes
        self.notes_page.wait_for_ajax()
        note = self.notes_page.notes[0]
        assert_page(note, self.raw_note_list[2]['usage_id'], "Tags")

        self.notes_page.visit().search("Fifth")
        # visiting the page results in an ajax request to fetch the notes
        self.notes_page.wait_for_ajax()

        note = self.notes_page.notes[0]
        assert_page(note, self.raw_note_list[4]['usage_id'], "Search Results")

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
        And an event has fired indicating that the Search Results view was selected
        And an event has fired recording the search that was performed
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
        notes = self.notes_page.notes
        self.assertEqual(len(notes), 4)

        self.assertNoteContent(
            notes[0],
            quote=u"Annotate this",
            text=u"Fifth note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2015 at 01:01 UTC"
        )

        self.assertNoteContent(
            notes[1],
            text=u"Fourth note",
            unit_name="Test Unit 3",
            time_updated="Jan 01, 2014 at 01:01 UTC",
            tags=["review"]
        )

        self.assertNoteContent(
            notes[2],
            quote="Annotate this",
            text=u"Third note",
            unit_name="Test Unit 1",
            time_updated="Jan 01, 2013 at 01:01 UTC",
            tags=["Cool", "TODO"]
        )

        self.assertNoteContent(
            notes[3],
            quote=u"Annotate this",
            text=u"First note",
            unit_name="Test Unit 4",
            time_updated="Jan 01, 2011 at 01:01 UTC"
        )

        self.assert_viewed_event('Search Results')
        self.assert_search_event('note', 4)

    @skip("scroll to tag functionality is disabled")
    def test_scroll_to_tag_recent_activity(self):
        """
        Scenario: Can scroll to a tag group from the Recent Activity view (default view)
        Given I have a course with 5 notes and I open the Notes page
        When I click on a tag associated with a note
        Then the Tags view tab gets focus and I scroll to the section of notes associated with that tag
        """
        self._add_default_notes(["apple", "banana", "kiwi", "pear", "pumpkin", "squash", "zucchini"])
        self.notes_page.visit()
        self._scroll_to_tag_and_verify("pear", 3)

    @skip("scroll to tag functionality is disabled")
    def test_scroll_to_tag_course_structure(self):
        """
        Scenario: Can scroll to a tag group from the Course Structure view
        Given I have a course with 5 notes and I open the Notes page and select the Course Structure view
        When I click on a tag associated with a note
        Then the Tags view tab gets focus and I scroll to the section of notes associated with that tag
        """
        self._add_default_notes(["apple", "banana", "kiwi", "pear", "pumpkin", "squash", "zucchini"])
        self.notes_page.visit().switch_to_tab("structure")
        self._scroll_to_tag_and_verify("squash", 5)

    @skip("scroll to tag functionality is disabled")
    def test_scroll_to_tag_search(self):
        """
        Scenario: Can scroll to a tag group from the Search Results view
        Given I have a course with 5 notes and I open the Notes page and perform a search
        Then the Search view tab opens and gets focus
        And when I click on a tag associated with a note
        Then the Tags view tab gets focus and I scroll to the section of notes associated with that tag
        """
        self._add_default_notes(["apple", "banana", "kiwi", "pear", "pumpkin", "squash", "zucchini"])
        self.notes_page.visit().search("note")
        self._scroll_to_tag_and_verify("pumpkin", 4)

    @skip("scroll to tag functionality is disabled")
    def test_scroll_to_tag_from_tag_view(self):
        """
        Scenario: Can scroll to a tag group from the Tags view
        Given I have a course with 5 notes and I open the Notes page and select the Tag view
        When I click on a tag associated with a note
        Then I scroll to the section of notes associated with that tag
        """
        self._add_default_notes(["apple", "banana", "kiwi", "pear", "pumpkin", "squash", "zucchini"])
        self.notes_page.visit().switch_to_tab("tags")
        self._scroll_to_tag_and_verify("kiwi", 2)

    def _scroll_to_tag_and_verify(self, tag_name, group_index):
        """ Helper method for all scroll to tag tests """
        self.notes_page.notes[1].go_to_tag(tag_name)

        # Because all the notes (with tags) have the same tags, they will end up ordered alphabetically.
        pear_group = self.notes_page.tag_groups[group_index]
        self.assertEqual(tag_name + " (3)", pear_group.title)
        self.assertTrue(pear_group.scrolled_to_top(group_index))

    def test_tabs_behaves_correctly(self):
        """
        Scenario: Tabs behaves correctly.
        Given I have a course with 5 notes
        When I open Notes page
        Then I see only "Recent Activity", "Location in Course", and "Tags" tabs
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
        self.assertEqual(len(self.notes_page.tabs), 3)
        self.assertEqual([u"Recent Activity", u"Location in Course", u"Tags"], self.notes_page.tabs)
        self.notes_page.search("note")
        # We're on Search Results tab
        self.assertEqual(len(self.notes_page.tabs), 4)
        self.assertIn(u"Search Results", self.notes_page.tabs)
        self.assertEqual(len(self.notes_page.notes), 4)
        # We can switch on Recent Activity tab and back.
        self.notes_page.switch_to_tab("recent")
        self.assertEqual(len(self.notes_page.notes), 5)
        self.notes_page.switch_to_tab("structure")
        self.assertEqual(len(self.notes_page.chapter_groups), 2)
        self.assertEqual(len(self.notes_page.notes), 5)
        self.notes_page.switch_to_tab("search")
        self.assertEqual(len(self.notes_page.notes), 4)
        # Can close search results page
        self.notes_page.close_tab()
        self.assertEqual(len(self.notes_page.tabs), 3)
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
                quote="Annotate this",
                updated=datetime(2012, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=14)],
            ),
            Note(
                usage_id=xblocks[2].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="Second note",
                quote="Annotate this",
                updated=datetime(2013, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=14)],
            ),
            Note(
                usage_id=xblocks[0].locator,
                user=self.username,
                course_id=self.course_fixture._course_key,
                text="First note",
                quote="Annotate this",
                updated=datetime(2014, 1, 1, 1, 1, 1, 1).isoformat(),
                ranges=[Range(startOffset=0, endOffset=14)],
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
        self.courseware_page.go_to_sequential_position(2)
        note = self.note_unit_page.notes[0]
        self.assertFalse(note.is_visible)
        self.courseware_page.go_to_sequential_position(1)
        note = self.note_unit_page.notes[0]
        self.assertFalse(note.is_visible)

    def test_page_size_limit(self):
        """
        Scenario: Verify that we can't get notes more than default page size.

        Given that I am a registered user
        And I have a course with 11 notes
        When I open Notes page
        Then I can see notes list contains 10 items
        And I should see paging header and footer with correct data
        And I should see disabled previous button
        And I should also see enabled next button
        """
        self._add_default_notes(extra_notes=21)
        self.notes_page.visit()

        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_pagination_with_single_page(self):
        """
        Scenario: Notes list pagination works as expected for single page
        Given that I am a registered user
        And I have a course with 5 notes
        When I open Notes page
        Then I can see notes list contains 5 items
        And I should see paging header and footer with correct data
        And I should see disabled previous and next buttons
        """
        self._add_default_notes()
        self.notes_page.visit()
        self._verify_pagination_info(
            notes_count_on_current_page=5,
            header_text='Showing 1-5 out of 5 total',
            previous_button_enabled=False,
            next_button_enabled=False,
            current_page_number=1,
            total_pages=1
        )

    def test_next_and_previous_page_button(self):
        """
        Scenario: Next & Previous buttons are working as expected for notes list pagination

        Given that I am a registered user
        And I have a course with 26 notes
        When I open Notes page
        Then I can see notes list contains 25 items
        And I should see paging header and footer with correct data
        And I should see disabled previous button
        And I should see enabled next button

        When I click on next page button in footer
        Then I should be navigated to second page
        And I should see a list with 1 item
        And I should see paging header and footer with correct info
        And I should see enabled previous button
        And I should also see disabled next button

        When I click on previous page button in footer
        Then I should be navigated to first page
        And I should see a list with 25 items
        And I should see paging header and footer with correct info
        And I should see disabled previous button
        And I should also see enabled next button
        """
        self._add_default_notes(extra_notes=21)
        self.notes_page.visit()

        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

        self.notes_page.press_next_page_button()
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )
        self.notes_page.press_previous_page_button()
        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_pagination_with_valid_and_invalid_page_number(self):
        """
        Scenario: Notes list pagination works as expected for valid & invalid page number

        Given that I am a registered user
        And I have a course with 26 notes
        When I open Notes page
        Then I can see notes list contains 25 items
        And I should see paging header and footer with correct data
        And I should see total page value is 2
        When I enter 2 in the page number input
        Then I should be navigated to page 2

        When I enter 3 in the page number input
        Then I should not be navigated away from page 2
        """
        self._add_default_notes(extra_notes=21)
        self.notes_page.visit()

        self.assertEqual(self.notes_page.get_total_pages, 2)

        # test pagination with valid page number
        self.notes_page.go_to_page(2)
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

        # test pagination with invalid page number
        self.notes_page.go_to_page(3)
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

    def test_search_behaves_correctly_with_pagination(self):
        """
        Scenario: Searching behaves correctly with pagination.

        Given that I am a registered user
        And I have a course with 27 notes
        When I open Notes page
        Then I can see notes list with 25 items
        And I should see paging header and footer with correct data
        And previous button is disabled
        And next button is enabled
        When I run the search with "note" query
        Then I see no error message
        And I see that "Search Results" tab appears with 26 notes found
        And an event has fired indicating that the Search Results view was selected
        And an event has fired recording the search that was performed
        """
        self.search_and_verify()
        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

        self.assert_viewed_event('Search Results')
        self.assert_search_event('note', 26)

    def test_search_with_next_and_prev_page_button(self):
        """
        Scenario: Next & Previous buttons are working as expected for search

        Given that I am a registered user
        And I have a course with 27 notes
        When I open Notes page
        Then I can see notes list with 25 items
        And I should see paging header and footer with correct data
        And previous button is disabled
        And next button is enabled

        When I run the search with "note" query
        Then I see that "Search Results" tab appears with 26 notes found
        And an event has fired indicating that the Search Results view was selected
        And an event has fired recording the search that was performed

        When I click on next page button in footer
        Then I should be navigated to second page
        And I should see a list with 1 item
        And I should see paging header and footer with correct info
        And I should see enabled previous button
        And I should also see disabled next button

        When I click on previous page button in footer
        Then I should be navigated to first page
        And I should see a list with 25 items
        And I should see paging header and footer with correct info
        And I should see disabled previous button
        And I should also see enabled next button
        """
        self.search_and_verify()

        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

        self.assert_viewed_event('Search Results')
        self.assert_search_event('note', 26)

        self.notes_page.press_next_page_button()
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )
        self.notes_page.press_previous_page_button()
        self._verify_pagination_info(
            notes_count_on_current_page=25,
            header_text='Showing 1-25 out of 26 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_search_with_valid_and_invalid_page_number(self):
        """
        Scenario: Notes list pagination works as expected for valid & invalid page number

        Given that I am a registered user
        And I have a course with 27 notes
        When I open Notes page
        Then I can see notes list contains 25 items
        And I should see paging header and footer with correct data
        And I should see total page value is 2

        When I run the search with "note" query
        Then I see that "Search Results" tab appears with 26 notes found
        And an event has fired indicating that the Search Results view was selected
        And an event has fired recording the search that was performed

        When I enter 2 in the page number input
        Then I should be navigated to page 2

        When I enter 3 in the page number input
        Then I should not be navigated away from page 2
        """
        self.search_and_verify()

        # test pagination with valid page number
        self.notes_page.go_to_page(2)
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

        # test pagination with invalid page number
        self.notes_page.go_to_page(3)
        self._verify_pagination_info(
            notes_count_on_current_page=1,
            header_text='Showing 26-26 out of 26 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )


@attr('shard_4')
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
        Then I see that the new note is shown
        """
        note_1 = self.note_unit_page.notes[0]
        note_2 = self.note_unit_page.notes[1]

        note_1.click_on_highlight()
        self.note_unit_page.move_mouse_to("body")
        self.assertTrue(note_1.is_visible)

        note_2.click_on_highlight()
        self.assertFalse(note_1.is_visible)
        self.assertTrue(note_2.is_visible)


@attr('shard_4')
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
        self.courseware_page.go_to_sequential_position(2)
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
        self.courseware_page.go_to_sequential_position(2)
        self.assertGreater(len(self.note_unit_page.notes), 0)
        self.course_nav.go_to_section(u"Test Section 1", u"Test Subsection 2")
        self.assertGreater(len(self.note_unit_page.notes), 0)
