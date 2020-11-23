"""
Base classes or util functions for use in Course Home API tests
"""


import unittest

from datetime import datetime
from django.conf import settings

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.verify_student.models import VerificationDeadline
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class BaseCourseHomeTests(SharedModuleStoreTestCase):
    """
    Base class for Course Home API tests.

    Creates a course to
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = modulestore()
        cls.course = CourseFactory.create(
            start=datetime(2020, 1, 1),
            end=datetime(2028, 1, 1),
            enrollment_start=datetime(2020, 1, 1),
            enrollment_end=datetime(2028, 1, 1),
            emit_signals=True,
            modulestore=cls.store,
        )
        chapter = ItemFactory(parent=cls.course, category='chapter')
        ItemFactory(parent=chapter, category='sequential', display_name='sequence')

        CourseModeFactory(course_id=cls.course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory(
            course_id=cls.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=datetime(2028, 1, 1)
        )
        VerificationDeadline.objects.create(course_key=cls.course.id, deadline=datetime(2028, 1, 1))

        cls.user = UserFactory(
            username='student',
            email='user@example.com',
            password='foo',
            is_staff=False
        )
        CourseOverviewFactory.create(run='1T2020')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.store.delete_course(cls.course.id, cls.user.id)

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username, password='foo')
