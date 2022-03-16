"""
Test the various password reset flow with `tahoe-auth0` package.
"""

import ddt

from django.conf import settings
from django.core import mail
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch
from openedx.core.djangoapps.user_authn.views.password_reset import password_reset
from openedx.core.djangolib.testing.utils import skip_unless_lms

from student.tests.factories import UserFactory


@ddt.ddt
@skip_unless_lms
@patch('openedx.core.djangoapps.user_authn.views.password_reset.tahoe_auth0_api', create=True)
class Auth0ResetPasswordTests(TestCase):
    """
    Tests that clicking reset works with both Auth0 and non-auth0 logic.
    """
    request_factory = RequestFactory()

    @ddt.unpack
    @ddt.data({
        'enable_auth0': False,
        'message': 'Sanity check for upstream logic: should send via Open edX',
    }, {
        'enable_auth0': True,
        'message': 'Tahoe 2.0 logic: should NOT send email via Open edX, `tahoe_auth0` takes care of that',
    })
    def test_reset_password_with_auth0(self, tahoe_auth0_api_mock, enable_auth0, message):
        """
        Tests auth0/non-auth0 password reset.
        """
        user = UserFactory.create()
        req = self.request_factory.post('/password_reset/', {'email': user.email})
        req.get_host = Mock(return_value=None)
        req.site = Mock(domain='example.com')
        req.user = user

        with patch.dict(settings.FEATURES, {'ENABLE_TAHOE_AUTH0': enable_auth0}):
            with patch('crum.get_current_request', return_value=req):
                response = password_reset(req)

        assert response.status_code == 200, 'should succeed: {}'.format(
            response.content.decode('utf-8')
        )

        assert enable_auth0 == (not mail.outbox), message
        assert tahoe_auth0_api_mock.request_password_reset.called == enable_auth0, 'should be called only for auth0'

        if enable_auth0:
            tahoe_auth0_api_mock.request_password_reset.assert_called_once_with(user.email)
