"""
Tests for the course import API views
"""
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import StaffFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class CourseQualityViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test course quality view via a RESTful API
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(CourseQualityViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_key = cls.course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course.id, password=cls.password)

        cls.initialize_course(cls.course)

    @classmethod
    def initialize_course(cls, course):
        course.self_paced = True
        cls.store.update_item(course, cls.staff.id)

        section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
        )
        subsection1 = ItemFactory.create(
            parent_location=section.location,
            category="sequential",
        )
        unit1 = ItemFactory.create(
            parent_location=subsection1.location,
            category="vertical",
        )
        ItemFactory.create(
            parent_location=unit1.location,
            category="video",
        )
        ItemFactory.create(
            parent_location=unit1.location,
            category="problem",
        )

        subsection2 = ItemFactory.create(
            parent_location=section.location,
            category="sequential",
        )
        unit2 = ItemFactory.create(
            parent_location=subsection2.location,
            category="vertical",
        )
        unit3 = ItemFactory.create(
            parent_location=subsection2.location,
            category="vertical",
        )
        ItemFactory.create(
            parent_location=unit3.location,
            category="video",
        )
        ItemFactory.create(
            parent_location=unit3.location,
            category="video",
        )

    def get_url(self, course_id):
        """
        Helper function to create the url
        """
        return reverse(
            'courses_api:course_quality',
            kwargs={
                'course_id': course_id
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
            'units': {
                'num_blocks': {
                    'max': 2,
                    'mean': 1.0,
                    'median': 2.0,
                    'mode': 2.0,
                    'min': 0,
                },
                'total_visible': 3,
            },
            'videos': {
                'durations': {
                    'max': None,
                    'mean': None,
                    'median': None,
                    'mode': None,
                    'min': None,
                },
                'num_mobile_encoded': 0,
                'num_with_val_id': 0,
                'total_number': 3,
            },
            'sections': {
                'number_with_highlights': 0,
                'total_visible': 1,
                'total_number': 1,
                'highlights_enabled': False,
                'highlights_active_for_course': False,
            },
            'subsections': {
                'num_with_one_block_type': 1,
                'num_block_types': {
                    'max': 2,
                    'mean': 2.0,
                    'median': 2.0,
                    'mode': 1.0,
                    'min': 1,
                },
                'total_visible': 2,
            },
            'is_self_paced': True,
        }
        self.assertDictEqual(resp.data, expected_data)
