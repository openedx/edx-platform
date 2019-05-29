"""
Test the create_user command line script
"""

from __future__ import absolute_import

from django.contrib.auth import get_user_model
from django.core.management import call_command
from six import text_type

from openedx.core.djangoapps.course_modes.models import CourseMode
from student.models import CourseEnrollment, UserProfile
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CreateUserMgmtTests(SharedModuleStoreTestCase):
    """
    Test creating users via command line, exercising various options
    """
    def setUp(self):
        super(CreateUserMgmtTests, self).setUp()
        self.course = CourseFactory.create()
        self.user_model = get_user_model()
        self.default_email = 'testuser555@test.edx.org'
        self.default_password = 'b3TT3rPa$$w0rd!'

        # This is the default mode that the create_user commands gives a user enrollment
        self.default_course_mode = CourseMode.HONOR

    def _do_successful_create_and_check(self, **kwargs):
        """
        Performs a create_user that is expected to succeed, passing in kwargs as given
        """

        # Do arg munging to work around required option issues in Django see:
        # https://stackoverflow.com/questions/32036562/call-command-argument-is-required
        email = kwargs.pop('email', self.default_email)
        password = kwargs.pop('password', self.default_password)

        should_be_enrolled = 'course' in kwargs
        should_be_staff = 'staff' in kwargs

        mode = kwargs.get('mode', self.default_course_mode)

        # For right now this method only handles creating users for the default course
        if 'course' in kwargs:
            self.assertEqual(kwargs['course'], text_type(self.course.id))

        self.assertFalse(self.user_model.objects.filter(email=email).exists())

        call_command('create_user',
                     '--email={}'.format(email),
                     '--password={}'.format(password),
                     **kwargs
                     )

        self.assertTrue(self.user_model.objects.filter(email=email).exists())

        user = self.user_model.objects.get(email=email)

        self.assertEqual(user.is_staff, should_be_staff)

        # create_user should activate their registration and set them active on success
        self.assertTrue(user.is_active)

        # Confirm the user is enrolled, or not, as expected
        self.assertEqual(
            CourseEnrollment.objects.filter(
                course__id=self.course.id,
                user__email=email,
                mode=mode).exists(),
            should_be_enrolled
        )

    def test_create_user(self):
        """
        Run create_user with all defaults
        """
        self._do_successful_create_and_check()

    def test_create_user_with_course(self):
        """
        Run create_user with a course and confirm enrollment
        """
        self._do_successful_create_and_check(course=text_type(self.course.id))

    def test_create_user_as_staff(self):
        """
        Test the functionality of creating the user with the staff flag
        """
        self._do_successful_create_and_check(staff=True)

    def test_create_user_with_overrides(self):
        """
        Test the results of passing in overrides for all optional parameters
        """
        params = {
            'mode': CourseMode.AUDIT,
            'username': 'test_username',
            'proper_name': 'test_name',
            'password': 'test_password',
            'email': 'rushfan2112@test.edx.org',
            'course': text_type(self.course.id),
            'staff': True
        }

        self._do_successful_create_and_check(**params)

        user = self.user_model.objects.get(email=params['email'])
        profile = UserProfile.objects.get(user=user)

        # staff, course, and mode are checked in _do_successful_create_and_check
        self.assertEqual(params['username'], user.username)
        self.assertEqual(params['proper_name'], profile.name)
        self.assertEqual(params['email'], user.email)

        # Check that the password was handled correctly and that the user can log in
        self.assertTrue(self.client.login(username=params['username'], password=params['password']))
