"""
test views
"""
import ddt
from nose.plugins.attrib import attr

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from student.models import (
    CourseEnrollment,
    CourseEnrollmentAllowed,
)
from student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from xmodule.modulestore.tests.factories import CourseFactory
from ccx_keys.locator import CCXLocator
from openedx.core.djangoapps.labster.tests.base import CCXCourseTestBase


def is_email(identifier):
    """
    Checks if an `identifier` string is a valid email
    """
    try:
        validate_email(identifier)
    except ValidationError:
        return False
    return True


@attr('shard_1')
@ddt.ddt
class TestCCXInvite(CCXCourseTestBase):
    """
    Tests for Courses views.
    """
    def setUp(self):
        super(TestCCXInvite, self).setUp()
        admin = UserFactory.create(is_superuser=True, is_staff=True)
        admin.set_password('pass')
        admin.save()
        self.client.login(username=admin.username, password="pass")
        token, created = Token.objects.get_or_create(user=admin)
        self.headers = {'Authorization': 'Token %s' % token}

    def get_outbox(self):
        """
        get fake outbox
        """
        from django.core import mail
        return mail.outbox

    @ddt.data(
        (True, 1, 'enroll'),
        (False, 0, 'enroll'),
    )
    @ddt.unpack
    def test_enroll_member_student(self, send_email, outbox_count, action):
        """
        Tests the enrollment of  a list of students who are members
        of the class.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse('labster_ccx_invite', kwargs={'course_id': str(ccx_course_key)})
        data = {
            'action': action,
            'identifiers': u','.join([student.email, ]),  # pylint: disable=no-member
            'email_students': send_email
        }
        response = self.client.post(url, data=data, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(outbox), outbox_count)
        if send_email:
            self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership exists for this student
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course.id, user=student).exists()
        )

    def test_ccx_invite_enroll_up_to_limit(self):
        """
        Enrolls a list of students up to the enrollment limit.

        This test is specific to one of the enrollment views: the reason is because
        the view used in this test can perform bulk enrollments.
        """
        self.make_coach()
        # create ccx and limit the maximum amount of students that can be enrolled to 2
        ccx = self.make_ccx(max_students_allowed=2)
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        # create some users
        students = [
            UserFactory.create(is_staff=False) for _ in range(3)
        ]
        url = reverse('labster_ccx_invite', kwargs={'course_id': str(ccx_course_key)})
        data = {
            'action': 'enroll',
            'identifiers': u','.join([student.email for student in students]),
        }
        response = self.client.post(url, data=data, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # a CcxMembership exists for the first two students but not the third
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[0]).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[1]).exists()
        )
        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[2]).exists()
        )

    @ddt.data(
        (True, 1, 'unenroll'),
        (False, 0, 'unenroll'),
    )
    @ddt.unpack
    def test_unenroll_member_student(self, send_email, outbox_count, action):
        """
        Tests the unenrollment of a list of students who are members of the class.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=course_key)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse('labster_ccx_invite', kwargs={'course_id': str(course_key)})
        data = {
            'action': action,
            'identifiers': u','.join([student.email, ]),  # pylint: disable=no-member
            'email_students': send_email
        }
        response = self.client.post(url, data=data, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(outbox), outbox_count)
        if send_email:
            self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership does not exists for this student
        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=self.course.id, user=student).exists()
        )

    @ddt.data(
        (True, 1, 'enroll', 'nobody@nowhere.com'),
        (False, 0, 'enroll', 'nobody@nowhere.com'),
        (True, 0, 'enroll', 'nobody'),
        (False, 0, 'enroll', 'nobody'),
    )
    @ddt.unpack
    def test_enroll_non_user_student(self, send_email, outbox_count, action, identifier):
        """
        Tests the enrollment of a list of students who are not users yet.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse('labster_ccx_invite', kwargs={'course_id': str(course_key)})
        data = {
            'action': action,
            'identifiers': u','.join([identifier, ]),
            'email_students': send_email
        }
        response = self.client.post(url, data=data, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(outbox), outbox_count)

        if is_email(identifier):
            if send_email:
                self.assertIn(identifier, outbox[0].recipients())
            self.assertTrue(
                CourseEnrollmentAllowed.objects.filter(course_id=course_key, email=identifier).exists()
            )
        else:
            self.assertFalse(
                CourseEnrollmentAllowed.objects.filter(course_id=course_key, email=identifier).exists()
            )

    @ddt.data(
        (True, 0, 'unenroll', 'nobody@nowhere.com'),
        (False, 0, 'unenroll', 'nobody@nowhere.com'),
        (True, 0, 'unenroll', 'nobody'),
        (False, 0, 'unenroll', 'nobody'),
    )
    @ddt.unpack
    def test_unenroll_non_user_student(self, send_email, outbox_count, action, identifier):
        """
        Unenroll a list of students who are not users yet
        """
        self.make_coach()
        course = CourseFactory.create()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(course.id, ccx.id)
        outbox = self.get_outbox()
        CourseEnrollmentAllowed(course_id=course_key, email=identifier)
        self.assertEqual(outbox, [])

        url = reverse('labster_ccx_invite', kwargs={'course_id': str(course_key)})
        data = {
            'action': action,
            'identifiers': u','.join([identifier, ]),
            'email_students': send_email
        }
        response = self.client.post(url, data=data, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(outbox), outbox_count)
        self.assertFalse(
            CourseEnrollmentAllowed.objects.filter(
                course_id=course_key, email=identifier
            ).exists()
        )
