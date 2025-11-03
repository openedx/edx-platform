"""
Unit tests for instructor API v2 endpoints.
"""
import json
from unittest.mock import Mock, patch
from urllib.parse import urlencode
from uuid import uuid4

import ddt
from django.urls import NoReverseMatch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from common.djangoapps.student.tests.factories import (
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
        )
        cls.course_key = cls.course.id

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.instructor = InstructorFactory.create(course_key=self.course_key)
        self.staff = StaffFactory.create(course_key=self.course_key)
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

    def test_tabs_include_course_info(self):
        """
        Test that sections include course_info which is always visible.
        """
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self._get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sections = response.data['tabs']

        # Find courseware section
        course_info_section = next(
            (s for s in sections if s['tab_id'] == 'course_info'),
            None
        )
        self.assertIsNotNone(course_info_section)
        self.assertEqual(course_info_section['title'], 'Course Info')
        self.assertEqual(course_info_section['is_hidden'], False)

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
