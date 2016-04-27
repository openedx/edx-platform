"""
Test the student dashboard view.
"""
import ddt
import unittest
from mock import patch
from pyquery import PyQuery as pq

from django.core.urlresolvers import reverse
from django.conf import settings

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from student.helpers import DISABLE_UNENROLL_CERT_STATES
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardUnenrollments(ModuleStoreTestCase):
    """
    Test to ensure that the student dashboard does not show the unenroll button for users with certificates.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"
    UNENROLL_ELEMENT_ID = "#actions-item-unenroll-0"

    def setUp(self):
        """ Create a course and user, then log in. """
        super(TestStudentDashboardUnenrollments, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        CourseEnrollmentFactory(course_id=self.course.id, user=self.user)
        self.cert_status = None
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def mock_cert(self, _user, _course_overview, _course_mode):  # pylint: disable=unused-argument
        """ Return a preset certificate status. """
        if self.cert_status is not None:
            return {
                'status': self.cert_status,
                'can_unenroll': self.cert_status not in DISABLE_UNENROLL_CERT_STATES
            }
        else:
            return {}

    @ddt.data(
        ('notpassing', 1),
        ('restricted', 1),
        ('processing', 1),
        (None, 1),
        ('generating', 0),
        ('ready', 0),
    )
    @ddt.unpack
    def test_unenroll_available(self, cert_status, unenroll_action_count):
        """ Assert that the unenroll action is shown or not based on the cert status."""
        self.cert_status = cert_status

        with patch('student.views.cert_info', side_effect=self.mock_cert):
            response = self.client.get(reverse('dashboard'))

            self.assertEqual(pq(response.content)(self.UNENROLL_ELEMENT_ID).length, unenroll_action_count)

    @ddt.data(
        ('notpassing', 200),
        ('restricted', 200),
        ('processing', 200),
        (None, 200),
        ('generating', 400),
        ('ready', 400),
    )
    @ddt.unpack
    @patch.object(CourseEnrollment, 'unenroll')
    def test_unenroll_request(self, cert_status, status_code, course_enrollment):
        """ Assert that the unenroll method is called or not based on the cert status"""
        self.cert_status = cert_status

        with patch('student.views.cert_info', side_effect=self.mock_cert):
            response = self.client.post(
                reverse('change_enrollment'),
                {'enrollment_action': 'unenroll', 'course_id': self.course.id}
            )

            self.assertEqual(response.status_code, status_code)
            if status_code == 200:
                course_enrollment.assert_called_with(self.user, self.course.id)
            else:
                course_enrollment.assert_not_called()

    def test_no_cert_status(self):
        """ Assert that the dashboard loads when cert_status is None."""
        with patch('student.views.cert_info', return_value=None):
            response = self.client.get(reverse('dashboard'))

            self.assertEqual(response.status_code, 200)

    def test_cant_unenroll_status(self):
        """ Assert that the dashboard loads when cert_status does not allow for unenrollment"""
        with patch('certificates.models.certificate_status_for_student', return_value={'status': 'ready'}):
            response = self.client.get(reverse('dashboard'))

            self.assertEqual(response.status_code, 200)
