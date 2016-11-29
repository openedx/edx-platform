"""
Test the student dashboard view.
"""
import json
import unittest

import ddt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test import TestCase
from edx_oauth2_provider.constants import AUTHORIZED_CLIENTS_SESSION_KEY
from edx_oauth2_provider.tests.factories import ClientFactory, TrustedClientFactory
from mock import patch
from pyquery import PyQuery as pq
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.cookies import get_user_info_cookie_data
from student.helpers import DISABLE_UNENROLL_CERT_STATES
from student.models import CourseEnrollment, LogoutViewConfiguration
from student.tests.factories import UserFactory, CourseEnrollmentFactory

PASSWORD = 'test'


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardUnenrollments(SharedModuleStoreTestCase):
    """
    Test to ensure that the student dashboard does not show the unenroll button for users with certificates.
    """
    UNENROLL_ELEMENT_ID = "#actions-item-unenroll-0"

    @classmethod
    def setUpClass(cls):
        super(TestStudentDashboardUnenrollments, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """ Create a course and user, then log in. """
        super(TestStudentDashboardUnenrollments, self).setUp()
        self.user = UserFactory()
        CourseEnrollmentFactory(course_id=self.course.id, user=self.user)
        self.cert_status = None
        self.client.login(username=self.user.username, password=PASSWORD)

    def mock_cert(self, _user, _course_overview, _course_mode):
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


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LogoutTests(TestCase):
    """ Tests for the logout functionality. """

    def setUp(self):
        """ Create a course and user, then log in. """
        super(LogoutTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=PASSWORD)
        LogoutViewConfiguration.objects.create(enabled=True)

    def create_oauth_client(self):
        """ Creates a trusted OAuth client. """
        client = ClientFactory(logout_uri='https://www.example.com/logout/')
        TrustedClientFactory(client=client)
        return client

    def assert_session_logged_out(self, oauth_client, **logout_headers):
        """ Authenticates a user via OAuth 2.0, logs out, and verifies the session is logged out. """
        self.authenticate_with_oauth(oauth_client)

        # Logging out should remove the session variables, and send a list of logout URLs to the template.
        # The template will handle loading those URLs and redirecting the user. That functionality is not tested here.
        response = self.client.get(reverse('logout'), **logout_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(AUTHORIZED_CLIENTS_SESSION_KEY, self.client.session)

        return response

    def authenticate_with_oauth(self, oauth_client):
        """ Perform an OAuth authentication using the current web client.

        This should add an AUTHORIZED_CLIENTS_SESSION_KEY entry to the current session.
        """
        data = {
            'client_id': oauth_client.client_id,
            'client_secret': oauth_client.client_secret,
            'response_type': 'code'
        }
        # Authenticate with OAuth to set the appropriate session values
        self.client.post(reverse('oauth2:capture'), data, follow=True)
        self.assertListEqual(self.client.session[AUTHORIZED_CLIENTS_SESSION_KEY], [oauth_client.client_id])

    def assert_logout_redirects(self):
        """ Verify logging out redirects the user to the homepage. """
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_switch(self):
        """ Verify the IDA logout functionality is disabled if the associated switch is disabled. """
        LogoutViewConfiguration.objects.create(enabled=False)
        oauth_client = self.create_oauth_client()
        self.authenticate_with_oauth(oauth_client)
        self.assert_logout_redirects()

    def test_without_session_value(self):
        """ Verify logout works even if the session does not contain an entry with
        the authenticated OpenID Connect clients."""
        self.assert_logout_redirects()

    def test_client_logout(self):
        """ Verify the context includes a list of the logout URIs of the authenticated OpenID Connect clients.

        The list should only include URIs of the clients for which the user has been authenticated.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client)
        expected = {
            'logout_uris': [client.logout_uri + '?no_redirect=1'],  # pylint: disable=no-member
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)  # pylint: disable=no-member

    def test_filter_referring_service(self):
        """ Verify that, if the user is directed to the logout page from a service, that service's logout URL
        is not included in the context sent to the template.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client, HTTP_REFERER=client.logout_uri)  # pylint: disable=no-member
        expected = {
            'logout_uris': [],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)  # pylint: disable=no-member


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class StudentDashboardTests(TestCase):
    """ Tests for the student dashboard. """

    def setUp(self):
        """ Create a course and user, then log in. """
        super(StudentDashboardTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=PASSWORD)
        self.path = reverse('dashboard')

    def test_user_info_cookie(self):
        """ Verify visiting the learner dashboard sets the user info cookie. """
        self.assertNotIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

        request = RequestFactory().get(self.path)
        request.user = self.user
        expected = json.dumps(get_user_info_cookie_data(request))
        self.client.get(self.path)
        actual = self.client.cookies[settings.EDXMKTG_USER_INFO_COOKIE_NAME].value
        self.assertEqual(actual, expected)
