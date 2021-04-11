"""
Base test case for the course API views.
"""


from django.urls import reverse
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import StaffFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


# pylint: disable=unused-variable
class BaseCourseViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Base test class for course data views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    view_name = None  # The name of the view to use in reverse() call in self.get_url()

    @classmethod
    def setUpClass(cls):
        super(BaseCourseViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_key = cls.course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course.id, password=cls.password)

        cls.initialize_course(cls.course)

    @classmethod
    def initialize_course(cls, course):
        """
        Sets up the structure of the test course.
        """
        course.self_paced = True
        cls.store.update_item(course, cls.staff.id)

        cls.section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
        )
        cls.subsection1 = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
        )
        unit1 = ItemFactory.create(
            parent_location=cls.subsection1.location,
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

        cls.subsection2 = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
        )
        unit2 = ItemFactory.create(
            parent_location=cls.subsection2.location,
            category="vertical",
        )
        unit3 = ItemFactory.create(
            parent_location=cls.subsection2.location,
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
            self.view_name,
            kwargs={
                'course_id': course_id
            }
        )
