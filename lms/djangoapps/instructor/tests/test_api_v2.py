"""
Unit tests for instructor API v2 endpoints.
"""
import json
from datetime import datetime
from unittest.mock import Mock, patch
from urllib.parse import urlencode
from uuid import uuid4

import ddt
from django.urls import NoReverseMatch
from django.urls import reverse
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient

from common.djangoapps.student.roles import CourseDataResearcherRole, CourseInstructorRole
from common.djangoapps.student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    InstructorFactory,
    StaffFactory,
    UserFactory,
)
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.instructor_task.tests.factories import InstructorTaskFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


@ddt.ddt
class CourseMetadataViewTest(SharedModuleStoreTestCase):
    """
    Tests for the CourseMetadataView API endpoint.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create(
            org='edX',
            number='DemoX',
            run='Demo_Course',
            display_name='Demonstration Course',
            self_paced=False,
            enable_proctored_exams=True,
        )
        cls.proctored_course = CourseFactory.create(
            org='edX',
            number='Proctored',
            run='2024',
            display_name='Demonstration Proctored Course',
        )

        cls.course_key = cls.course.id

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.admin = AdminFactory.create()
        self.instructor = InstructorFactory.create(course_key=self.course_key)
        self.staff = StaffFactory.create(course_key=self.course_key)
        self.data_researcher = UserFactory.create()
        CourseDataResearcherRole(self.course_key).add_users(self.data_researcher)
        CourseInstructorRole(self.proctored_course.id).add_users(self.instructor)
        self.student = UserFactory.create()

        # Create some enrollments for testing
        CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course_key,
            mode='audit',
            is_active=True
        )
        CourseEnrollmentFactory.create(
            user=UserFactory.create(),
            course_id=self.course_key,
            mode='verified',
            is_active=True
        )
        CourseEnrollmentFactory.create(
            user=UserFactory.create(),
            course_id=self.course_key,
            mode='honor',
            is_active=True
        )
        CourseEnrollmentFactory.create(
            user=UserFactory.create(),
            course_id=self.proctored_course.id,
            mode='verified',
            is_active=True
        )

    def _get_url(self, course_id=None):
        """Helper to get the API URL."""
        if course_id is None:
            course_id = str(self.course_key)
        return reverse('instructor_api_v2:course_metadata', kwargs={'course_id': course_id})

    def test_get_course_metadata_as_instructor(self):
        """
        Test that an instructor can retrieve comprehensive course metadata.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Verify basic course information
        self.assertEqual(data['course_id'], str(self.course_key))
        self.assertEqual(data['display_name'], 'Demonstration Course')
        self.assertEqual(data['org'], 'edX')
        self.assertEqual(data['course_number'], 'DemoX')
        self.assertEqual(data['course_run'], 'Demo_Course')
        self.assertEqual(data['pacing'], 'instructor')

        # Verify enrollment counts structure
        self.assertIn('enrollment_counts', data)
        self.assertIn('total', data['enrollment_counts'])
        self.assertIn('total_enrollment', data)
        self.assertGreaterEqual(data['total_enrollment'], 3)

        # Verify permissions structure
        self.assertIn('permissions', data)
        permissions_data = data['permissions']
        self.assertIn('admin', permissions_data)
        self.assertIn('instructor', permissions_data)
        self.assertIn('staff', permissions_data)
        self.assertIn('forum_admin', permissions_data)
        self.assertIn('finance_admin', permissions_data)
        self.assertIn('sales_admin', permissions_data)
        self.assertIn('data_researcher', permissions_data)

        # Verify sections structure
        self.assertIn('tabs', data)
        self.assertIsInstance(data['tabs'], list)

        # Verify other metadata fields
        self.assertIn('num_sections', data)
        self.assertIn('tabs', data)
        self.assertIn('grade_cutoffs', data)
        self.assertIn('course_errors', data)
        self.assertIn('studio_url', data)
        self.assertIn('disable_buttons', data)
        self.assertIn('has_started', data)
        self.assertIn('has_ended', data)
        self.assertIn('analytics_dashboard_message', data)

    def test_get_course_metadata_as_staff(self):
        """
        Test that course staff can retrieve course metadata.
        """
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['course_id'], str(self.course_key))
        self.assertIn('permissions', data)
        # Staff should have staff permission
        self.assertTrue(data['permissions']['staff'])

    def test_get_course_metadata_unauthorized(self):
        """
        Test that students cannot access course metadata endpoint.
        """
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_code = "You do not have permission to perform this action."
        self.assertEqual(response.data['developer_message'], error_code)

    def test_get_course_metadata_unauthenticated(self):
        """
        Test that unauthenticated users cannot access the endpoint.
        """
        response = self.client.get(self._get_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_course_metadata_invalid_course_id(self):
        """
        Test error handling for invalid course ID.
        """
        self.client.force_authenticate(user=self.instructor)
        invalid_course_id = 'invalid-course-id'
        with self.assertRaises(NoReverseMatch):
            self.client.get(self._get_url(course_id=invalid_course_id))

    def test_get_course_metadata_nonexistent_course(self):
        """
        Test error handling for non-existent course.
        """
        self.client.force_authenticate(user=self.instructor)
        nonexistent_course_id = 'course-v1:edX+NonExistent+2024'
        response = self.client.get(self._get_url(course_id=nonexistent_course_id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        error_code = "Course not found: course-v1:edX+NonExistent+2024."
        self.assertEqual(response.data['developer_message'], error_code)

    def test_instructor_permissions_reflected(self):
        """
        Test that instructor permissions are correctly reflected in response.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions_data = response.data['permissions']

        # Instructor should have instructor permission
        self.assertTrue(permissions_data['instructor'])

    def test_enrollment_counts_by_mode(self):
        """
        Test that enrollment counts include breakdown by mode.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment_counts = response.data['enrollment_counts']

        # Should have total count
        self.assertIn('total', enrollment_counts)
        self.assertGreaterEqual(enrollment_counts['total'], 3)

    def _get_tabs_from_response(self, user, course_id=None):
        """Helper to get tabs from API response."""
        self.client.force_authenticate(user=user)
        response = self.client.get(self._get_url(course_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data.get('tabs', [])

    def _test_staff_tabs(self, tabs):
        """Helper to test tabs visible to staff users."""
        tab_ids = [tab['tab_id'] for tab in tabs]

        # Staff should see these basic tabs
        expected_basic_tabs = ['course_info', 'enrollments', 'course_team', 'grading', 'cohorts']
        self.assertListEqual(tab_ids, expected_basic_tabs)

    def test_staff_sees_basic_tabs(self):
        """
        Test that staff users see the basic set of tabs.
        """
        tabs = self._get_tabs_from_response(self.staff)
        self._test_staff_tabs(tabs)

    def test_instructor_sees_all_basic_tabs(self):
        """
        Test that instructors see all tabs that staff see.
        """
        instructor_tabs = self._get_tabs_from_response(self.instructor)
        self._test_staff_tabs(instructor_tabs)

    def test_researcher_sees_all_basic_tabs(self):
        """
        Test that instructors see all tabs that staff see.
        """
        tabs = self._get_tabs_from_response(self.data_researcher)
        tab_ids = [tab['tab_id'] for tab in tabs]
        self.assertEqual(['data_downloads'], tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.is_enabled_for_course')
    def test_date_extensions_tab_when_enabled(self, mock_is_enabled):
        """
        Test that date_extensions tab appears when edx-when is enabled for the course.
        """
        mock_is_enabled.return_value = True

        tabs = self._get_tabs_from_response(self.instructor)
        tab_ids = [tab['tab_id'] for tab in tabs]

        self.assertIn('date_extensions', tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.modulestore')
    def test_open_responses_tab_with_openassessment_blocks(self, mock_modulestore):
        """
        Test that open_responses tab appears when course has openassessment blocks.
        """
        # Mock openassessment block
        mock_block = Mock()
        mock_block.parent = Mock()  # Has a parent (not orphaned)
        mock_store = Mock()
        mock_store.get_items.return_value = [mock_block]
        mock_store.get_course_errors.return_value = []
        mock_modulestore.return_value = mock_store

        tabs = self._get_tabs_from_response(self.staff)
        tab_ids = [tab['tab_id'] for tab in tabs]

        self.assertIn('open_responses', tab_ids)

    @patch('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True, 'MAX_ENROLLMENT_INSTR_BUTTONS': 200})
    def test_special_exams_tab_with_proctored_exams_enabled(self):
        """
        Test that special_exams tab appears when course has proctored exams enabled.
        """
        tabs = self._get_tabs_from_response(self.instructor)
        tab_ids = [tab['tab_id'] for tab in tabs]

        self.assertIn('special_exams', tab_ids)

    @patch('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True, 'MAX_ENROLLMENT_INSTR_BUTTONS': 200})
    def test_special_exams_tab_with_timed_exams_enabled(self):
        """
        Test that special_exams tab appears when course has timed exams enabled.
        """
        # Create course with timed exams
        timed_course = CourseFactory.create(
            org='edX',
            number='Timed',
            run='2024',
            enable_timed_exams=True,
        )
        CourseInstructorRole(timed_course.id).add_users(self.instructor)
        tabs = self._get_tabs_from_response(self.instructor, course_id=timed_course.id)
        tab_ids = [tab['tab_id'] for tab in tabs]
        self.assertIn('special_exams', tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.CertificateGenerationConfiguration.current')
    @patch('django.conf.settings.FEATURES', {'ENABLE_CERTIFICATES_INSTRUCTOR_MANAGE': True,
                                             'MAX_ENROLLMENT_INSTR_BUTTONS': 200})
    def test_certificates_tab_for_instructor_when_enabled(self, mock_cert_config):
        """
        Test that certificates tab appears for instructors when certificate management is enabled.
        """
        mock_config = Mock()
        mock_config.enabled = True
        mock_cert_config.return_value = mock_config

        tabs = self._get_tabs_from_response(self.instructor)
        tab_ids = [tab['tab_id'] for tab in tabs]
        self.assertIn('certificates', tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.CertificateGenerationConfiguration.current')
    def test_certificates_tab_for_admin_visible(self, mock_cert_config):
        """
        Test that certificates tab appears for admin users when certificates are enabled.
        """
        mock_config = Mock()
        mock_config.enabled = True
        mock_cert_config.return_value = mock_config

        tabs = self._get_tabs_from_response(self.admin)
        tab_ids = [tab['tab_id'] for tab in tabs]
        self.assertIn('certificates', tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.is_bulk_email_feature_enabled')
    @ddt.data('staff', 'instructor', 'admin')
    def test_bulk_email_tab_when_enabled(self, user_attribute, mock_bulk_email_enabled):
        """
        Test that the bulk_email tab appears for all staff-level users when is_bulk_email_feature_enabled is True.
        """
        mock_bulk_email_enabled.return_value = True

        user = getattr(self, user_attribute)
        tabs = self._get_tabs_from_response(user)
        tab_ids = [tab['tab_id'] for tab in tabs]

        self.assertIn('bulk_email', tab_ids)

    @patch('lms.djangoapps.instructor.views.serializers_v2.is_bulk_email_feature_enabled')
    @ddt.data(
        (False, 'staff'),
        (False, 'instructor'),
        (False, 'admin'),
        (True, 'data_researcher'),
    )
    @ddt.unpack
    def test_bulk_email_tab_not_visible(self, feature_enabled, user_attribute, mock_bulk_email_enabled):
        """
        Test that the bulk_email tab does not appear when is_bulk_email_feature_enabled is False or the user is not
        a user with staff permissions.
        """
        mock_bulk_email_enabled.return_value = feature_enabled

        user = getattr(self, user_attribute)
        tabs = self._get_tabs_from_response(user)
        tab_ids = [tab['tab_id'] for tab in tabs]

        self.assertNotIn('bulk_email', tab_ids)

    def test_tabs_have_sort_order(self):
        """
        Test that all tabs include a sort_order field.
        """
        tabs = self._get_tabs_from_response(self.staff)

        for tab in tabs:
            self.assertIn('sort_order', tab)
            self.assertIsInstance(tab['sort_order'], int)

    def test_disable_buttons_false_for_small_course(self):
        """
        Test that disable_buttons is False for courses with <=200 enrollments.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With only 3 enrollments, buttons should not be disabled
        self.assertFalse(response.data['disable_buttons'])

    @patch('lms.djangoapps.instructor.views.serializers_v2.modulestore')
    def test_course_errors_from_modulestore(self, mock_modulestore):
        """
        Test that course errors from modulestore are included in response.
        """
        mock_store = Mock()
        mock_store.get_course_errors.return_value = [(Exception("Test error"), '')]
        mock_store.get_items.return_value = []
        mock_modulestore.return_value = mock_store

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('course_errors', response.data)
        self.assertIsInstance(response.data['course_errors'], list)

    def test_pacing_self_for_self_paced_course(self):
        """
        Test that pacing is 'self' for self-paced courses.
        """
        # Create a self-paced course
        self_paced_course = CourseFactory.create(
            org='edX',
            number='SelfPaced',
            run='SP1',
            self_paced=True,
        )
        instructor = InstructorFactory.create(course_key=self_paced_course.id)

        self.client.force_authenticate(user=instructor)
        url = reverse('instructor_api_v2:course_metadata', kwargs={'course_id': str(self_paced_course.id)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pacing'], 'self')


@ddt.ddt
class InstructorTaskListViewTest(SharedModuleStoreTestCase):
    """
    Tests for the InstructorTaskListView API endpoint.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create(
            org='edX',
            number='TestX',
            run='Test_Course',
            display_name='Test Course',
        )
        cls.course_key = cls.course.id

        # Create a problem block for testing
        cls.chapter = BlockFactory.create(
            parent=cls.course,
            category='chapter',
            display_name='Test Chapter'
        )
        cls.sequential = BlockFactory.create(
            parent=cls.chapter,
            category='sequential',
            display_name='Test Sequential'
        )
        cls.vertical = BlockFactory.create(
            parent=cls.sequential,
            category='vertical',
            display_name='Test Vertical'
        )
        cls.problem = BlockFactory.create(
            parent=cls.vertical,
            category='problem',
            display_name='Test Problem'
        )
        cls.problem_location = str(cls.problem.location)

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.instructor = InstructorFactory.create(course_key=self.course_key)
        self.student = UserFactory.create()

    def _get_url(self, course_id=None):
        """Helper to get the API URL."""
        if course_id is None:
            course_id = str(self.course_key)
        return reverse('instructor_api_v2:instructor_tasks', kwargs={'course_id': course_id})

    def test_get_instructor_tasks_as_instructor(self):
        """
        Test that an instructor can retrieve instructor tasks.
        """
        # Create a test task
        task_id = str(uuid4())
        InstructorTaskFactory.create(
            course_id=self.course_key,
            task_type='grade_problems',
            task_state='PROGRESS',
            requester=self.instructor,
            task_id=task_id,
            task_key="dummy key",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIsInstance(response.data['tasks'], list)

    def test_get_instructor_tasks_unauthorized(self):
        """
        Test that students cannot access instructor tasks endpoint.
        """
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You do not have permission to perform this action.', response.data['developer_message'])

    def test_get_instructor_tasks_unauthenticated(self):
        """
        Test that unauthenticated users cannot access the endpoint.
        """
        response = self.client.get(self._get_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_instructor_tasks_nonexistent_course(self):
        """
        Test error handling for non-existent course.
        """
        self.client.force_authenticate(user=self.instructor)
        nonexistent_course_id = 'course-v1:edX+NonExistent+2024'
        response = self.client.get(self._get_url(course_id=nonexistent_course_id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual('Course not found: course-v1:edX+NonExistent+2024.', response.data['developer_message'])

    def test_filter_by_problem_location(self):
        """
        Test filtering tasks by problem location.
        """
        self.client.force_authenticate(user=self.instructor)
        params = {
            'problem_location_str': self.problem_location,
        }
        url = f"{self._get_url()}?{urlencode(params)}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)

    def test_filter_requires_problem_location_with_student(self):
        """
        Test that student identifier requires problem location.
        """
        self.client.force_authenticate(user=self.instructor)

        self.client.force_authenticate(user=self.instructor)
        params = {
            'unique_student_identifier': self.student.email,
        }
        url = f"{self._get_url()}?{urlencode(params)}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('problem_location_str', response.data['error'])

    def test_filter_by_problem_and_student(self):
        """
        Test filtering tasks by both problem location and student identifier.
        """
        # Enroll the student
        CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course_key,
            is_active=True
        )

        StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 10}),
        )

        task_id = str(uuid4())
        InstructorTaskFactory.create(
            course_id=self.course_key,
            task_state='PROGRESS',
            requester=self.student,
            task_id=task_id,
            task_key="dummy key",
        )

        self.client.force_authenticate(user=self.instructor)
        params = {
            'problem_location_str': self.problem_location,
            'unique_student_identifier': self.student.email,
        }
        url = f"{self._get_url()}?{urlencode(params)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)

    def test_invalid_student_identifier(self):
        """
        Test error handling for invalid student identifier.
        """
        self.client.force_authenticate(user=self.instructor)
        params = {
            'problem_location_str': self.problem_location,
            'unique_student_identifier': 'nonexistent@example.com',
        }
        url = f"{self._get_url()}?{urlencode(params)}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_invalid_problem_location(self):
        """
        Test error handling for invalid problem location.
        """
        self.client.force_authenticate(user=self.instructor)

        url = f"{self._get_url()}?problem_location_str=invalid-location"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid problem location', response.data['error'])

    @ddt.data(
        ('grade_problems', 'PROGRESS'),
        ('rescore_problem', 'SUCCESS'),
        ('reset_student_attempts', 'FAILURE'),
    )
    @ddt.unpack
    def test_various_task_types_and_states(self, task_type, task_state):
        """
        Test that various task types and states are properly returned.
        """
        task_id = str(uuid4())
        InstructorTaskFactory.create(
            course_id=self.course_key,
            task_type=task_type,
            task_state=task_state,
            requester=self.instructor,
            task_id=task_id,
            task_key="dummy key",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        if task_state == 'PROGRESS':
            self.assertEqual(task_id, response.data['tasks'][0]['task_id'])
            self.assertEqual(task_type, response.data['tasks'][0]['task_type'])
            self.assertEqual(task_state, response.data['tasks'][0]['task_state'])

    def test_task_data_structure(self):
        """
        Test that task data contains expected fields from extract_task_features.
        """
        task_id = str(uuid4())
        InstructorTaskFactory.create(
            course_id=self.course_key,
            task_type='grade_problems',
            task_state='PROGRESS',
            requester=self.instructor,
            task_id=task_id,
            task_key="dummy key",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = response.data['tasks']

        if tasks:
            task_data = tasks[0]
            # Verify key fields are present (these come from extract_task_features)
            self.assertIn('task_type', task_data)
            self.assertIn('task_state', task_data)
            self.assertIn('created', task_data)


@ddt.ddt
class GradedSubsectionsViewTest(SharedModuleStoreTestCase):
    """
    Tests for the GradedSubsectionsView API endpoint.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create(
            org='edX',
            number='DemoX',
            run='Demo_Course',
            display_name='Demonstration Course',
        )
        cls.course_key = cls.course.id

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.instructor = InstructorFactory.create(course_key=self.course_key)
        self.staff = StaffFactory.create(course_key=self.course_key)
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course_key,
            mode='audit',
            is_active=True
        )

        # Create some subsections with due dates
        self.chapter = BlockFactory.create(
            parent=self.course,
            category='chapter',
            display_name='Test Chapter'
        )
        self.due_date = datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC)
        self.subsection_with_due_date = BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Homework 1',
            due=self.due_date
        )
        self.subsection_without_due_date = BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Reading Material'
        )
        self.problem = BlockFactory.create(
            parent=self.subsection_with_due_date,
            category='problem',
            display_name='Test Problem'
        )

    def _get_url(self, course_id=None):
        """Helper to get the API URL."""
        if course_id is None:
            course_id = str(self.course_key)
        return reverse('instructor_api_v2:graded_subsections', kwargs={'course_id': course_id})

    def test_get_graded_subsections_success(self):
        """
        Test that an instructor can retrieve graded subsections with due dates.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('items', response_data)
        self.assertIsInstance(response_data['items'], list)

        # Should include subsection with due date
        items = response_data['items']
        if items:  # Only test if there are items with due dates
            item = items[0]
            self.assertIn('display_name', item)
            self.assertIn('subsection_id', item)
            self.assertIsInstance(item['display_name'], str)
            self.assertIsInstance(item['subsection_id'], str)

    def test_get_graded_subsections_as_staff(self):
        """
        Test that staff can retrieve graded subsections.
        """
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('items', response_data)

    def test_get_graded_subsections_nonexistent_course(self):
        """
        Test error handling for non-existent course.
        """
        self.client.force_authenticate(user=self.instructor)
        nonexistent_course_id = 'course-v1:NonExistent+Course+2024'
        nonexistent_url = self._get_url(nonexistent_course_id)
        response = self.client.get(nonexistent_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_graded_subsections_empty_course(self):
        """
        Test graded subsections for course without due dates.
        """
        # Create a completely separate course without any subsections with due dates
        empty_course = CourseFactory.create(
            org='EmptyTest',
            number='EmptyX',
            run='Empty2024',
            display_name='Empty Test Course'
        )
        # Don't add any subsections to this course
        empty_instructor = InstructorFactory.create(course_key=empty_course.id)

        self.client.force_authenticate(user=empty_instructor)
        response = self.client.get(self._get_url(str(empty_course.id)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        # An empty course should have no graded subsections with due dates
        self.assertEqual(response_data['items'], [])

    @patch('lms.djangoapps.instructor.views.api_v2.get_units_with_due_date')
    def test_get_graded_subsections_with_mocked_units(self, mock_get_units):
        """
        Test graded subsections response format with mocked data.
        """
        # Mock a unit with due date
        mock_unit = Mock()
        mock_unit.display_name = 'Mocked Assignment'
        mock_unit.location = Mock()
        mock_unit.location.__str__ = Mock(return_value='block-v1:Test+Course+2024+type@sequential+block@mock')
        mock_get_units.return_value = [mock_unit]

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        items = response_data['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['display_name'], 'Mocked Assignment')
        self.assertEqual(items[0]['subsection_id'], 'block-v1:Test+Course+2024+type@sequential+block@mock')

    @patch('lms.djangoapps.instructor.views.api_v2.title_or_url')
    @patch('lms.djangoapps.instructor.views.api_v2.get_units_with_due_date')
    def test_get_graded_subsections_title_fallback(self, mock_get_units, mock_title_or_url):
        """
        Test graded subsections when display_name is not available.
        """
        # Mock a unit without display_name
        mock_unit = Mock()
        mock_unit.location = Mock()
        mock_unit.location.__str__ = Mock(return_value='block-v1:Test+Course+2024+type@sequential+block@fallback')
        mock_get_units.return_value = [mock_unit]
        mock_title_or_url.return_value = 'block-v1:Test+Course+2024+type@sequential+block@fallback'

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        items = response_data['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['display_name'], 'block-v1:Test+Course+2024+type@sequential+block@fallback')
        self.assertEqual(items[0]['subsection_id'], 'block-v1:Test+Course+2024+type@sequential+block@fallback')

    def test_get_graded_subsections_response_format(self):
        """
        Test that the response has the correct format.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = json.loads(response.content)
        # Verify top-level structure
        self.assertIn('items', response_data)
        self.assertIsInstance(response_data['items'], list)

        # Verify each item has required fields
        for item in response_data['items']:
            self.assertIn('display_name', item)
            self.assertIn('subsection_id', item)
            self.assertIsInstance(item['display_name'], str)
            self.assertIsInstance(item['subsection_id'], str)
