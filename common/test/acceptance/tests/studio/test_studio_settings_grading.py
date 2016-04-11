"""
Acceptance tests for Studio Setting pages.
"""
from bok_choy.promise import BrokenPromise
from .base_studio_test import StudioCourseTest
from ...pages.studio.settings_graders import GradingPage


class GradingPageTest(StudioCourseTest):
    """
    Tests for settings/grading Page.
    """
    def setUp(self, is_staff=False):
        super(GradingPageTest, self).setUp(is_staff)
        self.page = GradingPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def test_can_add_grading_ranges(self):
        """
        Scenario: Users can add grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "1" new grade
        Then I see I now have "3" grades
        """
        self.page.visit()
        self.page.add_grading_range()
        self.assertEqual(len(self.page.grading_ranges), 3)

    def test_can_have_up_to_five_grading_ranges(self):
        """
        Scenario: Users can only have up to 5 grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "6" new grades
        Then I see I now have "5" grades
        """
        self.page.visit()
        for _ in xrange(6):
            self.page.add_grading_range()
        self.assertEqual(len(self.page.grading_ranges), 5)

    def test_can_remove_grades(self):
        """
        Scenario: When user removes a grade the remaining grades should be consistent
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "2" new grade
        Then Grade list has "ABCF" grades
        And I delete a grade
        Then Grade list has "ABF" grades
        """
        self.page.visit()
        for _ in xrange(2):
            self.page.add_grading_range()
        self.assertEqual(self.page.letter_grades, ['A', 'B', 'C', 'F'])
        self.page.remove_grading_range('C')
        self.page.click_save_button()
        self.assertEqual(self.page.letter_grades, ['A', 'B', 'F'])

    def test_can_delete_grading_ranges(self):
        """
        Scenario: Users can delete grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "1" new grade
        And I delete a grade
        Then I see I now have "2" grades
        """
        self.page.visit()
        self.page.add_grading_range()
        self.assertIn('B', self.page.letter_grades)
        self.page.remove_grading_range('B')
        self.page.click_save_button()
        self.assertEqual(len(self.page.grading_ranges), 2)

    def test_can_move_grading_ranges(self):
        """
        Scenario: Users can move grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I move a grading section
        Then I see that the grade range has changed
        """
        self.page.visit()
        self.page.move_grading_range_by_offset('Fail', offset_x=100, offset_y=0)
        for value in self.page.grading_ranges:
            self.assertNotEqual(value, '0-50')

    def test_can_modify_assignment_types(self):
        """
        Scenario: Users can modify Assignment types
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change assignment type "Homework" to "New Type"
        And I press the "Save" notification button
        And I reload the page
        Then I do see the assignment name "New Type"
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.name = 'New Type'
        self.page.click_save_button()
        self.page.refresh()
        self.page.wait_for_assignmnents()
        self.assertTrue(self.page.has_assignment_with_name('New Type'))

    def test_can_delete_assignment_types(self):
        """
        Scenario: Users can delete Assignment types
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I delete the assignment type "Homework"
        And I press the "Save" notification button
        And I reload the page
        Then I do not see the assignment name "Homework"
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.delete()
        self.page.click_save_button()
        self.page.refresh()
        self.page.wait_for_assignmnents()
        self.assertFalse(self.page.has_assignment_with_name('Homework'))

    def test_can_add_assignment_types(self):
        """
        Scenario: Users can add Assignment types
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add a new assignment type "New Type"
        And I press the "Save" notification button
        And I reload the page
        Then I do see the assignment name "New Type"
        """
        self.page.visit()
        self.page.click_add_assignment_button()
        self.page.assignments[-1].name = 'New Type'
        self.page.click_save_button()
        self.page.refresh()
        self.page.wait_for_assignmnents()
        self.assertTrue(self.page.has_assignment_with_name('New Type'))
        self.assertEqual(len(self.page.assignments), 5)

    def test_can_set_weight_to_assignment_types(self):
        """
        # Note that "7" is a special weight because it revealed rounding errors (STUD-826).
        Scenario: Users can set weight to Assignment types
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add a new assignment type "New Type"
        And I set the assignment weight to "7"
        And I press the "Save" notification button
        Then the assignment weight is displayed as "7"
        And I reload the page
        Then the assignment weight is displayed as "7"
        """
        self.page.visit()
        self.page.click_add_assignment_button()
        assignment = self.page.assignments[-1]
        assignment.name = 'New Type'
        assignment.weight = 7
        self.page.click_save_button()
        self.assertEqual(assignment.weight, 7)
        self.page.refresh()
        self.page.wait_for_assignmnents()
        assignment = self.page.get_assignment_by_name('New Type')
        self.assertEqual(assignment.weight, 7)

    def test_can_set_passing_grade_to_assignment_types(self):
        """
        # Note that "7" is a special passing grade because it revealed rounding errors.
        Scenario: Users can set passing grade to Assignment types
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add a new assignment type "New Type"
        And I set the assignment passing grade to "7"
        And I press the "Save" notification button
        Then the assignment passing grade is displayed as "7"
        And I reload the page
        Then the assignment passing grade is displayed as "7"
        """
        self.page.visit()
        self.page.click_add_assignment_button()
        assignment = self.page.assignments[-1]
        assignment.name = 'New Type'
        assignment.click_enable_passing_grade()
        assignment.passing_grade = 7
        self.page.click_save_button()
        self.assertEqual(assignment.passing_grade, 7)
        self.page.refresh()
        self.page.wait_for_assignmnents()
        assignment = self.page.get_assignment_by_name('New Type')
        self.assertEqual(assignment.passing_grade, 7)

    def test_settings_are_only_persisted_when_saved(self):
        """
        Scenario: Settings are only persisted when saved
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change assignment type "Homework" to "New Type"
        Then I do not see the changes persisted on refresh
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.name = 'New Type'
        self.page.refresh()
        self.page.wait_for_assignmnents()
        self.assertFalse(self.page.has_assignment_with_name('New Type'))

    def test_settings_are_reset_on_cancel(self):
        """
        Scenario: Settings are reset on cancel
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change assignment type "Homework" to "New Type"
        And I press the "Cancel" notification button
        Then I see the assignment type "Homework"
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.name = 'New Type'
        self.page.click_cancel_button()
        self.assertTrue(self.page.has_assignment_with_name('Homework'))

    def test_confirmation_is_shown_on_save(self):
        """
        Scenario: Confirmation is shown on save
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change assignment type "Homework" to "New Type"
        And I press the "Save" notification button
        Then I see a confirmation that my changes have been saved
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.name = 'New Type'
        self.page.click_save_button()
        self.assertTrue(self.page.is_confirmation_message_visible())

    def test_cannot_save_invalid_settings(self):
        """
        Scenario: User cannot save invalid settings
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change assignment type "Homework" to ""
        Then the save notification button is disabled
        """
        self.page.visit()
        assignment = self.page.get_assignment_by_name('Homework')
        assignment.name = ''
        self.assertTrue(self.page.is_save_button_disabled())

    def test_can_edit_grading_range_names(self):
        """
        Scenario: User can edit grading range names
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change the highest grade range to "Good"
        And I press the "Save" notification button
        And I reload the page
        Then I see the highest grade range is "Good"
        """
        self.page.visit()
        self.page.change_grading_range_name('Pass', 'Good')
        self.page.click_save_button()
        self.page.refresh()
        self.page.wait_for_letter_grades()
        self.assertEqual(self.page.letter_grades, ['Good', 'Fail'])

    def test_cannot_edit_failing_grade_range_name(self):
        """
        Scenario: User cannot edit failing grade range name
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        Then I cannot edit the "Fail" grade range
        """
        self.page.visit()
        try:
            self.page.change_grading_range_name('Fail', 'Failure')
        except BrokenPromise:
            pass  # We should get this exception on failing to edit the element
        self.assertEqual(self.page.letter_grades, ['Pass', 'Fail'])

    def test_can_set_a_grace_period_gt_than_one_day(self):
        """
        Scenario: User can set a grace period greater than one day
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change the grace period to "48:00"
        And I press the "Save" notification button
        And I reload the page
        Then I see the grace period is "48:00"
        """
        self.page.visit()
        self.page.grace_period = '48:00'
        self.page.click_save_button()
        self.page.refresh()
        # The default value is 00:00
        # so we need to wait for it to change
        self.page.wait_for_grace_period('48:00')
        self.assertEqual(self.page.grace_period, '48:00')

    def test_grace_periods_are_wrappered_correctly(self):
        """
        Scenario: Grace periods of more than 59 minutes are wrapped to the correct time
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I change the grace period to "01:99"
        And I press the "Save" notification button
        And I reload the page
        Then I see the grace period is "02:39"
        """
        self.page.visit()
        self.page.grace_period = '01:99'
        self.page.click_save_button()
        self.page.refresh()
        # The default value is 00:00
        # so we need to wait for it to change
        self.page.wait_for_grace_period('02:39')
        self.assertEqual(self.page.grace_period, '02:39')
