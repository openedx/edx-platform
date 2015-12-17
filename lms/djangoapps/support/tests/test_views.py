# coding: UTF-8
"""
Tests for support views.
"""

from datetime import datetime, timedelta
import itertools
import json
import re

import ddt
from django.test import TestCase
from django.core.urlresolvers import reverse
from pytz import UTC

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.verify_student.models import VerificationDeadline
from student.models import CourseEnrollment, ManualEnrollmentAudit, ENROLLED_TO_ENROLLED
from student.roles import GlobalStaff, SupportStaffRole
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class SupportViewTestCase(TestCase):
    """
    Base class for support view tests.
    """

    USERNAME = "support"
    EMAIL = "support@example.com"
    PASSWORD = "support"

    def setUp(self):
        """Create a user and log in. """
        super(SupportViewTestCase, self).setUp()
        self.user = UserFactory(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")


@ddt.ddt
class SupportViewAccessTests(SupportViewTestCase):
    """
    Tests for access control of support views.
    """

    @ddt.data(*(
        (url_name, role, has_access)
        for (url_name, (role, has_access))
        in itertools.product((
            'support:index',
            'support:certificates',
            'support:refund',
            'support:enrollment',
            'support:enrollment_list'
        ), (
            (GlobalStaff, True),
            (SupportStaffRole, True),
            (None, False)
        ))
    ))
    @ddt.unpack
    def test_access(self, url_name, role, has_access):
        if role is not None:
            role().add_users(self.user)

        url = reverse(url_name)
        response = self.client.get(url)

        if has_access:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 403)

    @ddt.data(
        "support:index",
        "support:certificates",
        "support:refund",
        "support:enrollment",
        "support:enrollment_list"
    )
    def test_require_login(self, url_name):
        url = reverse(url_name)

        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = "{login_url}?next={original_url}".format(
            login_url=reverse("signin_user"),
            original_url=url,
        )
        self.assertRedirects(response, redirect_url)


class SupportViewIndexTests(SupportViewTestCase):
    """
    Tests for the support index view.
    """

    EXPECTED_URL_NAMES = [
        "support:certificates",
        "support:refund",
    ]

    def setUp(self):
        """Make the user support staff. """
        super(SupportViewIndexTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_index(self):
        response = self.client.get(reverse("support:index"))
        self.assertContains(response, "Support")

        # Check that all the expected links appear on the index page.
        for url_name in self.EXPECTED_URL_NAMES:
            self.assertContains(response, reverse(url_name))


class SupportViewCertificatesTests(SupportViewTestCase):
    """
    Tests for the certificates support view.
    """
    def setUp(self):
        """Make the user support staff. """
        super(SupportViewCertificatesTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_certificates_no_query(self):
        # Check that an empty initial query is passed to the JavaScript client correctly.
        response = self.client.get(reverse("support:certificates"))
        self.assertContains(response, "userQuery: ''")

    def test_certificates_with_query(self):
        # Check that an initial query is passed to the JavaScript client.
        url = reverse("support:certificates") + "?query=student@example.com"
        response = self.client.get(url)
        self.assertContains(response, "userQuery: 'student@example.com'")


@ddt.ddt
class SupportViewEnrollmentsTests(SharedModuleStoreTestCase, SupportViewTestCase):
    """Tests for the enrollment support view."""

    def setUp(self):
        super(SupportViewEnrollmentsTests, self).setUp()
        SupportStaffRole().add_users(self.user)

        self.course = CourseFactory(display_name=u'teꜱᴛ')
        self.student = UserFactory.create(username='student', email='test@example.com', password='test')

        for mode in (CourseMode.AUDIT, CourseMode.VERIFIED):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)  # pylint: disable=no-member

        self.verification_deadline = VerificationDeadline(
            course_key=self.course.id,  # pylint: disable=no-member
            deadline=datetime.now(UTC) + timedelta(days=365)
        )
        self.verification_deadline.save()

        CourseEnrollmentFactory.create(mode=CourseMode.AUDIT, user=self.student, course_id=self.course.id)  # pylint: disable=no-member

        self.url = reverse('support:enrollment_list', kwargs={'username': self.student.username})

    def assert_enrollment(self, mode):
        """
        Assert that the student's enrollment has the correct mode.
        """
        enrollment = CourseEnrollment.get_enrollment(self.student, self.course.id)  # pylint: disable=no-member
        self.assertEqual(enrollment.mode, mode)

    def test_get_enrollments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'mode': CourseMode.AUDIT,
            'manual_enrollment': {},
            'user': self.student.username,
            'course_id': unicode(self.course.id),  # pylint: disable=no-member
            'is_active': True,
            'verified_upgrade_deadline': None,
        }, data[0])
        self.assertEqual(
            {CourseMode.VERIFIED, CourseMode.AUDIT},
            {mode['slug'] for mode in data[0]['course_modes']}
        )

    def test_get_manual_enrollment_history(self):
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.user,
            self.student.email,
            ENROLLED_TO_ENROLLED,
            'Financial Assistance',
            CourseEnrollment.objects.get(course_id=self.course.id, user=self.student)  # pylint: disable=no-member
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({
            'enrolled_by': self.user.email,
            'reason': 'Financial Assistance',
        }, json.loads(response.content)[0]['manual_enrollment'])

    def test_change_enrollment(self):
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        response = self.client.post(self.url, data={
            'course_id': unicode(self.course.id),  # pylint: disable=no-member
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.VERIFIED,
            'reason': 'Financial Assistance'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        self.assert_enrollment(CourseMode.VERIFIED)

    @ddt.data(
        ({}, r"The field '\w+' is required."),
        ({'course_id': 'bad course key'}, 'Could not parse course key.'),
        ({
            'course_id': 'course-v1:TestX+T101+2015',
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.VERIFIED,
            'reason': ''
        }, 'Could not find enrollment for user'),
        ({
            'course_id': None,
            'old_mode': CourseMode.HONOR,
            'new_mode': CourseMode.VERIFIED,
            'reason': ''
        }, r'User \w+ is not enrolled with mode ' + CourseMode.HONOR),
        ({
            'course_id': None,
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.CREDIT_MODE,
            'reason': ''
        }, "Specified course mode '{}' unavailable".format(CourseMode.CREDIT_MODE))
    )
    @ddt.unpack
    def test_change_enrollment_bad_data(self, data, error_message):
        # `self` isn't available from within the DDT declaration, so
        # assign the course ID here
        if 'course_id' in data and data['course_id'] is None:
            data['course_id'] = unicode(self.course.id)  # pylint: disable=no-member
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(re.match(error_message, response.content))
        self.assert_enrollment(CourseMode.AUDIT)
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
