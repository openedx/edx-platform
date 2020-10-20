"""
Unit test for CMS helpers
"""


from datetime import datetime

import mock
from mock import patch

from dateutil.parser import parse
from opaque_keys.edx.locator import CourseLocator
from openassessment.xblock.defaults import DEFAULT_DUE, DEFAULT_START
from pytz import UTC

from custom_settings.models import CustomSettings
from lms.djangoapps.courseware.courses import get_course_by_id
from openedx.features.cms import helpers
from xmodule.course_module import CourseFields
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from . import helpers as test_helpers
from ..constants import ERROR_MESSAGES
from .factories import CourseRerunFactory


class CourseRerunAutomationTestCase(ModuleStoreTestCase):
    """
    Class for test cases related to course re-run (course automation, in general)
    """

    def test_initialize_course_settings_custom_tags(self):
        """
        Testing custom tags while initializing course settings
        """
        source_course = CourseFactory.create(
            org='origin',
            number='source',
            run='test1',
            display_name='destination course',
            start=datetime(2018, 8, 1, tzinfo=UTC),
            emit_signals=True
        )

        rerun_course = CourseFactory.create(
            org='origin',
            number='rerun',
            run='test1',
            display_name='destination course',
            start=datetime(2018, 8, 1, tzinfo=UTC),
            emit_signals=True
        )

        parent_course_id = source_course.id
        re_run_course_id = rerun_course.id

        custom_tags = '{"test_key": "test_value"}'
        custom_settings = CustomSettings.objects.get(id=parent_course_id)

        custom_settings.tags = custom_tags
        custom_settings.save()

        helpers.initialize_course_settings(source_course, rerun_course)

        # Desired output is that the tags have been set in the rerun course
        # custom settings as per the parent course
        self.assertEqual(CustomSettings.objects.get(id=re_run_course_id).tags, custom_tags)

        # If parent course id is not provided or is none method returns none
        self.assertIsNone(helpers.initialize_course_settings(None, re_run_course_id))

    @patch('openedx.features.cms.helpers.calculate_date_by_delta')
    def test_initialize_course_settings_with_open_date_and_custom_tags(
            self, mock_calculate_date_by_delta):
        """
        Testing custom tags along with course open date, while initializing course settings
        """
        source_course = CourseFactory.create(
            org='origin',
            number='source',
            run='test1',
            display_name='destination course',
            start=datetime(2018, 8, 1, tzinfo=UTC),
            emit_signals=True
        )

        rerun_course = CourseFactory.create(
            org='origin',
            number='rerun',
            run='test1',
            display_name='destination course',
            start=datetime(2018, 8, 1, tzinfo=UTC),
            emit_signals=True
        )

        parent_course_id = source_course.id
        re_run_course_id = rerun_course.id

        custom_tags = '{"test_key": "test_value"}'
        custom_settings = CustomSettings.objects.get(id=parent_course_id)

        custom_settings.course_open_date = datetime(2018, 12, 1, tzinfo=UTC)
        custom_settings.tags = custom_tags
        custom_settings.save()

        mock_calculate_date_by_delta.return_value = datetime(2019, 12, 1, tzinfo=UTC)

        helpers.initialize_course_settings(source_course, rerun_course, False)

        # Desired output is that the tags have been set in the rerun course custom settings as per the parent course
        updated_custom_settings = CustomSettings.objects.get(id=re_run_course_id)
        self.assertEqual(updated_custom_settings.tags, custom_tags)
        self.assertEqual(updated_custom_settings.course_open_date,
                         datetime(2019, 12, 1, tzinfo=UTC))

    @patch('openedx.features.cms.helpers.set_rerun_course_dates')
    @patch('openedx.features.cms.helpers.initialize_course_settings')
    def test_apply_post_rerun_creation_tasks_with_new_course_start_date(
            self, mock_set_rerun_course_dates, mock_initialize_course_settings):
        """
        Testing apply_post_rerun_creation_tasks method if course start date is valid and not
        default course start date
        """
        source_course = test_helpers.create_source_course(self.store, self.user,
                                                          datetime(2019, 9, 1, tzinfo=UTC))
        dest_course = CourseFactory.create(
            org='origin',
            number='the_beginning_22',
            run='second_test_2',
            display_name='destination course',
            start=datetime(2018, 8, 1, tzinfo=UTC)
        )
        helpers.apply_post_rerun_creation_tasks(source_course.id, dest_course.id, self.user.id)
        assert mock_initialize_course_settings.called
        assert mock_set_rerun_course_dates.called

    @patch('openedx.features.cms.helpers.set_rerun_course_dates')
    @patch('openedx.features.cms.helpers.initialize_course_settings')
    def test_apply_post_rerun_creation_tasks_with_default_course_start_date(
            self, mock_initialize_course_settings, mock_set_rerun_course_dates):
        """
        Testing apply_post_rerun_creation_tasks method if course start date is default date
        """
        source_course = test_helpers.create_source_course(self.store, self.user,
                                                          datetime(2019, 9, 1, tzinfo=UTC))
        dest_course_default_date = CourseFactory.create(
            org='origin',
            number='the_beginning_2',
            run='second_test_2',
            display_name='destination course',
            start=CourseFields.start.default
        )
        helpers.apply_post_rerun_creation_tasks(source_course.id, dest_course_default_date.id,
                                                self.user.id)
        assert mock_initialize_course_settings.called
        assert not mock_set_rerun_course_dates.called

    @patch('openedx.features.cms.helpers.set_rerun_ora_dates')
    @patch('openedx.features.cms.helpers.set_rerun_module_dates')
    @patch('openedx.features.cms.helpers.set_advanced_settings_due_date')
    @patch('openedx.features.cms.helpers.set_rerun_schedule_dates')
    def test_set_rerun_course_dates_with_load_factor(self, mock_set_rerun_schedule_dates,
                                                     mock_set_advanced_settings_due_date,
                                                     mock_set_rerun_module_dates,
                                                     mock_set_rerun_ora_dates):
        """
        Testing set_rerun_course_dates method with a source course having few children up to the
        level of component
        """
        source_courses = test_helpers.create_large_course(self.store, 2,
                                                          datetime(2019, 4, 1, tzinfo=UTC))
        rerun_courses = test_helpers.create_large_course(self.store, 2,
                                                         datetime(2019, 4, 1, tzinfo=UTC))
        source_courses[0].start = datetime(2019, 5, 1, tzinfo=UTC)

        source_course = get_course_by_id(source_courses[0].id)
        rerun_course = get_course_by_id(rerun_courses[0].id)

        helpers.set_rerun_course_dates(source_course, rerun_course, self.user.id)
        assert mock_set_rerun_schedule_dates.called
        assert mock_set_advanced_settings_due_date.called
        assert mock_set_rerun_module_dates.called
        assert mock_set_rerun_ora_dates.called

    @patch('openedx.features.cms.helpers.set_rerun_ora_dates')
    @patch('openedx.features.cms.helpers.set_rerun_module_dates')
    @patch('openedx.features.cms.helpers.set_advanced_settings_due_date')
    @patch('openedx.features.cms.helpers.set_rerun_schedule_dates')
    def test_set_rerun_course_dates_with_empty_course(self, mock_set_rerun_schedule_dates,
                                                      mock_set_advanced_settings_due_date,
                                                      mock_set_rerun_module_dates,
                                                      mock_set_rerun_ora_dates):
        """
        Testing set_rerun_course_dates method with empty source course
        """
        source_course = CourseFactory.create(
            modulestore=self.store,
            start=datetime(2019, 4, 1, tzinfo=UTC)
        )
        rerun_course = CourseFactory.create(
            modulestore=self.store,
            start=datetime(2019, 5, 1, tzinfo=UTC)
        )
        helpers.set_rerun_course_dates(source_course, rerun_course, self.user.id)

        assert not mock_set_rerun_schedule_dates.called
        assert not mock_set_advanced_settings_due_date.called
        assert not mock_set_rerun_module_dates.called
        assert not mock_set_rerun_ora_dates.called

    @patch('openedx.features.cms.helpers.calculate_date_by_delta')
    def test_set_rerun_schedule_dates(self, mock_calculate_date_by_delta):
        re_run_course = CourseFactory.create(
            org='org',
            number='number',
            run='test_dest',
            display_name='destination course',
            start=datetime(2019, 10, 1, tzinfo=UTC)
        )

        mock_calculate_date_by_delta.side_effect = [datetime(2020, 10, 1, tzinfo=UTC),
                                                    datetime(2019, 10, 1, tzinfo=UTC),
                                                    datetime(2019, 10, 10, tzinfo=UTC)]

        helpers.set_rerun_schedule_dates(re_run_course, mock.Mock(), self.user)

        # Testing course end, enrollment start and enrollment end date
        updated_dest_course = get_course_by_id(re_run_course.id)
        self.assertEqual(updated_dest_course.end, datetime(2020, 10, 1, tzinfo=UTC))
        self.assertEqual(updated_dest_course.enrollment_start, datetime(2019, 10, 1, tzinfo=UTC))
        self.assertEqual(updated_dest_course.enrollment_end, datetime(2019, 10, 10, tzinfo=UTC))

    @patch('openedx.features.cms.helpers.calculate_date_by_delta')
    def test_set_advanced_settings_due_date(self, mock_calculate_date_by_delta):
        """
        Testing adding valid course due date
        """
        re_run_course = CourseFactory.create(
            org='org',
            number='number',
            run='test_dest',
            display_name='destination course',
            start=datetime(2019, 10, 1, tzinfo=UTC)
        )

        mock_calculate_date_by_delta.return_value = datetime(2020, 10, 1, tzinfo=UTC)

        helpers.set_advanced_settings_due_date(re_run_course, mock.Mock(), self.user)
        assert mock_calculate_date_by_delta.called
        self.assertEqual(re_run_course.due, datetime(2020, 10, 1, tzinfo=UTC))

    @patch('openedx.features.cms.helpers.calculate_date_by_delta')
    def test_set_advanced_settings_due_date_source_course_without_due_date(
            self, mock_calculate_date_by_delta):
        """
        Testing adding course due date without providing date
        """
        source_course = mock.Mock()
        source_course.due = None
        helpers.set_advanced_settings_due_date(mock.ANY, source_course, mock.ANY)
        assert not mock_calculate_date_by_delta.called

    def test_set_rerun_module_dates(self):
        """
        Testing start date of chapters (sequence) and start & due date of sub-sequences
        (sequential) by creating a re-run of source course
        """
        source_course = test_helpers.create_source_course(self.store, self.user,
                                                          datetime(2019, 9, 1, tzinfo=UTC))

        rerun_course_start_date = datetime(2019, 10, 1, tzinfo=UTC)
        result, rerun_course_id = CourseRerunFactory.create(
            source_course_id=source_course.id,
            user=self.user,
            run="rerun_test",
            start=rerun_course_start_date
        )
        self.assertEqual(result.get(), "succeeded")

        # Re-run from source course complete
        # Testing start date of chapters (sequence)
        # Testing start and due date of sub-sequences (sequential)

        rerun_course = get_course_by_id(rerun_course_id)
        source_course_start_date = source_course.start
        re_run_start_date = rerun_course.start

        self.assertEqual(re_run_start_date, rerun_course_start_date)

        source_course_sections = source_course.get_children()
        source_course_subsections = [sub_section for s in source_course_sections for sub_section in
                                     s.get_children()]
        re_run_sections = rerun_course.get_children()
        re_run_subsections = [sub_section for s in re_run_sections for sub_section in
                              s.get_children()]

        re_run_modules = re_run_sections + re_run_subsections
        source_course_modules = source_course_sections + source_course_subsections

        helpers.set_rerun_module_dates(re_run_modules, source_course_modules,
                                       source_course_start_date,
                                       re_run_start_date, self.user)

        # chapter 1 (section)
        chapter1 = rerun_course.get_children()[0]
        self.assertEqual(chapter1.start, datetime(2019, 10, 1, tzinfo=UTC))
        # chapter (section) does not have due dates, so it must be None
        self.assertIsNone(chapter1.due)
        self.assertEqual(len(chapter1.get_children()), 1)

        # chapter 1, sequential 1 (sub-section)
        chapter1_sequential = chapter1.get_children()[0]
        self.assertEqual(chapter1_sequential.start, datetime(2019, 10, 1, tzinfo=UTC))
        # Due date we not set in source course, hence re-run course must not have it
        self.assertIsNone(chapter1_sequential.due)

        # chapter 2 (section)
        chapter2 = rerun_course.get_children()[1]
        self.assertEqual(chapter2.start, datetime(2019, 10, 31, tzinfo=UTC))
        # chapter (section) does not have due dates, so it must be None
        self.assertIsNone(chapter2.due)
        self.assertEqual(len(chapter2.get_children()), 2)

        chapter2_sequential1 = chapter2.get_children()[0]
        self.assertEqual(chapter2_sequential1.start, datetime(2019, 11, 9, tzinfo=UTC))
        self.assertEqual(chapter2_sequential1.due, datetime(2019, 11, 19, tzinfo=UTC))

        chapter2_sequential2 = chapter2.get_children()[1]
        self.assertEqual(chapter2_sequential2.start, datetime(2019, 12, 1, tzinfo=UTC))
        self.assertIsNone(chapter2_sequential2.due)

        # chapter 3 (section)
        chapter3 = rerun_course.get_children()[2]
        self.assertEqual(chapter3.start, datetime(2019, 12, 1, tzinfo=UTC))
        # chapter (section) does not have due dates, so it must be None
        self.assertIsNone(chapter3.due)
        # This chapter was empty
        self.assertFalse(chapter3.get_children())

    def test_calculate_date_by_delta_near_future(self):
        """
        Testing near future date by adding delta into it
        """
        date_to_update = datetime(2019, 9, 15)
        # delta is be 31 days
        source_course_start_date = datetime(2019, 1, 1, tzinfo=UTC)
        re_run_course_start_date = datetime(2019, 2, 1, tzinfo=UTC)

        result = helpers.calculate_date_by_delta(date_to_update, source_course_start_date,
                                                 re_run_course_start_date)
        self.assertEqual(result, datetime(2019, 10, 16, tzinfo=UTC))

    def test_calculate_date_by_delta_past(self):
        """
        Testing past date by adding delta into it
        """
        date_to_update = datetime(2019, 9, 15, tzinfo=UTC)
        # delta is be (-ive) 16 years 8 months 17 days
        source_course_start_date = datetime(2019, 1, 1, tzinfo=UTC)
        re_run_course_start_date = datetime(2002, 4, 15, tzinfo=UTC)

        result = helpers.calculate_date_by_delta(date_to_update, source_course_start_date,
                                                 re_run_course_start_date)
        # Manually calculated date is 1 day less than actual date
        self.assertEqual(result, datetime(2002, 12, 28, tzinfo=UTC))

    def test_calculate_date_by_delta_future(self):
        """
        Testing future date by adding delta into it
        """
        date_to_update = datetime(2019, 9, 15, tzinfo=UTC)
        # delta is be 9 years 3 months 14 days
        source_course_start_date = datetime(2019, 1, 1, tzinfo=UTC)
        re_run_course_start_date = datetime(2028, 4, 15, tzinfo=UTC)

        result = helpers.calculate_date_by_delta(date_to_update, source_course_start_date,
                                                 re_run_course_start_date)
        self.assertEqual(result, datetime(2028, 12, 28, tzinfo=UTC))

    def test_component_update_successful(self):
        """
        Testing updating component in store
        """
        courses = test_helpers.create_large_course(self.store, 1)
        components = self.store.get_items(
            courses[0].id,
            qualifiers={'category': 'html'}
        )

        # change title of component and update it via module store
        components[0].display_name = "Testing HTML"
        helpers.component_update(components[0], self.user)

        # Find component which is updated and get display name for testing
        updated_components = self.store.get_items(
            courses[0].id,
            qualifiers={'category': 'html'}
        )

        # since load factor was one, there should be only one html component
        self.assertEqual(len(updated_components), 1)
        self.assertEqual(updated_components[0].display_name, "Testing HTML")

    def test_set_rerun_ora_dates(self):
        """
        Testing all dates in ORA. In our case source_course can server the purpose of
        rerun_course, so we can consider source_course as rerun_course
        """
        rerun_course = test_helpers.create_source_course(self.store, self.user,
                                                         datetime(2019, 9, 1, tzinfo=UTC))
        # ORA dates will be updated by +ive 30 day
        source_course_start_date = datetime(2019, 9, 1, tzinfo=UTC)
        re_run_start_date = datetime(2019, 10, 1, tzinfo=UTC)

        re_run_sections = rerun_course.get_children()
        re_run_subsections = [sub_section for s in re_run_sections for sub_section in
                              s.get_children()]

        helpers.set_rerun_ora_dates(re_run_subsections, re_run_start_date, source_course_start_date,
                                    self.user)

        # Get updated ORA components from store
        ora_list_in_course = self.store.get_items(
            rerun_course.id, qualifiers={'category': 'openassessment'}
        )

        # course course had only two ORA components, re-run course must have same count
        self.assertEqual(len(ora_list_in_course), 2)
        ora_list_in_course.sort(key=lambda course: course.display_name, reverse=True)

        ora1 = ora_list_in_course[0]
        ora2 = ora_list_in_course[1]

        # assertions for ORA - default assessment dates

        self.assertEqual(ora1.display_name, "ORA - default assessment dates")
        self.assertEqual(parse(ora1.submission_start), datetime(2019, 1, 31, tzinfo=UTC))
        self.assertEqual(parse(ora1.submission_due), datetime(2019, 3, 3, tzinfo=UTC))

        ora1_student_training = ora1.rubric_assessments[0]
        self.assertIsNone(ora1_student_training['start'])
        self.assertIsNone(ora1_student_training['due'])
        self.assertEqual(ora1_student_training['name'], 'student-training')

        date_default_start = parse(DEFAULT_START)
        date_default_end = parse(DEFAULT_DUE)

        # peer, self and staff assessment all have default date so, their dates must not change
        iter_assessment = iter(ora1.rubric_assessments)
        next(iter_assessment)
        for assessment in iter_assessment:
            self.assertEqual(parse(assessment['start']), date_default_start)
            self.assertEqual(parse(assessment['due']), date_default_end)

        # assertions for ORA - all custom dates

        self.assertEqual(ora2.display_name, "ORA - all custom dates")
        self.assertEqual(parse(ora2.submission_start), datetime(2019, 1, 31, tzinfo=UTC))
        self.assertEqual(parse(ora2.submission_due), datetime(2019, 3, 3, tzinfo=UTC))

        ora2_student_training = ora2.rubric_assessments[0]
        self.assertIsNone(ora2_student_training['start'])
        self.assertIsNone(ora2_student_training['due'])
        self.assertEqual(ora2_student_training['name'], 'student-training')

        ora2_peer_assessment = ora2.rubric_assessments[1]
        # providing dates without time zone info
        self.assertEqual(parse(ora2_peer_assessment['start']), datetime(2019, 3, 31, tzinfo=UTC))
        self.assertEqual(parse(ora2_peer_assessment['due']), datetime(2019, 5, 1, tzinfo=UTC))

        ora2_self_assessment = ora2.rubric_assessments[2]
        self.assertEqual(parse(ora2_self_assessment['start']), datetime(2019, 5, 31, tzinfo=UTC))
        self.assertEqual(parse(ora2_self_assessment['due']), datetime(2019, 7, 1, tzinfo=UTC))

        ora2_staff_assessment = ora2.rubric_assessments[3]
        self.assertEqual(parse(ora2_staff_assessment['start']), datetime(2019, 7, 31, tzinfo=UTC))
        self.assertEqual(parse(ora2_staff_assessment['due']), datetime(2019, 8, 31, tzinfo=UTC))

    @patch('openedx.features.cms.helpers.create_new_run_id')
    @patch('openedx.features.cms.helpers.calculate_next_rerun_number')
    def test_update_course_re_run_details_for_multiple_rerun(
            self, mock_calculate_next_rerun_number, mock_create_new_run_id):
        """
        This method tests update_course_re_run_details helper method by mocking some of its parts
        """

        def side_effect_number_mapper(course_id):
            """
            This mapper is a helper function for mock, it used dict to map
            course_id to CourseLocator object
            """
            return number_mapping[course_id]

        number_mapping = {
            CourseLocator('organization', 'Phy101', '1_1.33_20091001_20100101', deprecated=True): 2,
            CourseLocator('organization', 'CS101', '4_1.31_20091001_20100101'): 5
        }

        def side_effect_run_mapper(run_number):
            """
            This mapper is a helper function for mock, it used dict to map
            run_number to complete run pattern
            """
            return run_mapping[run_number]

        run_mapping = {
            2: '2_1.33_20191001_20200101',
            5: '5_1.33_20191001_20200101',
            6: '6_1.34_20181001_20190101',
        }

        # Input dictionary for the method (as param), which we are testing
        course_rerun_details = [
            {
                "runs": [
                    {"release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"}
                ],
                "source_course_key": "organization/Phy101/1_1.33_20091001_20100101"
            },
            {
                "runs": [
                    {"release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"},
                    {"release_number": "1.34", "start_date": "10/01/2018", "start_time": "00:00"}
                ],
                "source_course_key": "course-v1:organization+CS101+4_1.31_20091001_20100101"
            }
        ]

        # The expected output of the method (as return value), which we are testing
        expected_course_re_run_details = [
            {
                'source_course_key': CourseLocator('organization', 'Phy101',
                                                   '1_1.33_20091001_20100101',
                                                   deprecated=True),
                'runs': [
                    {
                        'start_time': '00:00', 'run': '2_1.33_20191001_20200101',
                        'start_date': '10/01/2019', 'release_number': '1.33'
                    }
                ],
                'org': 'organization', 'display_name': 'Physics', 'number': 'Phy101'
            },
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'runs': [
                    {
                        'start_time': '00:00', 'run': '5_1.33_20191001_20200101',
                        'start_date': '10/01/2019', 'release_number': '1.33'
                    },
                    {
                        'start_time': '00:00', 'run': '6_1.34_20181001_20190101',
                        'start_date': '10/01/2018', 'release_number': '1.34'
                    }
                ],
                'org': 'organization', 'display_name': 'Computer Science', 'number': 'CS101'
            }
        ]

        test_helpers.create_course(self.store, self.user)

        # using side_effect to provide mocked data (by mapping) to specific inputs
        mock_calculate_next_rerun_number.side_effect = side_effect_number_mapper
        mock_create_new_run_id.side_effect = side_effect_run_mapper

        updated_course_rerun_details = helpers.update_course_re_run_details(course_rerun_details)

        self.assertEqual(updated_course_rerun_details, expected_course_re_run_details)

    def test_update_course_re_run_details_raise_course_end_date_error(self):

        CourseFactory.create(
            org='org',
            number='num',
            run='dummy_run',
            start=datetime(2009, 10, 1, tzinfo=UTC),
            enrollment_start=datetime(2009, 10, 1, tzinfo=UTC),
            enrollment_end=datetime(2009, 10, 10, tzinfo=UTC),
        )

        # course rerun in following dict, does not have course end date set
        expected_course_re_run_details = [
            {"source_course_key": "org/num/dummy_run"}
        ]

        with self.assertRaises(Exception) as error:
            helpers.update_course_re_run_details(expected_course_re_run_details)

        expected_error_message = ERROR_MESSAGES['course_end_date_missing']
        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, expected_course_re_run_details[0]['error'])

    def test_update_course_re_run_details_raise_enrollment_start_date_error(self):
        CourseFactory.create(
            org='org',
            number='num',
            run='dummy_run',
            start=datetime(2009, 10, 1, tzinfo=UTC),
            end=datetime(2010, 10, 1, tzinfo=UTC),
            enrollment_end=datetime(2009, 10, 10, tzinfo=UTC),
        )

        # course rerun in following dict, does not have enrollment start date set
        expected_course_re_run_details = [
            {"source_course_key": "org/num/dummy_run"}
        ]

        with self.assertRaises(Exception) as error:
            helpers.update_course_re_run_details(expected_course_re_run_details)

        expected_error_message = ERROR_MESSAGES['enrollment_start_date_missing']
        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, expected_course_re_run_details[0]['error'])

    def test_update_course_re_run_details_raise_multiple_date_errors(self):

        test_helpers.create_course(self.store, self.user)

        # course rerun in following dict, does not have any of the dates set
        # i.e. course end, enrollment_start, enrollment_start, hence enrollment end
        # error will be raised
        expected_course_re_run_details = [
            {"source_course_key": "course-v1:organization+Mth101+3_1.30_20091001_20100101"}
        ]

        with self.assertRaises(Exception) as error:
            helpers.update_course_re_run_details(expected_course_re_run_details)

        expected_error_message = ' '.join(
            [
                ERROR_MESSAGES['course_end_date_missing'],
                ERROR_MESSAGES['enrollment_start_date_missing'],
                ERROR_MESSAGES['enrollment_end_date_missing']
            ]
        )

        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, expected_course_re_run_details[0]['error'])

    def test_calculate_next_rerun_number_for_valid_run(self):
        course = CourseFactory.create(
            org='org',
            number='num',
            run='5_x_y_z',
            start=datetime(2009, 10, 1, tzinfo=UTC),
        )
        run_number = helpers.calculate_next_rerun_number(course.id)
        # If run is as per required pattern, just increment run number
        self.assertEqual(run_number, 6)

    @patch('openedx.features.cms.helpers.get_course_group')
    def test_calculate_next_rerun_number_for_invalid_number_of_underscores(
            self, mock_get_course_group):
        course = CourseFactory.create(
            org='org',
            number='num',
            run='5_1.1_2009_10_10_2010_10_10',
            start=datetime(2009, 10, 1, tzinfo=UTC),
        )
        # let get_course_group return dummy list of group ids of size 10
        # so that we can assure we have a group of 10 courses
        mock_get_course_group.return_value = [0] * 10
        run_number = helpers.calculate_next_rerun_number(course.id)
        # If run is not as per required pattern,
        # run number will be calculated from group count
        self.assertEqual(run_number, 11)

    @patch('openedx.features.cms.helpers.get_course_group')
    def test_calculate_next_rerun_number_run_number_not_digit(self, mock_get_course_group):
        # Run number is not digit i.e. xyz
        course = CourseFactory.create(
            org='org',
            number='num',
            run='xyz_1.1_20091010_20101010',
            start=datetime(2009, 10, 1, tzinfo=UTC),
        )
        # let get_course_group return dummy list of group ids of size 10
        # so that we can assure we have a group of 10 courses
        mock_get_course_group.return_value = [0] * 10
        run_number = helpers.calculate_next_rerun_number(course.id)
        # If run is not as per required pattern,
        # run number will be calculated from group count
        self.assertEqual(run_number, 11)

    @patch('openedx.features.cms.helpers.calculate_date_by_delta')
    def test_create_new_run_id(self, mock_calculate_date_by_delta):
        mock_calculate_date_by_delta.return_value = datetime(2019, 12, 20, tzinfo=UTC)
        run_dict = {"release_number": "1.33", "start": datetime(2019, 10, 1, tzinfo=UTC)}
        run_number = 9
        # course start and end date will be ignored because calculate_date_by_delta
        # return value is mocked
        course = CourseFactory.create(start=None, end=None)
        new_run_id = helpers.create_new_run_id(run_dict, course, run_number)
        self.assertEqual(new_run_id, "9_1.33_20191001_20191220")

        run_dict['release_number'] = ""

        with self.assertRaises(Exception):
            helpers.create_new_run_id(run_dict, course, run_number)

    def test_get_course_group_parent_course_without_reruns(self):
        course = CourseFactory.create(
            org='org',
            number='num',
            run='5_1.1_2009_10_10_2010_10_10',
            start=datetime(2009, 10, 1, tzinfo=UTC),
        )
        # Get course group from parent course
        course_ids = helpers.get_course_group(course.id)
        self.assertEqual(course_ids, [course.id])

    def test_get_course_group_from_parent_course_with_all_successful_reruns(self):
        # Creating group as test data, group contains parent course
        # and two successful reruns
        test_course_ids = test_helpers.create_course_and_two_rerun(self.store, self.user)
        # Get course group from parent course
        course_ids = helpers.get_course_group(test_course_ids[0])
        self.assertItemsEqual(course_ids, test_course_ids)

    def test_get_course_group_from_parent_course_with_all_unsuccessful_reruns(self):
        # Creating group as test data, group contains parent course
        # and two unsuccessful reruns
        test_course_ids = test_helpers.create_course_and_two_rerun(self.store, self.user, False)
        # Get course group from parent course
        course_ids = helpers.get_course_group(test_course_ids[0])
        self.assertItemsEqual(course_ids, [test_course_ids[0]])

    def test_get_course_group_from_rerun_course(self):
        # Creating group as test data, group contains parent course
        # and two successful reruns
        test_course_ids = test_helpers.create_course_and_two_rerun(self.store, self.user)
        # Get course group from rerun
        course_ids = helpers.get_course_group(test_course_ids[1])
        self.assertItemsEqual(course_ids, test_course_ids)

    def test_raise_rerun_creation_exception(self):
        details_dict = {'dummy': 'value'}
        error_message = "Testing error message"
        expected_details_dict = {'dummy': 'value', 'error': error_message}

        with self.assertRaises(Exception) as error:
            helpers.raise_rerun_creation_exception(details_dict, error_message, Exception)

        self.assertEqual(details_dict, expected_details_dict)
        self.assertEqual(error_message, str(error.exception))

    def test_raise_rerun_creation_exception_without_exception_class(self):
        details_dict = {'dummy': 'value'}
        error_message = "Testing error message"
        expected_details_dict = {'dummy': 'value', 'error': error_message}

        returned_error_message = helpers.raise_rerun_creation_exception(details_dict, error_message)

        self.assertEqual(details_dict, expected_details_dict)
        self.assertEqual(error_message, returned_error_message)

    def test_latest_course_reruns(self):

        expected_latest_course = test_helpers.create_course(self.store, self.user)
        # Get all course summaries from the store
        courses = self.store.get_course_summaries()

        latest_courses = helpers.latest_course_reruns(courses)

        latest_courses_id = [course.id for course in latest_courses]
        expected_latest_courses_id = [course.id for course in expected_latest_course]

        self.assertItemsEqual(latest_courses_id, expected_latest_courses_id)
