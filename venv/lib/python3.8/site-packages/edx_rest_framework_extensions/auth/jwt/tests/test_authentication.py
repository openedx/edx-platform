""" Tests for JWT authentication class. """
from logging import Logger
from unittest import mock

import ddt
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from edx_rest_framework_extensions.auth.jwt import authentication
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.jwt.constants import USE_JWT_COOKIE_HEADER
from edx_rest_framework_extensions.auth.jwt.decoder import jwt_decode_handler
from edx_rest_framework_extensions.auth.jwt.tests.utils import (
    generate_jwt_token,
    generate_latest_version_payload,
)
from edx_rest_framework_extensions.tests import factories


User = get_user_model()


@ddt.ddt
class JwtAuthenticationTests(TestCase):
    """ JWT Authentication class tests. """

    def get_jwt_payload(self, **additional_claims):
        """ Returns a JWT payload with the necessary claims to create a new user. """
        email = 'gcostanza@gmail.com'
        username = 'gcostanza'
        payload = dict({'preferred_username': username, 'email': email}, **additional_claims)

        return payload

    @ddt.data(True, False)
    def test_authenticate_credentials_user_creation(self, is_staff):
        """ Test whether the user model is being created and assigned fields from the payload. """

        payload = self.get_jwt_payload(administrator=is_staff)
        user = JwtAuthentication().authenticate_credentials(payload)
        self.assertEqual(user.username, payload['preferred_username'])
        self.assertEqual(user.email, payload['email'])
        self.assertEqual(user.is_staff, is_staff)

    def test_authenticate_credentials_user_updates_default_attributes(self):
        """ Test whether the user model is being assigned default fields from the payload. """

        username = 'gcostanza'
        old_email = 'tbone@gmail.com'
        new_email = 'koko@gmail.com'

        user = factories.UserFactory(email=old_email, username=username, is_staff=False)
        self.assertEqual(user.email, old_email)
        self.assertFalse(user.is_staff)

        payload = {'username': username, 'email': new_email, 'is_staff': True}

        user = JwtAuthentication().authenticate_credentials(payload)
        self.assertEqual(user.email, new_email)
        self.assertFalse(user.is_staff)

    @override_settings(
        EDX_DRF_EXTENSIONS={'JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING': {'email': 'email', 'is_staff': 'is_staff'}}
    )
    def test_authenticate_credentials_user_attributes_custom_attributes(self):
        """ Test whether the user model is being assigned all custom fields from the payload. """

        username = 'ckramer'
        old_email = 'ckramer@hotmail.com'
        new_email = 'cosmo@hotmail.com'

        user = factories.UserFactory(email=old_email, username=username, is_staff=False)
        self.assertEqual(user.email, old_email)
        self.assertFalse(user.is_staff)

        payload = {'username': username, 'email': new_email, 'is_staff': True}

        user = JwtAuthentication().authenticate_credentials(payload)
        self.assertEqual(user.email, new_email)
        self.assertTrue(user.is_staff)

    @override_settings(
        EDX_DRF_EXTENSIONS={
            'JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING': {
                'email': 'email',
                'is_staff': 'is_staff',
                'tags': 'tags',
                'fun_attr': 'fun_attr',
                'fruit': 'fruit'
            },
            'JWT_PAYLOAD_MERGEABLE_USER_ATTRIBUTES': [
                'tags',
                'fun_attr',
                'fruit'
            ]
        }
    )
    def test_authenticate_credentials_user_attributes_merge_attributes(self):
        """ Test whether the user model is being assigned all custom fields from the payload. """

        username = 'ckramer'
        email = 'ckramer@hotmail.com'
        old_tags = {'country': 'USA', 'browser': 'Firefox'}
        new_tags = {'browser': 'Chrome', 'new_attr': 'here!'}
        new_fun_attr = {'shiny': 'object'}
        expected_tags = {'country': 'USA', 'browser': 'Chrome', 'new_attr': 'here!'}
        old_fruit = {'fruit': 'apple'}

        user = factories.UserFactory(email=email, username=username, is_staff=False)
        setattr(user, 'tags', old_tags)
        setattr(user, 'fruit', old_fruit)
        self.assertEqual(user.email, email)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.tags, old_tags)
        self.assertEqual(user.fruit, old_fruit)  # pylint: disable=no-member

        payload = {'username': username, 'email': email, 'is_staff': True, 'tags': new_tags, 'fun_attr': new_fun_attr}

        # Patch get_or_create so that our tags attribute is on the user object
        with mock.patch('edx_rest_framework_extensions.auth.jwt.authentication.get_user_model') as mock_get_user_model:
            mock_get_user_model().objects.get_or_create.return_value = (user, False)

            user = JwtAuthentication().authenticate_credentials(payload)
        self.assertEqual(user.tags, expected_tags)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.fun_attr, new_fun_attr)
        self.assertEqual(user.fruit, old_fruit)

    @override_settings(
        EDX_DRF_EXTENSIONS={
            'JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING': {'email': 'email', 'is_staff': 'is_staff', 'tags': 'tags'},
            'JWT_PAYLOAD_MERGEABLE_USER_ATTRIBUTES': ['tags']
        }
    )
    def test_authenticate_credentials_user_attributes_new_mergeable_attributes(self):
        """ Test whether the user model is being assigned all custom fields from the payload. """

        username = 'ckramer'
        email = 'ckramer@hotmail.com'
        new_tags = {'browser': 'Chrome'}

        user = factories.UserFactory(email=email, username=username, is_staff=False)
        self.assertEqual(user.email, email)
        self.assertFalse(user.is_staff)

        payload = {'username': username, 'email': email, 'is_staff': True, 'tags': new_tags}

        # Patch get_or_create so that our tags attribute is on the user object
        with mock.patch('edx_rest_framework_extensions.auth.jwt.authentication.get_user_model') as mock_get_user_model:
            mock_get_user_model().objects.get_or_create.return_value = (user, False)

            user = JwtAuthentication().authenticate_credentials(payload)
        self.assertEqual(user.tags, new_tags)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_staff)

    def test_authenticate_credentials_user_retrieval_failed(self):
        """ Verify exceptions raised during user retrieval are properly logged. """

        with mock.patch.object(User.objects, 'get_or_create', side_effect=ValueError):
            with mock.patch.object(Logger, 'exception') as logger:
                self.assertRaises(
                    AuthenticationFailed,
                    JwtAuthentication().authenticate_credentials,
                    {'username': 'test', 'email': 'test@example.com'}
                )
                logger.assert_called_with('User retrieval failed.')

    def test_authenticate_credentials_no_usernames(self):
        """ Verify an AuthenticationFailed exception is raised if the payload contains no username claim. """
        with self.assertRaises(AuthenticationFailed):
            JwtAuthentication().authenticate_credentials({'email': 'test@example.com'})

    @mock.patch('edx_rest_framework_extensions.auth.jwt.authentication.set_custom_attribute')
    def test_authenticate_csrf_protected(self, mock_set_custom_attribute):
        """ Verify authenticate exception for CSRF protected cases. """
        request = RequestFactory().post('/')

        request.META[USE_JWT_COOKIE_HEADER] = 'true'

        with mock.patch.object(JSONWebTokenAuthentication, 'authenticate', return_value=('mock-user', "mock-auth")):
            with self.assertRaises(PermissionDenied) as context_manager:
                JwtAuthentication().authenticate(request)

        assert context_manager.exception.detail.startswith('CSRF Failed')
        mock_set_custom_attribute.assert_called_once_with(
            'jwt_auth_failed',
            "Exception:PermissionDenied('CSRF Failed: CSRF cookie not set.')",
        )

    @ddt.data(True, False)
    def test_get_decoded_jwt_from_auth(self, is_jwt_authentication):
        """ Verify get_decoded_jwt_from_auth returns the appropriate value. """

        # Mock out the `is_jwt_authenticated` method
        authentication.is_jwt_authenticated = lambda request: is_jwt_authentication

        jwt_token = self._get_test_jwt_token()
        mock_request_with_cookie = mock.Mock(COOKIES={}, auth=jwt_token)

        expected_decoded_jwt = jwt_decode_handler(jwt_token) if is_jwt_authentication else None

        decoded_jwt = authentication.get_decoded_jwt_from_auth(mock_request_with_cookie)
        self.assertEqual(expected_decoded_jwt, decoded_jwt)

    def test_authenticate_with_correct_jwt_authorization(self):
        """
        With JWT header it continues and validates the credentials and throws error.

        Note: CSRF protection should be skipped for this case, with no PermissionDenied.
        """
        jwt_token = self._get_test_jwt_token()
        request = RequestFactory().get('/', HTTP_AUTHORIZATION=jwt_token)
        JwtAuthentication().authenticate(request)

    def test_authenticate_with_incorrect_jwt_authorization(self):
        """ With JWT header it continues and validates the credentials and throws error. """
        auth_header = '{token_name} {token}'.format(token_name='JWT', token='wrongvalue')
        request = RequestFactory().get('/', HTTP_AUTHORIZATION=auth_header)
        with self.assertRaises(AuthenticationFailed):
            JwtAuthentication().authenticate(request)

    def test_authenticate_with_bearer_token(self):
        """ Returns a None for bearer header request. """
        auth_header = '{token_name} {token}'.format(token_name='Bearer', token='abc123')
        request = RequestFactory().get('/', HTTP_AUTHORIZATION=auth_header)
        self.assertIsNone(JwtAuthentication().authenticate(request))

    def _get_test_jwt_token(self):
        """ Returns a user and jwt token """
        user = factories.UserFactory()
        payload = generate_latest_version_payload(user)
        jwt_token = generate_jwt_token(payload)
        return jwt_token
