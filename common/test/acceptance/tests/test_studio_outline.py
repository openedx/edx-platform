"""
Acceptance tests for studio related to the outline page.
"""
from nose.plugins.attrib import attr

from datetime import datetime, timedelta
import itertools
from pytz import UTC
from bok_choy.promise import EmptyPromise

from ..pages.studio.overview import CourseOutlinePage, ContainerPage, ExpandCollapseLinkState
from ..pages.studio.utils import add_discussion
from ..pages.lms.courseware import CoursewarePage
from ..fixtures.course import XBlockFixtureDesc

from .base_studio_test import StudioCourseTest
from .helpers import load_data_str
from ..pages.lms.progress import ProgressPage


SECTION_NAME = 'Test Section'
SUBSECTION_NAME = 'Test Subsection'
UNIT_NAME = 'Test Unit'


class CourseOutlineTest(StudioCourseTest):
    """
    Base class for all course outline tests
    """

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(CourseOutlineTest, self).setUp()
        self.course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """ Install a course with sections/problems, tabs, updates, and handouts """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', UNIT_NAME).add_children(
                        XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                        XBlockFixtureDesc('html', 'Test HTML Component'),
                        XBlockFixtureDesc('discussion', 'Test Discussion Component')
                    )
                )
            )
        )


@attr('shard_2')
class WarningMessagesTest(CourseOutlineTest):
    """
    Feature: Warning messages on sections, subsections, and units
    """

    __test__ = True

    STAFF_ONLY_WARNING = 'Contains staff only content'
    LIVE_UNPUBLISHED_WARNING = 'Unpublished changes to live content'
    FUTURE_UNPUBLISHED_WARNING = 'Unpublished changes to content that will release in the future'
    NEVER_PUBLISHED_WARNING = 'Unpublished units will not be released'

    class PublishState:
        NEVER_PUBLISHED = 1
        UNPUBLISHED_CHANGES = 2
        PUBLISHED = 3
        VALUES = [NEVER_PUBLISHED, UNPUBLISHED_CHANGES, PUBLISHED]

    class UnitState:
        """ Represents the state of a unit """

        def __init__(self, is_released, publish_state, is_locked):
            """ Creates a new UnitState with the given properties """
            self.is_released = is_released
            self.publish_state = publish_state
            self.is_locked = is_locked

        @property
        def name(self):
            """ Returns an appropriate name based on the properties of the unit """
            result = "Released " if self.is_released else "Unreleased "
            if self.publish_state == WarningMessagesTest.PublishState.NEVER_PUBLISHED:
                result += "Never Published "
            elif self.publish_state == WarningMessagesTest.PublishState.UNPUBLISHED_CHANGES:
                result += "Unpublished Changes "
            else:
                result += "Published "
            result += "Locked" if self.is_locked else "Unlocked"
            return result

    def populate_course_fixture(self, course_fixture):
        """ Install a course with various configurations that could produce warning messages """

        # Define the dimensions that map to the UnitState constructor
        features = [
            [True, False],             # Possible values for is_released
            self.PublishState.VALUES,  # Possible values for publish_state
            [True, False]              # Possible values for is_locked
        ]

        # Add a fixture for every state in the product of features
        course_fixture.add_children(*[
            self._build_fixture(self.UnitState(*state)) for state in itertools.product(*features)
        ])

    def _build_fixture(self, unit_state):
        """ Returns an XBlockFixtureDesc with a section, subsection, and possibly unit that has the given state. """
        name = unit_state.name
        start = (datetime(1984, 3, 4) if unit_state.is_released else datetime.now(UTC) + timedelta(1)).isoformat()

        subsection = XBlockFixtureDesc('sequential', name, metadata={'start': start})

        # Children of never published subsections will be added on demand via _ensure_unit_present
        return XBlockFixtureDesc('chapter', name).add_children(
            subsection if unit_state.publish_state == self.PublishState.NEVER_PUBLISHED
            else subsection.add_children(
                XBlockFixtureDesc('vertical', name, metadata={'visible_to_staff_only': unit_state.is_locked})
            )
        )

    def test_released_never_published_locked(self):
        """ Tests that released never published locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.NEVER_PUBLISHED, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_released_never_published_unlocked(self):
        """ Tests that released never published unlocked units display 'Unpublished units will not be released' """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.NEVER_PUBLISHED, is_locked=False),
            self.NEVER_PUBLISHED_WARNING
        )

    def test_released_unpublished_changes_locked(self):
        """ Tests that released unpublished changes locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.UNPUBLISHED_CHANGES, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_released_unpublished_changes_unlocked(self):
        """ Tests that released unpublished changes unlocked units display 'Unpublished changes to live content' """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.UNPUBLISHED_CHANGES, is_locked=False),
            self.LIVE_UNPUBLISHED_WARNING
        )

    def test_released_published_locked(self):
        """ Tests that released published locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.PUBLISHED, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_released_published_unlocked(self):
        """ Tests that released published unlocked units display no warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=True, publish_state=self.PublishState.PUBLISHED, is_locked=False),
            None
        )

    def test_unreleased_never_published_locked(self):
        """ Tests that unreleased never published locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.NEVER_PUBLISHED, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_unreleased_never_published_unlocked(self):
        """ Tests that unreleased never published unlocked units display 'Unpublished units will not be released' """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.NEVER_PUBLISHED, is_locked=False),
            self.NEVER_PUBLISHED_WARNING
        )

    def test_unreleased_unpublished_changes_locked(self):
        """ Tests that unreleased unpublished changes locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.UNPUBLISHED_CHANGES, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_unreleased_unpublished_changes_unlocked(self):
        """
        Tests that unreleased unpublished changes unlocked units display 'Unpublished changes to content that will
        release in the future'
        """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.UNPUBLISHED_CHANGES, is_locked=False),
            self.FUTURE_UNPUBLISHED_WARNING
        )

    def test_unreleased_published_locked(self):
        """ Tests that unreleased published locked units display staff only warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.PUBLISHED, is_locked=True),
            self.STAFF_ONLY_WARNING
        )

    def test_unreleased_published_unlocked(self):
        """ Tests that unreleased published unlocked units display no warnings """
        self._verify_unit_warning(
            self.UnitState(is_released=False, publish_state=self.PublishState.PUBLISHED, is_locked=False),
            None
        )

    def _verify_unit_warning(self, unit_state, expected_status_message):
        """
        Verifies that the given unit's messages match the expected messages.
        If expected_status_message is None, then the unit status message is expected to not be present.
        """
        self._ensure_unit_present(unit_state)
        self.course_outline_page.visit()
        section = self.course_outline_page.section(unit_state.name)
        subsection = section.subsection_at(0)
        subsection.toggle_expand()
        unit = subsection.unit_at(0)
        if expected_status_message == self.STAFF_ONLY_WARNING:
            self.assertEqual(section.status_message, self.STAFF_ONLY_WARNING)
            self.assertEqual(subsection.status_message, self.STAFF_ONLY_WARNING)
            self.assertEqual(unit.status_message, self.STAFF_ONLY_WARNING)
        else:
            self.assertFalse(section.has_status_message)
            self.assertFalse(subsection.has_status_message)
            if expected_status_message:
                self.assertEqual(unit.status_message, expected_status_message)
            else:
                self.assertFalse(unit.has_status_message)

    def _ensure_unit_present(self, unit_state):
        """ Ensures that a unit with the given state is present on the course outline """
        if unit_state.publish_state == self.PublishState.PUBLISHED:
            return

        name = unit_state.name
        self.course_outline_page.visit()
        subsection = self.course_outline_page.section(name).subsection(name)
        subsection.toggle_expand()

        if unit_state.publish_state == self.PublishState.UNPUBLISHED_CHANGES:
            unit = subsection.unit(name).go_to()
            add_discussion(unit)
        elif unit_state.publish_state == self.PublishState.NEVER_PUBLISHED:
            subsection.add_unit()
            unit = ContainerPage(self.browser, None)
            unit.wait_for_page()

        if unit.is_staff_locked != unit_state.is_locked:
            unit.toggle_staff_lock()


@attr('shard_2')
class EditingSectionsTest(CourseOutlineTest):
    """
    Feature: Editing Release date, Due date and grading type.
    """

    __test__ = True

    def test_can_edit_subsection(self):
        """
        Scenario: I can edit settings of subsection.

            Given that I have created a subsection
            Then I see release date, due date and grading policy of subsection in course outline
            When I click on the configuration icon
            Then edit modal window is shown
            And release date, due date and grading policy fields present
            And they have correct initial values
            Then I set new values for these fields
            And I click save button on the modal
            Then I see release date, due date and grading policy of subsection in course outline
        """
        self.course_outline_page.visit()
        subsection = self.course_outline_page.section(SECTION_NAME).subsection(SUBSECTION_NAME)

        # Verify that Release date visible by default
        self.assertTrue(subsection.release_date)
        # Verify that Due date and Policy hidden by default
        self.assertFalse(subsection.due_date)
        self.assertFalse(subsection.policy)

        modal = subsection.edit()

        # Verify fields
        self.assertTrue(modal.has_release_date())
        self.assertTrue(modal.has_due_date())
        self.assertTrue(modal.has_policy())

        # Verify initial values
        self.assertEqual(modal.release_date, u'1/1/1970')
        self.assertEqual(modal.due_date, u'')
        self.assertEqual(modal.policy, u'Not Graded')

        # Set new values
        modal.release_date = '3/12/1972'
        modal.due_date = '7/21/2014'
        modal.policy = 'Lab'

        modal.save()
        self.assertIn(u'Released: Mar 12, 1972', subsection.release_date)
        self.assertIn(u'Due: Jul 21, 2014', subsection.due_date)
        self.assertIn(u'Lab', subsection.policy)

    def test_can_edit_section(self):
        """
        Scenario: I can edit settings of section.

            Given that I have created a section
            Then I see release date of section in course outline
            When I click on the configuration icon
            Then edit modal window is shown
            And release date field present
            And it has correct initial value
            Then I set new value for this field
            And I click save button on the modal
            Then I see release date of section in course outline
        """
        self.course_outline_page.visit()
        section = self.course_outline_page.section(SECTION_NAME)

        # Verify that Release date visible by default
        self.assertTrue(section.release_date)
        # Verify that Due date and Policy are not present
        self.assertFalse(section.due_date)
        self.assertFalse(section.policy)

        modal = section.edit()
        # Verify fields
        self.assertTrue(modal.has_release_date())
        self.assertFalse(modal.has_due_date())
        self.assertFalse(modal.has_policy())

        # Verify initial value
        self.assertEqual(modal.release_date, u'1/1/1970')

        # Set new value
        modal.release_date = '5/14/1969'

        modal.save()
        self.assertIn(u'Released: May 14, 1969', section.release_date)
        # Verify that Due date and Policy are not present
        self.assertFalse(section.due_date)
        self.assertFalse(section.policy)

    def test_subsection_is_graded_in_lms(self):
        """
        Scenario: I can grade subsection from course outline page.

            Given I visit progress page
            And I see that problem in subsection has grading type "Practice"
            Then I visit course outline page
            And I click on the configuration icon of subsection
            And I set grading policy to "Lab"
            And I click save button on the modal
            Then I visit progress page
            And I see that problem in subsection has grading type "Problem"
        """
        progress_page = ProgressPage(self.browser, self.course_id)
        progress_page.visit()
        progress_page.wait_for_page()
        self.assertEqual(u'Practice', progress_page.grading_formats[0])
        self.course_outline_page.visit()

        subsection = self.course_outline_page.section(SECTION_NAME).subsection(SUBSECTION_NAME)
        modal = subsection.edit()
        # Set new values
        modal.policy = 'Lab'
        modal.save()

        progress_page.visit()

        self.assertEqual(u'Problem', progress_page.grading_formats[0])

    def test_unchanged_release_date_is_not_saved(self):
        """
        Scenario: Saving a subsection without changing the release date will not override the release date
            Given that I have created a section with a subsection
            When I open the settings modal for the subsection
            And I pressed save
            And I open the settings modal for the section
            And I change the release date to 07/20/1969
            And I press save
            Then the subsection and the section have the release date 07/20/1969
        """
        self.course_outline_page.visit()

        modal = self.course_outline_page.section_at(0).subsection_at(0).edit()
        modal.save()

        modal = self.course_outline_page.section_at(0).edit()
        modal.release_date = '7/20/1969'
        modal.save()

        release_text = 'Released: Jul 20, 1969'
        self.assertIn(release_text, self.course_outline_page.section_at(0).release_date)
        self.assertIn(release_text, self.course_outline_page.section_at(0).subsection_at(0).release_date)


@attr('shard_2')
class EditNamesTest(CourseOutlineTest):
    """
    Feature: Click-to-edit section/subsection names
    """

    __test__ = True

    def set_name_and_verify(self, item, old_name, new_name, expected_name):
        """
        Changes the display name of item from old_name to new_name, then verifies that its value is expected_name.
        """
        self.assertEqual(item.name, old_name)
        item.change_name(new_name)
        self.assertFalse(item.in_editable_form())
        self.assertEqual(item.name, expected_name)

    def test_edit_section_name(self):
        """
        Scenario: Click-to-edit section name
            Given that I have created a section
            When I click on the name of section
            Then the section name becomes editable
            And given that I have edited the section name
            When I click outside of the edited section name
            Then the section name saves
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0),
            'Test Section',
            'Changed',
            'Changed'
        )

    def test_edit_subsection_name(self):
        """
        Scenario: Click-to-edit subsection name
            Given that I have created a subsection
            When I click on the name of subsection
            Then the subsection name becomes editable
            And given that I have edited the subsection name
            When I click outside of the edited subsection name
            Then the subsection name saves
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0).subsection_at(0),
            'Test Subsection',
            'Changed',
            'Changed'
        )

    def test_edit_empty_section_name(self):
        """
        Scenario: Click-to-edit section name, enter empty name
            Given that I have created a section
            And I have clicked to edit the name of the section
            And I have entered an empty section name
            When I click outside of the edited section name
            Then the section name does not change
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0),
            'Test Section',
            '',
            'Test Section'
        )

    def test_edit_empty_subsection_name(self):
        """
        Scenario: Click-to-edit subsection name, enter empty name
            Given that I have created a subsection
            And I have clicked to edit the name of the subsection
            And I have entered an empty subsection name
            When I click outside of the edited subsection name
            Then the subsection name does not change
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0).subsection_at(0),
            'Test Subsection',
            '',
            'Test Subsection'
        )

    def test_editing_names_does_not_expand_collapse(self):
        """
        Scenario: A section stays in the same expand/collapse state while its name is edited
            Given that I have created a section
            And the section is collapsed
            When I click on the name of the section
            Then the section is collapsed
            And given that I have entered a new name
            Then the section is collapsed
            And given that I press ENTER to finalize the name
            Then the section is collapsed
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).toggle_expand()
        self.assertFalse(self.course_outline_page.section_at(0).in_editable_form())
        self.assertTrue(self.course_outline_page.section_at(0).is_collapsed)
        self.course_outline_page.section_at(0).edit_name()
        self.assertTrue(self.course_outline_page.section_at(0).in_editable_form())
        self.assertTrue(self.course_outline_page.section_at(0).is_collapsed)
        self.course_outline_page.section_at(0).enter_name('Changed')
        self.assertTrue(self.course_outline_page.section_at(0).is_collapsed)
        self.course_outline_page.section_at(0).finalize_name()
        self.assertTrue(self.course_outline_page.section_at(0).is_collapsed)


