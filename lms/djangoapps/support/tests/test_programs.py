# pylint: disable=missing-docstring
from django.core.urlresolvers import reverse
from django.test import TestCase
import mock
from edx_oauth2_provider.tests.factories import AccessTokenFactory, ClientFactory

from student.tests.factories import UserFactory


class IssueProgramCertificatesViewTests(TestCase):
    password = 'password'

    def setUp(self):
        super(IssueProgramCertificatesViewTests, self).setUp()

        self.path = reverse('support:programs-certify')
        self.user = UserFactory(password=self.password, is_staff=True)
        self.data = {'username': self.user.username}
        self.headers = {}

        self.client.login(username=self.user.username, password=self.password)

    def _verify_response(self, status_code):
        """Verify that the endpoint returns the provided status code and enqueues the task if appropriate."""
        with mock.patch('lms.djangoapps.support.views.programs.award_program_certificates.delay') as mock_task:
            response = self.client.post(self.path, self.data, **self.headers)

        self.assertEqual(response.status_code, status_code)
        self.assertEqual(status_code == 200, mock_task.called)

    def test_authentication_required(self):
        """Verify that the endpoint requires authentication."""
        self.client.logout()

        self._verify_response(403)

    def test_session_auth(self):
        """Verify that the endpoint supports session auth."""
        self._verify_response(200)

    def test_oauth(self):
        """Verify that the endpoint supports OAuth 2.0."""
        access_token = AccessTokenFactory(user=self.user, client=ClientFactory()).token  # pylint: disable=no-member
        self.headers['HTTP_AUTHORIZATION'] = 'Bearer ' + access_token

        self.client.logout()

        self._verify_response(200)

    def test_staff_permissions_required(self):
        """Verify that staff permissions are required to access the endpoint."""
        self.user.is_staff = False
        self.user.save()  # pylint: disable=no-member

        self._verify_response(403)

    def test_username_required(self):
        """Verify that the endpoint returns a 400 when a username isn't provided."""
        self.data.pop('username')

        self._verify_response(400)
