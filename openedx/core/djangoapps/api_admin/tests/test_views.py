#pylint: disable=missing-docstring
import unittest

import ddt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from oauth2_provider.models import get_application_model

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig
from openedx.core.djangoapps.api_admin.tests.factories import ApiAccessRequestFactory, ApplicationFactory
from openedx.core.djangoapps.api_admin.tests.utils import VALID_DATA
from student.tests.factories import UserFactory


Application = get_application_model()  # pylint: disable=invalid-name


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
@override_settings(PLATFORM_NAME='edX')
@ddt.ddt
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

    @ddt.data(
        (ApiAccessRequest.APPROVED, 'Your request to access the edX Course Catalog API has been approved.'),
        (ApiAccessRequest.PENDING, 'Your request to access the edX Course Catalog API is being processed.'),
        (ApiAccessRequest.DENIED, 'Your request to access the edX Course Catalog API has been denied.'),
    )
    @ddt.unpack
    def test_get_with_request(self, status, expected):
        """
        Verify that users who have requested access can see a message
        regarding their request status.
        """
        ApiAccessRequestFactory(user=self.user, status=status)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(expected, response.content)

    def test_get_with_existing_application(self):
        """
        Verify that if the user has created their client credentials, they
        are shown on the status page.
        """
        ApiAccessRequestFactory(user=self.user, status=ApiAccessRequest.APPROVED)
        application = ApplicationFactory(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        unicode_content = response.content.decode('utf-8')
        self.assertIn(application.client_secret, unicode_content)  # pylint: disable=no-member
        self.assertIn(application.client_id, unicode_content)  # pylint: disable=no-member
        self.assertIn(application.redirect_uris, unicode_content)  # pylint: disable=no-member

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

    @ddt.data(
        (ApiAccessRequest.APPROVED, True, True),
        (ApiAccessRequest.DENIED, True, False),
        (ApiAccessRequest.PENDING, True, False),
        (ApiAccessRequest.APPROVED, False, True),
        (ApiAccessRequest.DENIED, False, False),
        (ApiAccessRequest.PENDING, False, False),
    )
    @ddt.unpack
    def test_post(self, status, application_exists, new_application_created):
        """
        Verify that posting the form creates an application if the user is
        approved, and does not otherwise. Also ensure that if the user
        already has an application, it is deleted before a new
        application is created.
        """
        if application_exists:
            old_application = ApplicationFactory(user=self.user)
        ApiAccessRequestFactory(user=self.user, status=status)
        self.client.post(self.url, {
            'name': 'test.com',
            'redirect_uris': 'http://example.com'
        })
        applications = Application.objects.filter(user=self.user)
        if application_exists and new_application_created:
            self.assertEqual(applications.count(), 1)
            self.assertNotEqual(old_application, applications[0])
        elif application_exists:
            self.assertEqual(applications.count(), 1)
            self.assertEqual(old_application, applications[0])
        elif new_application_created:
            self.assertEqual(applications.count(), 1)
        else:
            self.assertEqual(applications.count(), 0)

    def test_post_with_errors(self):
        ApiAccessRequestFactory(user=self.user, status=ApiAccessRequest.APPROVED)
        response = self.client.post(self.url, {
            'name': 'test.com',
            'redirect_uris': 'not a url'
        })
        self.assertIn('Enter a valid URL.', response.content)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ApiTosViewTest(ApiAdminTest):

    def test_get_api_tos(self):
        """Verify that the terms of service can be read."""
        url = reverse('api_admin:api-tos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Terms of Service', response.content)
