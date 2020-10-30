"""
Tests for the tiers integration in the LMS.
"""



from django.urls import reverse
from django.test import TestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms

from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import with_organization_context


class SiteUnavailableViewTest(TestCase):
    """
    Unit tests for the Tiers views.
    """

    BLUE = 'blue2'

    def setUp(self):
        super(SiteUnavailableViewTest, self).setUp()
        self.url = reverse('site_unavailable')

    def test_site_unavailable_page(self):
        """
        Ensure trial expire page shows up with site information.
        """
        with with_organization_context(self.BLUE):
            response = self.client.get(self.url)
            message = 'The trial site of {} has expired.'.format(self.BLUE)
            assert message in response.content, 'Trial page works.'
