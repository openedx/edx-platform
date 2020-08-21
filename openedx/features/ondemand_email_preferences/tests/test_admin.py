"""
Tests for ondemand email preferences admin's helper functions
"""
from datetime import datetime

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.ondemand_email_preferences.admin import get_all_on_demand_courses
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class OnDemandEmailPreferencesAdminFunctions(ModuleStoreTestCase):
    def test_get_all_on_demand_courses_with_valid_start_and_end_date(self):
        """
        Test 'get_all_on_demand_courses' by getting all ondemand courses with valid course start and end dates.
        """
        start_date = datetime.strptime('2020-02-20', '%Y-%m-%d')
        end_date = datetime.strptime('2021-02-20', '%Y-%m-%d')

        ondemand_course_with_valid_dates = CourseFactory.create(display_name='test course 1', run='Testing_course_1')
        CourseOverviewFactory.create(
            id=ondemand_course_with_valid_dates.id, start=start_date, end=end_date, self_paced=True)

        ondemand_course_with_invalid_dates = CourseFactory.create(display_name='test course 2', run='Testing_course_2')
        CourseOverviewFactory.create(id=ondemand_course_with_invalid_dates.id, self_paced=True)

        instructor_paced_course_with_valid_dates = CourseFactory.create(display_name='test course 3',
                                                                        run='Testing_course_3')
        CourseOverviewFactory.create(id=instructor_paced_course_with_valid_dates.id, start=start_date, end=end_date)

        expected_output_length = 1
        expected_output = ondemand_course_with_valid_dates.id

        actual_output = get_all_on_demand_courses()
        course_id_from_first_index_of_actual_output = actual_output[0][0]

        self.assertEqual(expected_output_length, len(actual_output))
        self.assertEqual(expected_output, course_id_from_first_index_of_actual_output)
