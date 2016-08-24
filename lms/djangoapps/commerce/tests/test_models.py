""" Tests for commerce models. """

import ddt

from django.test import TestCase

from commerce.models import CommerceConfiguration
from microsite_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory


@ddt.ddt
class CommerceConfigurationModelTests(TestCase):
    """ Tests for the CommerceConfiguration model. """

    def setUp(self):
        """
        Create CommerceConfiguration object
        """
        super(CommerceConfigurationModelTests, self).setUp()
        self.site = SiteFactory()
        self.order_number = "TEST_ORDER_NUMBER"

    def configure_commerce(self, is_configured, is_default_page):
        """
        Helper for creating specific Commerce Configuration.

        Arguments:
            is_configured (bool): Indicates whether or not the Site has Site Configuration.
            is_default_page (bool): Indicates whether or not the LMS receipt page is used

        Returns:
            Commerce configuration.
        """
        if not is_default_page:
            if is_configured:
                SiteConfigurationFactory.create(
                    site=self.site,
                    receipt_page_url='receipt/page/url',
                )

        return CommerceConfiguration.objects.create(
            enabled=True,
            site=self.site if not is_default_page else None
        )

    @ddt.data((True, False), (False, False), (False, True))
    @ddt.unpack
    def test_get_receipt_page_url_site_configured(self, is_configured, is_default_page):
        commerce_configuration = self.configure_commerce(is_configured, is_default_page)
        receipt_page_url = commerce_configuration.get_receipt_page_url(self.order_number)
        expected_receipt_page_url = '{site_domain}{receipt_page_url}{order_number}'.format(
            site_domain=self.site.domain,
            receipt_page_url=self.site.configuration.receipt_page_url,  # pylint: disable=no-member
            order_number=self.order_number
        ) if (is_configured and not is_default_page) else '{default_receipt_page_url}{order_number}'.format(
            default_receipt_page_url=SiteConfiguration.DEFAULT_RECEIPT_PAGE_URL,
            order_number=self.order_number
        )
        self.assertEqual(
            receipt_page_url,
            expected_receipt_page_url
        )
