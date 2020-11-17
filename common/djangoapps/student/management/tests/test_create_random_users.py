"""
Test the create_random_users command line script
"""


import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from opaque_keys import InvalidKeyError
from six import text_type

from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CreateRandomUserTests(SharedModuleStoreTestCase):
    """
    Test creating random users via command line, with various options
    """
    def setUp(self):
        super(CreateRandomUserTests, self).setUp()
        self.course = CourseFactory.create()
        self.user_model = get_user_model()
        self.num_users_start = len(self.user_model.objects.all())

    def test_create_users(self):
        """
        The command should create users_to_create number of random users
        """
        users_to_create = 5
        call_command('create_random_users', text_type(users_to_create))

        # Verify correct number of users are now in the database
        self.assertEqual(self.num_users_start + users_to_create, len(self.user_model.objects.all()))

    def test_create_users_with_course(self):
        """
        The command should create users_to_create number of random users and add them to self.course
        """
        users_to_create = 3
        call_command('create_random_users', text_type(users_to_create), text_type(self.course.id))

        # Verify correct number of users are now in the database
        self.assertEqual(self.num_users_start + users_to_create, len(self.user_model.objects.all()))

        # Verify that the users are enrolled in our course
        self.assertEqual(len(CourseEnrollment.objects.filter(course__id=self.course.id)), users_to_create)

    def test_create_users_with_bad_course(self):
        """
        The test passes in a bad course id, no users or CourseEnrollments should be created
        """
        users_to_create = 3

        with pytest.raises(InvalidKeyError):
            call_command('create_random_users', text_type(users_to_create), u'invalid_course_id')

        # Verify correct number of users are now in the database
        self.assertEqual(self.num_users_start, len(self.user_model.objects.all()))

        # Verify that the users are enrolled in our course
        self.assertEqual(len(CourseEnrollment.objects.filter(course__id=self.course.id)), 0)