@attr('shard_2')
class CreateSectionsTest(CourseOutlineTest):
    """
    Feature: Create new sections/subsections/units
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with a completely empty course to easily test adding things to it """
        pass

    def test_create_new_section_from_top_button(self):
        """
        Scenario: Create new section from button at top of page
            Given that I am on the course outline
            When I click the "+ Add section" button at the top of the page
            Then I see a new section added to the bottom of the page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.assertTrue(self.course_outline_page.section_at(0).in_editable_form())

    def test_create_new_section_from_bottom_button(self):
        """
        Scenario: Create new section from button at bottom of page
            Given that I am on the course outline
            When I click the "+ Add section" button at the bottom of the page
            Then I see a new section added to the bottom of the page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_bottom_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.assertTrue(self.course_outline_page.section_at(0).in_editable_form())

    def test_create_new_subsection(self):
        """
        Scenario: Create new subsection
            Given that I have created a section
            When I click the "+ Add subsection" button in that section
            Then I see a new subsection added to the bottom of the section
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection()
        subsections = self.course_outline_page.section_at(0).subsections()
        self.assertEqual(len(subsections), 1)
        self.assertTrue(subsections[0].in_editable_form())

    def test_create_new_unit(self):
        """
        Scenario: Create new unit
            Given that I have created a section
            And that I have created a subsection within that section
            When I click the "+ Add unit" button in that subsection
            Then I am redirected to a New Unit page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).add_unit()
        unit_page = ContainerPage(self.browser, None)
        EmptyPromise(unit_page.is_browser_on_page, 'Browser is on the unit page').fulfill()
        self.assertTrue(unit_page.is_inline_editing_display_name())


