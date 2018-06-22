"""
Tests for oauth_dispatch models.
"""
from django.test import TestCase

from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationOrganizationFilterFactory


class ApplicationOrganizationFilterTestCase(TestCase):
    """
    Tests for the ApplicationOrganizationFilter model.
    """
    def test_unicode(self):
        """ Verify __unicode__ returns the expected serialization of the model. """
        org_filter = ApplicationOrganizationFilterFactory()
        organization = org_filter.organization
        assert unicode(org_filter) == unicode(':'.join([org_filter.provider_type, organization.short_name]))
