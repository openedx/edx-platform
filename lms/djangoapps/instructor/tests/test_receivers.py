# pylint: disable=E1101
"""
Run these tests @ Devstack:
    paver test_system -s lms --test_id=lms/djangoapps/gradebook/tests.py
"""
from datetime import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config

from util.signals import course_deleted

from student.models import CourseAccessRole

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class InstructorReceiversTests(ModuleStoreTestCase):
    """ Test suite for signal receivers """

    def setUp(self):
        # Create a course to work with
        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2020, 1, 16)
        )
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)

    def test_receiver_on_course_deleted(self):
        """
        Test the workflow
        """
        # Set up the data to be removed
        CourseAccessRole.objects.create(course_id=self.course.id, user=self.user, role='instructor')

        # Emit the signal
        course_deleted.send(sender=None, course_key=self.course.id)

        # Validate that the course references were removed
        self.assertEqual(CourseAccessRole.objects.filter(course_id=self.course.id).count(), 0)