@attr('shard_2')
class DeleteContentTest(CourseOutlineTest):
    """
    Feature: Deleting sections/subsections/units
    """

    __test__ = True

    def test_delete_section(self):
        """
        Scenario: Delete section
            Given that I am on the course outline
            When I click the delete button for a section on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the section
            When I click "Yes, I want to delete this component"
            Then the confirmation message should close
            And the section should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).delete()
        self.assertEqual(len(self.course_outline_page.sections()), 0)

    def test_cancel_delete_section(self):
        """
        Scenario: Cancel delete of section
            Given that I clicked the delte button for a section on the course outline
            And I received a confirmation message, asking me if I really want to delete the component
            When I click "Cancel"
            Then the confirmation message should close
            And the section should remain in the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.sections()), 1)

    def test_delete_subsection(self):
        """
        Scenario: Delete subsection
            Given that I am on the course outline
            When I click the delete button for a subsection on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the subsection
            When I click "Yes, I want to delete this component"
            Then the confiramtion message should close
            And the subsection should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).delete()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 0)

    def test_cancel_delete_subsection(self):
        """
        Scenario: Cancel delete of subsection
            Given that I clicked the delete button for a subsection on the course outline
            And I received a confirmation message, asking me if I really want to delete the subsection
            When I click "cancel"
            Then the confirmation message should close
            And the subsection should remain in the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)

    def test_delete_unit(self):
        """
        Scenario: Delete unit
            Given that I am on the course outline
            When I click the delete button for a unit on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the unit
            When I click "Yes, I want to delete this unit"
            Then the confirmation message should close
            And the unit should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).delete()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 0)

    def test_cancel_delete_unit(self):
        """
        Scenario: Cancel delete of unit
            Given that I clicked the delete button for a unit on the course outline
            And I received a confirmation message, asking me if I really want to delete the unit
            When I click "Cancel"
            Then the confirmation message should close
            And the unit should remain in the course outline
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)

    def test_delete_all_no_content_message(self):
        """
        Scenario: Delete all sections/subsections/units in a course, "no content" message should appear
            Given that I delete all sections, subsections, and units in a course
            When I visit the course outline
            Then I will see a message that says, "You haven't added any content to this course yet"
            Add see a + Add Section button
        """
        self.course_outline_page.visit()
        self.assertFalse(self.course_outline_page.has_no_content_message)
        self.course_outline_page.section_at(0).delete()
        self.assertEqual(len(self.course_outline_page.sections()), 0)
        self.assertTrue(self.course_outline_page.has_no_content_message)


