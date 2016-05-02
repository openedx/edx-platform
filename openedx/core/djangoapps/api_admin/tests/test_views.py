#pylint: disable=missing-docstring
from smtplib import SMTPException
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
import mock

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig
from openedx.core.djangoapps.api_admin.tests.factories import ApiAccessRequestFactory
from openedx.core.djangoapps.api_admin.tests.utils import VALID_DATA
from openedx.core.djangoapps.api_admin.views import log as view_log
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ApiRequestViewTest(TestCase):

    def setUp(self):
        super(ApiRequestViewTest, self).setUp()
        self.url = reverse('api-request')
        password = 'abc123'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)
        ApiAccessConfig(enabled=True).save()

    def test_get(self):
        """Verify that a logged-in can see the API request form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        """Verify that users must be logged in to see the page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_with_existing_request(self):
        """
        Verify that users who have already requested access are redirected
        to the client creation page to see their status.
        """
        ApiAccessRequestFactory(user=self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('api-status'))

    def _assert_post_success(self, response):
        """
        Assert that a successful POST has been made, that the response
        redirects correctly, and that the correct object has been created.
        """
        self.assertRedirects(response, reverse('api-status'))
        api_request = ApiAccessRequest.objects.get(user=self.user)
        self.assertEqual(api_request.status, ApiAccessRequest.PENDING)
        return api_request

    def test_post_valid(self):
        """Verify that a logged-in user can create an API request."""
        self.assertFalse(ApiAccessRequest.objects.all().exists())
        with mock.patch('openedx.core.djangoapps.api_admin.views.send_mail') as mock_send_mail:
            response = self.client.post(self.url, VALID_DATA)
        mock_send_mail.assert_called_once_with(
            'API access request from ' + VALID_DATA['company_name'],
            mock.ANY,
            settings.API_ACCESS_FROM_EMAIL,
            [settings.API_ACCESS_MANAGER_EMAIL],
            fail_silently=False
        )
        self._assert_post_success(response)

    def test_failed_email(self):
        """
        Verify that an access request is still created if sending email
        fails for some reason, and that the necessary information is
        logged.
        """
        mail_function = 'openedx.core.djangoapps.api_admin.views.send_mail'
        with mock.patch(mail_function, side_effect=SMTPException):
            with mock.patch.object(view_log, 'exception') as mock_view_log_exception:
                response = self.client.post(self.url, VALID_DATA)
        api_request = self._assert_post_success(response)
        mock_view_log_exception.assert_called_once_with(
            'Error sending API request email for request [%s].', api_request.id  # pylint: disable=no-member
        )

    def test_post_anonymous(self):
        """Verify that users must be logged in to create an access request."""
        self.client.logout()
        with mock.patch('openedx.core.djangoapps.api_admin.views.send_mail') as mock_send_mail:
            response = self.client.post(self.url, VALID_DATA)
        mock_send_mail.assert_not_called()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ApiAccessRequest.objects.all().exists())

    def test_get_with_feature_disabled(self):
        """Verify that the view can be disabled via ApiAccessConfig."""
        ApiAccessConfig(enabled=False).save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_with_feature_disabled(self):
        """Verify that the view can be disabled via ApiAccessConfig."""
        ApiAccessConfig(enabled=False).save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ApiRequestStatusViewTest(TestCase):

    def setUp(self):
        super(ApiRequestStatusViewTest, self).setUp()
        ApiAccessConfig(enabled=True).save()
        password = 'abc123'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)
        self.url = reverse('api-status')

    def test_get_without_request(self):
        """
        Verify that users who have not yet requested API access are
        redirected to the API request form.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('api-request'))

    def test_get_with_request(self):
        """
        Verify that users who have requested access can see a message
        regarding their request status.
        """
        ApiAccessRequestFactory(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        """Verify that users must be logged in to see the page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_with_feature_disabled(self):
        """Verify that the view can be disabled via ApiAccessConfig."""
        ApiAccessConfig(enabled=False).save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
