"""
Tests for the LTI user management functionality
"""

import string

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.test.client import RequestFactory
from mock import patch, MagicMock
from lti_provider.models import LtiConsumer, LtiUser
import lti_provider.users as users
from student.tests.factories import UserFactory


class UserManagementHelperTest(TestCase):
    """
    Tests for the helper functions in users.py
    """

    def setUp(self):
        super(UserManagementHelperTest, self).setUp()
        self.request = RequestFactory().post('/')
        self.old_user = UserFactory.create()
        self.new_user = UserFactory.create()
        self.new_user.save()
        self.request.user = self.old_user
        self.lti_consumer = LtiConsumer(
            consumer_name='TestConsumer',
            consumer_key='TestKey',
            consumer_secret='TestSecret'
        )
        self.lti_consumer.save()
        self.lti_user = LtiUser(
            lti_user_id='lti_user_id',
            edx_user=self.new_user
        )

    @patch('django.contrib.auth.authenticate', return_value=None)
    def test_permission_denied_for_unknown_user(self, _authenticate_mock):
        with self.assertRaises(PermissionDenied):
            users.switch_user(self.request, self.lti_user, self.lti_consumer)

    @patch('lti_provider.users.login')
    def test_authenticate_called(self, _login_mock):
        with patch('lti_provider.users.authenticate', return_value=self.new_user) as authenticate:
            users.switch_user(self.request, self.lti_user, self.lti_consumer)
            authenticate.assert_called_with(
                username=self.new_user.username,
                lti_user_id=self.lti_user.lti_user_id,
                lti_consumer=self.lti_consumer
            )

    @patch('lti_provider.users.login')
    def test_login_called(self, login_mock):
        with patch('lti_provider.users.authenticate', return_value=self.new_user):
            users.switch_user(self.request, self.lti_user, self.lti_consumer)
            login_mock.assert_called_with(self.request, self.new_user)

    def test_random_username_generator(self):
        for _idx in range(1000):
            username = users.generate_random_edx_username()
            self.assertTrue(len(username) <= 30, 'Username too long')
            # Check that the username contains only allowable characters
            for char in range(len(username)):
                self.assertTrue(
                    username[char] in string.ascii_letters + string.digits,
                    "Username has forbidden character '{}'".format(username[char])
                )


@patch('lti_provider.users.switch_user', autospec=True)
@patch('lti_provider.users.create_lti_user', autospec=True)
class AuthenticateLtiUserTest(TestCase):
    """
    Tests for the authenticate_lti_user function in users.py
    """
    def setUp(self):
        super(AuthenticateLtiUserTest, self).setUp()
        self.lti_consumer = LtiConsumer(
            consumer_name='TestConsumer',
            consumer_key='TestKey',
            consumer_secret='TestSecret'
        )
        self.lti_consumer.save()
        self.lti_user_id = 'lti_user_id'
        self.edx_user_id = 'edx_user_id'
        self.old_user = UserFactory.create()
        self.request = RequestFactory().post('/')
        self.request.user = self.old_user

    def create_lti_user_model(self):
        """
        Generate and save a User and an LTI user model
        """
        edx_user = User(username=self.edx_user_id)
        edx_user.save()
        lti_user = LtiUser(
            lti_consumer=self.lti_consumer,
            lti_user_id=self.lti_user_id,
            edx_user=edx_user
        )
        lti_user.save()
        return lti_user

    def test_authentication_with_new_user(self, _create_user, switch_user):
        lti_user = MagicMock()
        lti_user.edx_user_id = self.edx_user_id
        with patch('lti_provider.users.create_lti_user', return_value=lti_user) as create_user:
            users.authenticate_lti_user(self.request, self.lti_user_id, self.lti_consumer)
            create_user.assert_called_with(self.lti_user_id, self.lti_consumer)
            switch_user.assert_called_with(self.request, lti_user, self.lti_consumer)

    def test_authentication_with_authenticated_user(self, create_user, switch_user):
        lti_user = self.create_lti_user_model()
        self.request.user = lti_user.edx_user
        self.request.user.is_authenticated = MagicMock(return_value=True)
        users.authenticate_lti_user(self.request, self.lti_user_id, self.lti_consumer)
        self.assertFalse(create_user.called)
        self.assertFalse(switch_user.called)

    def test_authentication_with_unauthenticated_user(self, create_user, switch_user):
        lti_user = self.create_lti_user_model()
        self.request.user = lti_user.edx_user
        self.request.user.is_authenticated = MagicMock(return_value=False)
        users.authenticate_lti_user(self.request, self.lti_user_id, self.lti_consumer)
        self.assertFalse(create_user.called)
        switch_user.assert_called_with(self.request, lti_user, self.lti_consumer)

    def test_authentication_with_wrong_user(self, create_user, switch_user):
        lti_user = self.create_lti_user_model()
        self.request.user = self.old_user
        self.request.user.is_authenticated = MagicMock(return_value=True)
        users.authenticate_lti_user(self.request, self.lti_user_id, self.lti_consumer)
        self.assertFalse(create_user.called)
        switch_user.assert_called_with(self.request, lti_user, self.lti_consumer)


