"""
Tests for the course import API views
"""
from datetime import datetime
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import StaffFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class CourseValidationViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test course validation view via a RESTful API
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(CourseValidationViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_key = cls.course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course.id, password=cls.password)

        cls.initialize_course(cls.course)

    @classmethod
    def initialize_course(cls, course):
        course.start = datetime.now()
        course.self_paced = True
        cls.store.update_item(course, cls.staff.id)

        update_key = course.id.make_usage_key('course_info', 'updates')
        cls.store.create_item(
            cls.staff.id,
            update_key.course_key,
            update_key.block_type,
            block_id=update_key.block_id,
            fields=dict(data=u"<ol><li><h2>Date</h2>Hello world!</li></ol>"),
        )

        section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
        )
        ItemFactory.create(
            parent_location=section.location,
            category="sequential",
        )

    def get_url(self, course_id):
        """
        Helper function to create the url
        """
        return reverse(
            'courses_api:course_validation',
            kwargs={
                'course_id': course_id,
            }
        )

    def test_student_fails(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_succeeds(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key), {'all': 'true'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = {
            'assignments': {
                'total_number': 1,
                'total_visible': 1,
                'assignments_with_dates_before_start': [],
                'assignments_with_dates_after_end': [],
                'assignments_with_ora_dates_after_end': [],
                'assignments_with_ora_dates_before_start': [],
            },
            'dates': {
                'has_start_date': True,
                'has_end_date': False,
            },
            'updates': {
                'has_update': True,
            },
            'certificates': {
                'is_enabled': True,
                'is_activated': False,
                'has_certificate': False,
            },
            'grades': {
                'has_grading_policy': False,
                'sum_of_weights': 1.0,
            },
            'is_self_paced': True,
        }
        self.assertDictEqual(resp.data, expected_data)
