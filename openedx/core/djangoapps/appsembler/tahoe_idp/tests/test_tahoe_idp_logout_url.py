"""
Test the logout flow with `tahoe-idp` package.
"""

import ddt

from django.conf import settings
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch

from openedx.core.djangoapps.user_authn.views.logout import LogoutView
from openedx.core.djangolib.testing.utils import skip_unless_lms

from student.tests.factories import UserFactory


@ddt.ddt
@skip_unless_lms
@patch('tahoe_idp.api.get_logout_url')
class TahoeIdpLogoutTests(TestCase):
    """
    Tests that clicking logout works with both Tahoe IdP and non-idp logic.
    """

    request_factory = RequestFactory()

    @patch.dict(settings.FEATURES, {'ENABLE_TAHOE_IDP': False})
    def test_logout_without_tahoe_idp(self, _mock_get_logout_url):
        """
        Test the feature without Tahoe IdP enabled.
        """
        view = LogoutView()

        req = self.request_factory.post('/logout')
        req.get_host = Mock(return_value=None)
        req.site = Mock(domain='example.com')
        view.request = req

        assert view.target == '/'

    @patch.dict(settings.FEATURES, {'ENABLE_TAHOE_IDP': True})
    def test_logout_with_tahoe_idp(self, mock_get_logout_url):
        """
        Ensure the logout also logs out from the Tahoe IdP.
        """
        mock_get_logout_url.return_value = 'https://idp/logout'
        view = LogoutView()

        req = self.request_factory.post('/logout')
        req.get_host = Mock(return_value=None)
        req.site = Mock(domain='example.com')
        view.request = req

        assert view.target == 'https://idp/logout'