@attr('shard_2')
class ExpandCollapseMultipleSectionsTest(CourseOutlineTest):
    """
    Feature: Courses with multiple sections can expand and collapse all sections.
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with a course with two sections """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit 2')
                )
            )
        )

    def verify_all_sections(self, collapsed):
        """
        Verifies that all sections are collapsed if collapsed is True, otherwise all expanded.
        """
        for section in self.course_outline_page.sections():
            self.assertEqual(collapsed, section.is_collapsed)

    def toggle_all_sections(self):
        """
        Toggles the expand collapse state of all sections.
        """
        for section in self.course_outline_page.sections():
            section.toggle_expand()

    def test_expanded_by_default(self):
        """
        Scenario: The default layout for the outline page is to show sections in expanded view
            Given I have a course with sections
            When I navigate to the course outline page
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Collapse link is removed after last section of a course is deleted
            Given I have a course with multiple sections
            And I navigate to the course outline page
            When I will confirm all alerts
            And I press the "section" delete icon
            Then I do not see the "Collapse All Sections" link
            And I will see a message that says "You haven't added any content to this course yet"
        """
        self.course_outline_page.visit()
        for section in self.course_outline_page.sections():
            section.delete()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.assertTrue(self.course_outline_page.has_no_content_message)

    def test_collapse_all_when_all_expanded(self):
        """
        Scenario: Collapse all sections when all sections are expanded
            Given I navigate to the outline page of a course with sections
            And all sections are expanded
            When I click the "Collapse All Sections" link
            Then I see the "Expand All Sections" link
            And all sections are collapsed
        """
        self.course_outline_page.visit()
        self.verify_all_sections(collapsed=False)
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.verify_all_sections(collapsed=True)

    def test_collapse_all_when_some_expanded(self):
        """
        Scenario: Collapsing all sections when 1 or more sections are already collapsed
            Given I navigate to the outline page of a course with sections
            And all sections are expanded
            When I collapse the first section
            And I click the "Collapse All Sections" link
            Then I see the "Expand All Sections" link
            And all sections are collapsed
        """
        self.course_outline_page.visit()
        self.verify_all_sections(collapsed=False)
        self.course_outline_page.section_at(0).toggle_expand()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.verify_all_sections(collapsed=True)

    def test_expand_all_when_all_collapsed(self):
        """
        Scenario: Expanding all sections when all sections are collapsed
            Given I navigate to the outline page of a course with multiple sections
            And I click the "Collapse All Sections" link
            When I click the "Expand All Sections" link
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)

    def test_expand_all_when_some_collapsed(self):
        """
        Scenario: Expanding all sections when 1 or more sections are already expanded
            Given I navigate to the outline page of a course with multiple sections
            And I click the "Collapse All Sections" link
            When I expand the first section
            And I click the "Expand All Sections" link
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.course_outline_page.section_at(0).toggle_expand()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)


