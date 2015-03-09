"""Tests for util.authentication module."""

from mock import patch
from django.conf import settings
from rest_framework import permissions
from rest_framework.compat import patterns, url
from rest_framework.tests import test_authentication
from provider import scope, constants
from unittest import skipUnless

from ..authentication import OAuth2AuthenticationAllowInactiveUser


class OAuth2AuthAllowInactiveUserDebug(OAuth2AuthenticationAllowInactiveUser):
    """
    A debug class analogous to the OAuth2AuthenticationDebug class that tests
    the OAuth2 flow with the access token sent in a query param."""
    allow_query_params_token = True


# The following patch overrides the URL patterns for the MockView class used in
# rest_framework.tests.test_authentication so that the corresponding AllowInactiveUser
# classes are tested instead.
@skipUnless(settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'), 'OAuth2 not enabled')
@patch.object(
    test_authentication,
    'urlpatterns',
    patterns(
        '',
        url(
            r'^oauth2-test/$',
            test_authentication.MockView.as_view(authentication_classes=[OAuth2AuthenticationAllowInactiveUser])
        ),
        url(
            r'^oauth2-test-debug/$',
            test_authentication.MockView.as_view(authentication_classes=[OAuth2AuthAllowInactiveUserDebug])
        ),
        url(
            r'^oauth2-with-scope-test/$',
            test_authentication.MockView.as_view(
                authentication_classes=[OAuth2AuthenticationAllowInactiveUser],
                permission_classes=[permissions.TokenHasReadWriteScope]
            )
        )
    )
)
class OAuth2AuthenticationAllowInactiveUserTestCase(test_authentication.OAuth2Tests):
    """
    Tests the OAuth2AuthenticationAllowInactiveUser class by running all the existing tests in
    OAuth2Tests but with the is_active flag on the user set to False.
    """
    def setUp(self):
        super(OAuth2AuthenticationAllowInactiveUserTestCase, self).setUp()

        # set the user's is_active flag to False.
        self.user.is_active = False
        self.user.save()

        # Override the SCOPE_NAME_DICT setting for tests for oauth2-with-scope-test.  This is
        # needed to support READ and WRITE scopes as they currently aren't supported by the
        # edx-auth2-provider, and their scope values collide with other scopes defined in the
        # edx-auth2-provider.
        scope.SCOPE_NAME_DICT = {'read': constants.READ, 'write': constants.WRITE}
