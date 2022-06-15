from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django.test.client import RequestFactory
from mock import patch, PropertyMock

from tiers.tier_info import TierInfo

from openedx.core.djangoapps.appsembler.tahoe_tiers.middleware import TahoeTierMiddleware
from openedx.core.djangoapps.appsembler.tahoe_tiers.helpers import TIER_INFO_REQUEST_FIELD_NAME


@patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
class TestMiddlewareTests(TestCase):
    """
    TiersMiddleware tests with a non-expired trial Tier.
    """

    def setUp(self):
        super(TestMiddlewareTests, self).setUp()
        self.middleware = TahoeTierMiddleware()
        self.tier_info = TierInfo(
            tier='trial',
            subscription_ends=timezone.now() + timedelta(days=40),
            always_active=False,
        )
        self.request = RequestFactory().get('/dashboard')
        setattr(self.request, TIER_INFO_REQUEST_FIELD_NAME, self.tier_info)
        self.request.session = {}
        self.user = User()
        self.request.user = self.user

    def test_empty_by_default_attributes(self):
        default = object()
        for attrib in ['DISPLAY_EXPIRATION_WARNING', 'TIER_EXPIRES_IN', 'TIER_EXPIRED', 'TIER_NAME']:
            assert self.request.session.get(attrib, default) is default

    def test_added_session_attribs(self):
        self.middleware.process_request(self.request)
        assert not self.request.session['TIER_EXPIRED']
        assert self.request.session['TIER_EXPIRES_IN'] == self.tier_info.time_til_expiration()
        assert self.request.session['DISPLAY_EXPIRATION_WARNING']
        assert self.request.session['TIER_NAME'] == 'trial'


class TestExpiredTierMiddleware(TestCase):
    """
    TiersMiddleware tests with an expired trial Tier.
    """

    def setUp(self):
        super(TestExpiredTierMiddleware, self).setUp()
        self.middleware = TahoeTierMiddleware()
        self.tier_info = TierInfo(
            tier='trial',
            subscription_ends=timezone.now() - timedelta(days=40),
            always_active=False,
        )
        self.request = RequestFactory().get('/dashboard')
        setattr(self.request, TIER_INFO_REQUEST_FIELD_NAME, self.tier_info)
        self.request.session = {}
        self.user = User()
        self.request.user = self.user

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
    @override_settings(TIERS_EXPIRED_REDIRECT_URL='/expired')
    def test_added_session_attribs(self):
        self.middleware.process_request(self.request)
        assert self.request.session['TIER_EXPIRED']
        assert self.request.session['TIER_NAME'] == 'trial'

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
    @override_settings(TIERS_EXPIRED_REDIRECT_URL='/expired')
    def test_redirect(self):
        response = self.middleware.process_request(self.request)
        assert response, 'should redirect'
        assert response.status_code == 302 and response['Location'] == '/expired', 'should redirect'

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
    @override_settings(TIERS_EXPIRED_REDIRECT_URL='/expired')
    def test_expired_url_should_not_redirect(self):
        self.request.path = '/expired'
        response = self.middleware.process_request(self.request)
        assert not response, 'should NOT redirect if it is already on expred url'

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
    @override_settings(TIERS_EXPIRED_REDIRECT_URL='/expired')
    def test_admin_url_should_not_redirect(self):
        self.request.path = '/admin'
        response = self.middleware.process_request(self.request)
        assert not response, 'should NOT redirect if if on /admin'

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
    @override_settings(TIERS_EXPIRED_REDIRECT_URL='/expired')
    def test_homepage_url_should_redirect(self):
        self.request.path = '/'
        response = self.middleware.process_request(self.request)
        assert response, 'should redirect if if on homepage "/"'

    @patch.object(User, 'is_authenticated', PropertyMock(return_value=False))
    def test_redirect_non_authenticated(self):
        self.middleware.process_request(self.request)
        assert 'TIER_NAME' in self.request.session
        assert self.request.session['TIER_EXPIRED']
