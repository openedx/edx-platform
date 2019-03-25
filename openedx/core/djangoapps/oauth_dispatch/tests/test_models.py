"""
Tests for oauth_dispatch models.
"""
from django.test import TestCase

from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationOrganizationFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class ApplicationOrganizationTestCase(TestCase):
    """
    Tests for the ApplicationOrganization model.
    """
    def test_to_jwt_filter_claim(self):
        """ Verify to_jwt_filter_claim returns the expected serialization of the model. """
        org_relation = ApplicationOrganizationFactory()
        organization = org_relation.organization
        jwt_filter_claim = org_relation.to_jwt_filter_claim()
        assert jwt_filter_claim == unicode(':'.join([org_relation.relation_type, organization.short_name]))
