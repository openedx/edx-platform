"""
Tests for the tiers integration in the LMS.
"""

from django.urls import reverse
from django.test import TestCase

from ...multi_tenant_emails.tests.test_utils import with_organization_context
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class LMSSiteUnavailableViewTest(TestCase):
    """
    Unit tests for the Tiers views.
    """

    BLUE = 'blue2'

    def setUp(self):
        super().setUp()
        self.url = reverse('lms_site_unavailable')

    def test_site_unavailable_page(self):
        """
        Ensure trial expire page shows up with site information.
        """
        with with_organization_context(self.BLUE):
            response = self.client.get(self.url)
            body = response.content.decode(response.charset)
            message = 'The trial site of {} has expired.'.format(self.BLUE)
            assert message in body, 'Trial page works.'
