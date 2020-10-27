"""
Acceptance tests for grade settings in Studio.
"""
from common.test.acceptance.pages.studio.settings_graders import GradingPage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from bok_choy.promise import EmptyPromise


class GradingPageTest(StudioCourseTest):
    """
    Bockchoy tests to add/edit grade settings in studio.
    """

    url = None
    GRACE_FIELD_CSS = "#course-grading-graceperiod"

    def setUp(self):  # pylint: disable=arguments-differ
        super(GradingPageTest, self).setUp()
        self.grading_page = GradingPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.grading_page.visit()
        self.ensure_input_fields_are_loaded()

    def ensure_input_fields_are_loaded(self):
        """
        Ensures values in input fields are loaded.
        """
        EmptyPromise(
            lambda: self.grading_page.q(css=self.GRACE_FIELD_CSS).attrs('value')[0],
            "Waiting for input fields to be loaded"
        ).fulfill()

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
        length = self.grading_page.total_number_of_grades
        self.grading_page.click_add_grade()
        self.assertTrue(self.grading_page.is_grade_added(length))
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        total_number_of_grades = self.grading_page.total_number_of_grades
        self.assertEqual(total_number_of_grades, 3)

    def test_staff_can_add_up_to_five_grades_only(self):
        """
        Scenario: Users can only have up to 5 grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I try to add more than 5 grades
            Then I see I have only "5" grades
        """
        for grade_ordinal in range(1, 5):
            length = self.grading_page.total_number_of_grades
            self.grading_page.click_add_grade()
            # By default page has 2 grades, so greater than 3 means, attempt is made to add 6th grade
            if grade_ordinal > 3:
                self.assertFalse(self.grading_page.is_grade_added(length))
            else:
                self.assertTrue(self.grading_page.is_grade_added(length))
        self.grading_page.save()
        self.grading_page.refresh_and_wait_for_load()
        total_number_of_grades = self.grading_page.total_number_of_grades
        self.assertEqual(total_number_of_grades, 5)

    def test_grades_remain_consistent(self):
        """
        Scenario: When user removes a grade the remaining grades should be consistent
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I add "2" new grade
            Then Grade list has "A,B,C,F" grades
            And I delete a grade
            Then Grade list has "A,B,F" grades
        """
        for _ in range(2):
            length = self.grading_page.total_number_of_grades
            self.grading_page.click_add_grade()
            self.assertTrue(self.grading_page.is_grade_added(length))
        self.grading_page.save()
        grades_alphabets = self.grading_page.grade_letters
        self.assertEqual(grades_alphabets, ['A', 'B', 'C', 'F'])
        self.grading_page.remove_grades(1)
        self.grading_page.save()
        grades_alphabets = self.grading_page.grade_letters
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
        length = self.grading_page.total_number_of_grades
        self.grading_page.click_add_grade()
        self.assertTrue(self.grading_page.is_grade_added(length))
        self.grading_page.save()
        total_number_of_grades = self.grading_page.total_number_of_grades
        self.assertEqual(total_number_of_grades, 3)
        self.grading_page.remove_grades(1)
        total_number_of_grades = self.grading_page.total_number_of_grades
        self.assertEqual(total_number_of_grades, 2)

    def test_staff_can_move_grading_ranges(self):
        """
        Scenario: Users can move grading ranges
            Given I have opened a new course in Studio
            And I am viewing the grading settings
            When I move a grading section
            Then I see that the grade range has changed
        """
        grade_ranges = self.grading_page.grades_range
        self.assertIn('0-50', grade_ranges)
        self.grading_page.drag_and_drop_grade()
        grade_ranges = self.grading_page.grades_range
        self.assertIn(
            '0-3',
            grade_ranges,
            'expected range: 0-3, not found in grade ranges:{}'.format(grade_ranges)
        )

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
        self.assertIn('Homework', self.grading_page.get_assignment_names)

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
        assignment_names = self.grading_page.get_assignment_names
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
        confirmation_message = self.grading_page.confirmation_message
        self.assertEqual(confirmation_message, 'Your changes have been saved.')

    def test_staff_can_set_weight_to_assignment(self):
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
        assignment_weight = self.grading_page.get_assignment_weight('New Type')
        self.assertEqual(assignment_weight, '7')
        self.grading_page.refresh_and_wait_for_load()
        assignment_weight = self.grading_page.get_assignment_weight('New Type')
        self.assertEqual(assignment_weight, '7')

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
        grade_name = self.grading_page.highest_grade_name
        self.assertEqual(grade_name, 'Good')

    def test_staff_cannot_edit_lowest_grade_name(self):
        """
        Scenario: User cannot edit failing grade range name
            Given I have populated a new course in Studio
            And I am viewing the grading settings
            Then I cannot edit the "Fail" grade range
        """
        self.grading_page.try_edit_fail_grade('Failure')
        self.assertNotEqual(self.grading_page.lowest_grade_name, 'Failure')

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
        self.ensure_input_fields_are_loaded()
        self.grading_page.check_field_value('00:00')
        self.grading_page.set_grace_period('01:99')
        self.grading_page.check_field_value('01:99')
        self.grading_page.click_button("save")
        self.grading_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        grace_time = self.grading_page.grace_period_value
        self.assertEqual(grace_time, '02:39')

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
        self.ensure_input_fields_are_loaded()
        self.grading_page.check_field_value('00:00')
        self.grading_page.set_grace_period('48:00')
        self.grading_page.check_field_value('48:00')
        self.grading_page.click_button("save")
        self.grading_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        grace_time = self.grading_page.grace_period_value
        self.assertEqual(grace_time, '48:00')
