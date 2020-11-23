"""
Test cases to cover Accounts-related serializers of the User API application
"""


import logging

from django.test import TestCase
from django.test.client import RequestFactory
from testfixtures import LogCapture

from openedx.core.djangoapps.user_api.accounts.serializers import UserReadOnlySerializer
from common.djangoapps.student.models import UserProfile
from common.djangoapps.student.tests.factories import UserFactory

LOGGER_NAME = "openedx.core.djangoapps.user_api.accounts.serializers"


class UserReadOnlySerializerTest(TestCase):
    def setUp(self):
        super(UserReadOnlySerializerTest, self).setUp()
        request_factory = RequestFactory()
        self.request = request_factory.get('/api/user/v1/accounts/')
        self.user = UserFactory.build(username='test_user', email='test_user@test.com')
        self.user.save()
        self.config = {
            "default_visibility": "public",
            "public_fields": [
                'email', 'name', 'username'
            ],
        }

    def test_serializer_data(self):
        """
        Test serializer return data properly.
        """
        UserProfile.objects.create(user=self.user, name='test name')
        data = UserReadOnlySerializer(self.user, configuration=self.config, context={'request': self.request}).data
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['name'], 'test name')
        self.assertEqual(data['email'], self.user.email)

    def test_user_no_profile(self):
        """
        Test serializer return data properly when user does not have profile.
        """
        with LogCapture(LOGGER_NAME, level=logging.DEBUG) as logger:
            data = UserReadOnlySerializer(self.user, configuration=self.config, context={'request': self.request}).data
            logger.check(
                (LOGGER_NAME, 'WARNING', 'user profile for the user [test_user] does not exist')
            )

        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['name'], None)
