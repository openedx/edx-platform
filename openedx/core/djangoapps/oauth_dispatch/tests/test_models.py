import ddt
from django.test import TestCase

from openedx.core.djangoapps.oauth_dispatch.models import Application
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory


@ddt.ddt
class ApplicationTests(TestCase):
    @ddt.data(
        Application.GRANT_AUTHORIZATION_CODE,
        Application.GRANT_IMPLICIT,
        Application.GRANT_PASSWORD,
        Application.GRANT_CLIENT_CREDENTIALS,
    )
    def test_allows_grant_type(self, authorization_grant_type):
        """ The method should always allow the client credentials grant. """
        application = ApplicationFactory(authorization_grant_type=authorization_grant_type)
        self.assertTrue(application.allows_grant_type(Application.GRANT_CLIENT_CREDENTIALS))