class CreateLtiUserTest(TestCase):
    """
    Tests for the create_lti_user function in users.py
    """

    def setUp(self):
        super(CreateLtiUserTest, self).setUp()
        self.lti_consumer = LtiConsumer(
            consumer_name='TestConsumer',
            consumer_key='TestKey',
            consumer_secret='TestSecret'
        )
        self.lti_consumer.save()

    def test_create_lti_user_creates_auth_user_model(self):
        users.create_lti_user('lti_user_id', self.lti_consumer)
        self.assertEqual(User.objects.count(), 1)

    @patch('uuid.uuid4', return_value='random_uuid')
    @patch('lti_provider.users.generate_random_edx_username', return_value='edx_id')
    def test_create_lti_user_creates_correct_user(self, uuid_mock, _username_mock):
        users.create_lti_user('lti_user_id', self.lti_consumer)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='edx_id')
        self.assertEqual(user.email, 'edx_id@lti.example.com')
        uuid_mock.assert_called_with()

    @patch('lti_provider.users.generate_random_edx_username', side_effect=['edx_id', 'new_edx_id'])
    def test_unique_username_created(self, username_mock):
        User(username='edx_id').save()
        users.create_lti_user('lti_user_id', self.lti_consumer)
        self.assertEqual(username_mock.call_count, 2)
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(username='new_edx_id')
        self.assertEqual(user.email, 'new_edx_id@lti.example.com')


class LtiBackendTest(TestCase):
    """
    Tests for the authentication backend that authenticates LTI users.
    """

    def setUp(self):
        super(LtiBackendTest, self).setUp()
        self.edx_user = UserFactory.create()
        self.edx_user.save()
        self.lti_consumer = LtiConsumer(
            consumer_key="Consumer Key",
            consumer_secret="Consumer Secret"
        )
        self.lti_consumer.save()
        self.lti_user_id = 'LTI User ID'
        LtiUser(
            lti_consumer=self.lti_consumer,
            lti_user_id=self.lti_user_id,
            edx_user=self.edx_user
        ).save()

    def test_valid_user_authenticates(self):
        user = users.LtiBackend().authenticate(
            username=self.edx_user.username,
            lti_user_id=self.lti_user_id,
            lti_consumer=self.lti_consumer
        )
        self.assertEqual(user, self.edx_user)

    def test_missing_user_returns_none(self):
        user = users.LtiBackend().authenticate(
            username=self.edx_user.username,
            lti_user_id='Invalid Username',
            lti_consumer=self.lti_consumer
        )
        self.assertIsNone(user)

    def test_non_lti_user_returns_none(self):
        non_edx_user = UserFactory.create()
        non_edx_user.save()
        user = users.LtiBackend().authenticate(
            username=non_edx_user.username,
        )
        self.assertIsNone(user)

    def test_missing_lti_id_returns_null(self):
        user = users.LtiBackend().authenticate(
            username=self.edx_user.username,
            lti_consumer=self.lti_consumer
        )
        self.assertIsNone(user)

    def test_missing_lti_consumer_returns_null(self):
        user = users.LtiBackend().authenticate(
            username=self.edx_user.username,
            lti_user_id=self.lti_user_id,
        )
        self.assertIsNone(user)

    def test_existing_user_returned_by_get_user(self):
        user = users.LtiBackend().get_user(self.edx_user.id)
        self.assertEqual(user, self.edx_user)

    def test_get_user_returns_none_for_invalid_user(self):
        user = users.LtiBackend().get_user(-1)
        self.assertIsNone(user)