@attr('shard_2')
class ExpandCollapseSingleSectionTest(CourseOutlineTest):
    """
    Feature: Courses with a single section can expand and collapse all sections.
    """

    __test__ = True

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Collapse link is removed after last section of a course is deleted
            Given I have a course with one section
            And I navigate to the course outline page
            When I will confirm all alerts
            And I press the "section" delete icon
            Then I do not see the "Collapse All Sections" link
            And I will see a message that says "You haven't added any content to this course yet"
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).delete()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.assertTrue(self.course_outline_page.has_no_content_message)

    def test_old_subsection_stays_collapsed_after_creation(self):
        """
        Scenario: Collapsed subsection stays collapsed after creating a new subsection
            Given I have a course with one section and subsection
            And I navigate to the course outline page
            Then the subsection is collapsed
            And when I create a new subsection
            Then the first subsection is collapsed
            And the second subsection is expanded
        """
        self.course_outline_page.visit()
        self.assertTrue(self.course_outline_page.section_at(0).subsection_at(0).is_collapsed)
        self.course_outline_page.section_at(0).add_subsection()
        self.assertTrue(self.course_outline_page.section_at(0).subsection_at(0).is_collapsed)
        self.assertFalse(self.course_outline_page.section_at(0).subsection_at(1).is_collapsed)


