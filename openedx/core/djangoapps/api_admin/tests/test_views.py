#pylint: disable=missing-docstring
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig
from openedx.core.djangoapps.api_admin.tests.factories import ApiAccessRequestFactory
from openedx.core.djangoapps.api_admin.tests.utils import VALID_DATA
from student.tests.factories import UserFactory


class ApiAdminTest(TestCase):

    def setUp(self):
        super(ApiAdminTest, self).setUp()
        ApiAccessConfig(enabled=True).save()


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ApiRequestViewTest(ApiAdminTest):

    def setUp(self):
        super(ApiRequestViewTest, self).setUp()
        self.url = reverse('api_admin:api-request')
        password = 'abc123'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)

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
        self.assertRedirects(response, reverse('api_admin:api-status'))

    def _assert_post_success(self, response):
        """
        Assert that a successful POST has been made, that the response
        redirects correctly, and that the correct object has been created.
        """
        self.assertRedirects(response, reverse('api_admin:api-status'))
        api_request = ApiAccessRequest.objects.get(user=self.user)
        self.assertEqual(api_request.status, ApiAccessRequest.PENDING)
        return api_request

    def test_post_valid(self):
        """Verify that a logged-in user can create an API request."""
        self.assertFalse(ApiAccessRequest.objects.all().exists())
        response = self.client.post(self.url, VALID_DATA)
        self._assert_post_success(response)

    def test_post_anonymous(self):
        """Verify that users must be logged in to create an access request."""
        self.client.logout()
        response = self.client.post(self.url, VALID_DATA)

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
class ApiRequestStatusViewTest(ApiAdminTest):

    def setUp(self):
        super(ApiRequestStatusViewTest, self).setUp()
        password = 'abc123'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)
        self.url = reverse('api_admin:api-status')

    def test_get_without_request(self):
        """
        Verify that users who have not yet requested API access are
        redirected to the API request form.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('api_admin:api-request'))

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


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ApiTosViewTest(ApiAdminTest):

    def test_get_api_tos(self):
        """Verify that the terms of service can be read."""
        url = reverse('api_admin:api-tos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Terms of Service', response.content)
