"""
Acceptance tests for grade settings in Studio.
"""
from common.test.acceptance.pages.studio.settings_graders import GradingPage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from unittest import skip


class GradingPageTest(StudioCourseTest):
    """
    Bockchoy tests to add/edit grade settings in studio.
    """

    url = None

    def setUp(self):
        super(GradingPageTest, self).setUp()
        self.grading_page = GradingPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.grading_page.visit()

    def populate_course_fixture(self, course_fixture):
        """
        Return a test course fixture.
        """
        course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                )
            )
        )

    def test_add_grade_range(self):
        """
        Scenario: Users can add grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I add "1" new grade
            Then I see I now have "3"
        """
        self.grading_page.add_grades(1)
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        total_number_of_grades = self.grading_page.get_total_number_of_grades()
        self.assertEqual(total_number_of_grades, 3)

    def test_staff_can_add_up_to_five_grades_only(self):
        """
        Scenario: Users can only have up to 5 grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I add "6" new grades
            Then I see I now have "5" grades
        """
        self.grading_page.add_grades(6)
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        total_number_of_grades = self.grading_page.get_total_number_of_grades()
        self.assertEqual(total_number_of_grades, 5)

    def test_grades_remain_consistent(self):
        """
        Scenario: When user removes a grade the remaining grades should be consistent
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I add "2" new grade
            Then Grade list has "ABCF" grades
            And I delete a grade
            Then Grade list has "ABF" grades
        """
        self.grading_page.add_grades(2)
        grades_alphabets = self.grading_page.get_grade_alphabets()
        self.assertEqual(grades_alphabets, ['A', 'B', 'C', 'F'])
        self.grading_page.remove_grades(1)
        grades_alphabets = self.grading_page.get_grade_alphabets()
        self.assertEqual(grades_alphabets, ['A', 'B', 'F'])

    def test_staff_can_delete_grade_range(self):
        """
        Scenario: Users can delete grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I add "1" new grade
            And I delete a grade
            Then I see I now have "2" grades
        """
        self.grading_page.add_grades(1)
        total_number_of_grades = self.grading_page.get_total_number_of_grades()
        self.assertEqual(total_number_of_grades, 3)
        self.grading_page.remove_grades(1)
        total_number_of_grades = self.grading_page.get_total_number_of_grades()
        self.assertEqual(total_number_of_grades, 2)

    def test_staff_can_move_grading_ranges(self):
        """
        Scenario: Users can move grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I move a grading section
            Then I see that the grade range has changed
        """
        self.grading_page.drag_and_drop_grade()
        grade_ranges = self.grading_page.get_grade_ranges()
        for grade_range in grade_ranges:
            self.assertNotEqual(grade_range, '0-50')

    def test_modify_assignment_type(self):
        """
        Scenario: Users can modify Assignment types
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change assignment type "Homework" to "New Type"
            And I press the "Save" notification button
            And I go back to the main course page
            Then I do see the assignment name "New Type"
            And I do not see the assignment name "Homework"
        """
        self.grading_page.change_assignment_name('Homework', 'New Type')
        self.grading_page.save()
        course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        course_outline_page.visit()
        subsection = course_outline_page.section('Test Section').subsection('Test Subsection')
        modal = subsection.edit()
        # Set new values
        modal.policy = 'New Type'
        modal.save()
        grade = course_outline_page.policy
        self.assertEqual(grade, 'New Type')

    @skip
    def staff_can_delete_assignment_type(self):
        """
        Scenario: Users can delete Assignment types
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I delete the assignment type "Homework"
            And I press the "Save" notification button
            And I go back to the main course page
            Then I do not see the assignment name "Homework"
        """
        self.grading_page.delete_assignment_type('Homework')
        self.grading_page.save()
        # Could not implement the test as deleted grade does not get removed from the subsection.

    def staff_can_add_assignment_type(self):
        """
        Scenario: Users can add Assignment types
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I add a new assignment type "New Type"
            And I press the "Save" notification button
            And I go back to the main course page
            Then I do see the assignment name "New Type"
        """
        self.grading_page.add_new_assignment_type()
        self.grading_page.change_assignment_name('', 'New Type')
        self.grading_page.save()
        course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        course_outline_page.visit()
        subsection = course_outline_page.section('Test Section').subsection('Test Subsection')
        modal = subsection.edit()
        # Set new values
        modal.policy = 'New Type'
        modal.save()
        grade = course_outline_page.policy
        self.assertEqual(grade, 'New Type')

    def staff_can_set_weight_to_assignment(self):
        """
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
        self.grading_page.add_new_assignment_type()
        self.grading_page.change_assignment_name('', 'New Type')
        self.grading_page.set_weight('New Type', '7')
        self.grading_page.save()
        assignment_weight = self.grading_page.get_assignment_weight()
        self.assertEqual(assignment_weight, '7')
        self.grading_page.refresh_and_wait_for_load()
        assignment_weight = self.grading_page.get_assignment_weight()
        self.assertEqual(assignment_weight, '7')

    def test_settings_are_persisted_on_save_only(self):
        """
        Scenario: Settings are only persisted when saved
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change assignment type "Homework" to "New Type"
            Then I do not see the changes persisted on refresh
        """
        self.grading_page.change_assignment_name('Homework', 'New Type')
        self.grading_page.refresh_and_wait_for_load()
        self.assertIn('Homework', self.grading_page.get_assignment_names())

    def test_settings_are_reset_on_cancel(self):
        """
        Scenario: Settings are reset on cancel
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change assignment type "Homework" to "New Type"
            And I press the "Cancel" notification button
            Then I see the assignment type "Homework"
        """
        self.grading_page.change_assignment_name('Homework', 'New Type')
        self.grading_page.cancel()
        assignment_names = self.grading_page.get_assignment_names()
        self.assertIn('Homework', assignment_names)

    def test_confirmation_is_shown_on_save(self):
        """
        Scenario: Confirmation is shown on save
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change assignment type "Homework" to "New Type"
            And I press the "Save" notification button
            Then I see a confirmation that my changes have been saved
        """
        self.grading_page.change_assignment_name('Homework', 'New Type')
        self.grading_page.save()
        confirmation_message = self.grading_page.get_confirmation_message()
        self.assertEqual(confirmation_message, 'Your changes have been saved.')

    def test_staff_cannot_save_invalid_settings(self):
        """
        Scenario: User cannot save invalid settings
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change assignment type "Homework" to ""
            Then the save notification button is disabled
        """
        self.grading_page.change_assignment_name('Homework', '')
        self.assertTrue(self.grading_page.is_notification_button_disbaled(), True)

    def test_edit_highest_grade_name(self):
        """
        Scenario: User can edit grading range names
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change the highest grade range to "Good"
            And I press the "Save" notification button
            And I reload the page
            Then I see the highest grade range is "Good"
        """
        self.grading_page.edit_grade_name('Good')
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        grade_name = self.grading_page.get_highest_grade_name()
        self.assertEqual(grade_name, 'Good')

    def test_staff_cannot_edit_lowest_grade_name(self):
        """
        Scenario: User cannot edit failing grade range name
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            Then I cannot edit the "Fail" grade range
        """
        self.grading_page.try_edit_fail_grade('Failure')
        self.assertNotEqual(self.grading_page.get_lowest_grade_name, 'Failure')

    def test_setting_grace_period_greater_than_one_day(self):
        """
        Scenario: User can set a grace period greater than one day
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change the grace period to "48:00"
            And I press the "Save" notification button
            And I reload the page
            Then I see the grace period is "48:00"
        """
        self.grading_page.set_grace_period_value('48:00')
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        grace_time = self.grading_page.get_grace_period_value()
        self.assertEqual(grace_time, '48:00')

    def test_grace_period_wrapped_to_correct_time(self):
        """
        Scenario: Grace periods of more than 59 minutes are wrapped to the correct time
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            When I change the grace period to "01:99"
            And I press the "Save" notification button
            And I reload the page
            Then I see the grace period is "02:39"
        """
        self.grading_page.set_grace_period_value('01:99')
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        grace_time = self.grading_page.get_grace_period_value()
        self.assertEqual(grace_time, '02:39')