@attr('shard_2')
class ExpandCollapseEmptyTest(CourseOutlineTest):
    """
    Feature: Courses with no sections initially can expand and collapse all sections after addition.
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with an empty course """
        pass

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Expand/collapse for a course with no sections
            Given I have a course with no sections
            When I navigate to the course outline page
            Then I do not see the "Collapse All Sections" link
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)

    def test_link_appears_after_section_creation(self):
        """
        Scenario: Collapse link appears after creating first section of a course
            Given I have a course with no sections
            When I navigate to the course outline page
            And I add a section
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.course_outline_page.add_section_from_top_button()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.assertFalse(self.course_outline_page.section_at(0).is_collapsed)


@attr('shard_2')
class DefaultStatesEmptyTest(CourseOutlineTest):
    """
    Feature: Misc course outline default states/actions when starting with an empty course
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with an empty course """
        pass

    def test_empty_course_message(self):
        """
        Scenario: Empty course state
            Given that I am in a course with no sections, subsections, nor units
            When I visit the course outline
            Then I will see a message that says "You haven't added any content to this course yet"
            And see a + Add Section button
        """
        self.course_outline_page.visit()
        self.assertTrue(self.course_outline_page.has_no_content_message)
        self.assertTrue(self.course_outline_page.bottom_add_section_button.is_present())


@attr('shard_2')
class DefaultStatesContentTest(CourseOutlineTest):
    """
    Feature: Misc course outline default states/actions when starting with a course with content
    """

    __test__ = True

    def test_view_live(self):
        """
        Scenario: View Live version from course outline
            Given that I am on the course outline
            When I click the "View Live" button
            Then a new tab will open to the course on the LMS
        """
        self.course_outline_page.visit()
        self.course_outline_page.view_live()
        courseware = CoursewarePage(self.browser, self.course_id)
        courseware.wait_for_page()
        self.assertEqual(courseware.num_xblock_components, 3)
        self.assertEqual(courseware.xblock_component_type(0), 'problem')
        self.assertEqual(courseware.xblock_component_type(1), 'html')
        self.assertEqual(courseware.xblock_component_type(2), 'discussion')


@attr('shard_2')
class UnitNavigationTest(CourseOutlineTest):
    """
    Feature: Navigate to units
    """

    __test__ = True

    def test_navigate_to_unit(self):
        """
        Scenario: Click unit name to navigate to unit page
            Given that I have expanded a section/subsection so I can see unit names
            When I click on a unit name
            Then I will be taken to the appropriate unit page
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        unit = self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).go_to()
        self.assertTrue(unit.is_browser_on_page)
