import json
from datetime import datetime, timedelta, date
from random import randint

import ddt
from django.conf import settings
from django.contrib.auth.models import Permission
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.test import TestCase, Client
from django.test.utils import override_settings

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.subscriptions.api.v1.serializers import UserSubscriptionSerializer
from openedx.features.subscriptions.api.v1.tests.factories import UserSubscriptionFactory
from openedx.features.subscriptions.models import UserSubscription
from student.tests.factories import UserFactory

PASSWORD = 'test'
JSON_CONTENT_TYPE = 'application/json'


class SubscriptionListViewTests(TestCase):
    """
    Tests for SubscriptionsListView.
    """
    path = '{}?{}'.format(reverse_lazy('subscriptions_api:v1:list'), urlencode({'valid': 'true'}))

    def setUp(self):
        super(SubscriptionListViewTests, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.site = SiteFactory()
        self.client = Client(SERVER_NAME=self.site.domain)
        self.client.login(username=self.user.username, password=PASSWORD)

    def test_authentication_required(self):
        """
        Verify only authenticated users can access the view.
        """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 401)

    def test_list(self):
        """
        Verify the view lists the available courses and modes.
        """
        user_subscription = UserSubscriptionFactory(user=self.user, site=self.site)
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)
        actual_data = response.json()[0]
        expected_data = UserSubscriptionSerializer(user_subscription).data
        self.assertEqual(actual_data, expected_data)

@ddt.ddt
class SubscriptionRetrieveUpdateViewTests(TestCase):
    """
    Tests for SubscriptionRetrieveUpdateView.
    """
    def setUp(self):
        super(SubscriptionRetrieveUpdateViewTests, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.user_subscription = UserSubscriptionFactory(user=self.user)
        self.path = reverse('subscriptions_api:v1:retrieve-update', args=[self.user_subscription.subscription_id])
        self.client.login(username=self.user.username, password=PASSWORD)

    @ddt.data('get', 'post', 'put')
    def test_authentication_required(self, method):
        """
        Verify only authenticated users can access the view.
        """
        self.client.logout()
        response = getattr(self.client, method)(self.path)
        self.assertEqual(response.status_code, 401)

    @ddt.data('post', 'put')
    def test_authorization_required(self, method):
        """
        Verify create/edit operations require appropriate permissions.
        """
        response = getattr(self.client, method)(self.path)
        self.assertEqual(response.status_code, 403)

    def test_retrieve(self):
        """
        Verify the view displays info for a given course.
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        actual_data = response.json()
        expected_data = UserSubscriptionSerializer(self.user_subscription).data
        self.assertEqual(actual_data, expected_data)

    def test_retrieve_invalid_user_subscription(self):
        """
        The view should return HTTP 404 when retrieving data for a user subscription that does not exist.
        """
        path = reverse('subscriptions_api:v1:retrieve-update', args=[123])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def assert_can_create_user_subscription(self, **request_kwargs):
        """
        Verify the view supports updating a user subscription.
        """
        subscription_id = randint(10, 20)
        path = reverse('subscriptions_api:v1:retrieve-update', args=[subscription_id])
        expected_data = {
            'subscription_id': subscription_id,
            'expiration_date': str(date.today() + timedelta(days=1)),
            'user': self.user.username,
            'max_allowed_courses': 4,
            'subscription_type': UserSubscription.LIMITED_ACCESS,
        }

        response = self.client.put(path, json.dumps(expected_data), content_type=JSON_CONTENT_TYPE, **request_kwargs)

        expected_data['course_enrollments'] = []
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, expected_data)

    def test_create_with_permissions(self):
        """
        Verify the view supports creating a course as a user with the appropriate permissions.
        """
        permissions = Permission.objects.filter(name__in=('Can add user subscription', 'Can change user subscription'))
        for permission in permissions:
            self.user.user_permissions.add(permission)

        self.assert_can_create_user_subscription()

    @override_settings(EDX_API_KEY='edx')
    def test_create_with_api_key(self):
        """
        Verify the view supports creating a course when authenticated with the API header key.
        """
        self.client.logout()
        self.assert_can_create_user_subscription(HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
