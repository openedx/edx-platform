"""
Tests for the sites.middlewares module.
"""

from mock import patch, Mock
from django.test import TestCase

from openedx.core.djangoapps.appsembler.sites.middleware import LmsCurrentOrganizationMiddleware


@patch('openedx.core.djangoapps.appsembler.sites.middleware.get_current_organization')
class LmsCurrentOrganizationMiddlewareTests(TestCase):
    def test_with_organization(self, get_current_organization):
        middleware = LmsCurrentOrganizationMiddleware()
        request = Mock(session={})
        fake_org = Mock()
        get_current_organization.return_value = fake_org

        middleware.process_request(request)
        assert request.session['organization'] is fake_org

    def test_with_no_organization(self, get_current_organization):
        middleware = LmsCurrentOrganizationMiddleware()
        request = Mock(session={})
        get_current_organization.return_value = None

        middleware.process_request(request)
        assert request.session['organization'] is None
