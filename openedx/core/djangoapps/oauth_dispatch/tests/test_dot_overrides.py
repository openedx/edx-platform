"""
Test of custom django-oauth-toolkit behavior
"""

# pylint: disable=protected-access


import datetime
import unittest

from django.conf import settings
from django.test import RequestFactory, TestCase
from django.utils import timezone

from common.djangoapps.student.tests.factories import UserFactory

# oauth_dispatch is not in CMS' INSTALLED_APPS so these imports will error during test collection
if settings.ROOT_URLCONF == 'lms.urls':
    from oauth2_provider import models as dot_models

    from .. import adapters
    from .. import models
    from ..dot_overrides.validators import EdxOAuth2Validator
    from .constants import DUMMY_REDIRECT_URL


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class AuthenticateTestCase(TestCase):
    """
    Test that users can authenticate with either username or email
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            username='darkhelmet',
            password='12345',
            email='darkhelmet@spaceball_one.org',
        )
        self.validator = EdxOAuth2Validator()

    def test_authenticate_with_username(self):
        user = self.validator._authenticate(username='darkhelmet', password='12345')
        assert self.user == user

    def test_authenticate_with_email(self):
        user = self.validator._authenticate(username='darkhelmet@spaceball_one.org', password='12345')
        assert self.user == user


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CustomValidationTestCase(TestCase):
    """
    Test custom user validation works.

    In particular, inactive users should be able to validate.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            username='darkhelmet',
            password='12345',
            email='darkhelmet@spaceball_one.org',
        )
        self.validator = EdxOAuth2Validator()
        self.request_factory = RequestFactory()

    def test_active_user_validates(self):
        assert self.user.is_active
        request = self.request_factory.get('/')
        assert self.validator.validate_user('darkhelmet', '12345', client=None, request=request)

    def test_inactive_user_validates(self):
        self.user.is_active = False
        self.user.save()
        request = self.request_factory.get('/')
        assert self.validator.validate_user('darkhelmet', '12345', client=None, request=request)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CustomAuthorizationViewTestCase(TestCase):
    """
    Test custom authorization view works.

    In particular, users should not be re-prompted to approve
    an application even if the access token is expired.
    (This is a temporary override until Auth Scopes is implemented.)
    """
    def setUp(self):
        super().setUp()
        self.dot_adapter = adapters.DOTAdapter()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='test')

        self.restricted_dot_app = self._create_restricted_app()
        self._create_expired_token(self.restricted_dot_app)

    def _create_restricted_app(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        restricted_app = self.dot_adapter.create_confidential_client(
            name='test restricted dot application',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dot-restricted-app-client-id',
        )
        models.RestrictedApplication.objects.create(application=restricted_app)
        return restricted_app

    def _create_expired_token(self, application):
        date_in_the_past = timezone.now() + datetime.timedelta(days=-100)
        dot_models.AccessToken.objects.create(
            user=self.user,
            token='1234567890',
            application=application,
            expires=date_in_the_past,
            scope='profile',
        )

    def _get_authorize(self, scope):
        authorize_url = '/oauth2/authorize/'
        return self.client.get(
            authorize_url,
            {
                'client_id': self.restricted_dot_app.client_id,
                'response_type': 'code',
                'state': 'random_state_string',
                'redirect_uri': DUMMY_REDIRECT_URL,
                'scope': scope,
            },
        )

    def test_no_reprompting(self):
        response = self._get_authorize(scope='profile')
        assert response.status_code == 302
        assert response.url.startswith(DUMMY_REDIRECT_URL)

    def test_prompting_with_new_scope(self):
        response = self._get_authorize(scope='email')
        assert response.status_code == 200
        self.assertContains(response, settings.OAUTH2_PROVIDER['SCOPES']['email'])
        self.assertNotContains(response, settings.OAUTH2_PROVIDER['SCOPES']['profile'])
