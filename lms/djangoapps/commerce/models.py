"""
Commerce-related models.
"""
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from config_models.models import ConfigurationModel
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from logging import getLogger

LOGGER = getLogger(__name__)


class CommerceConfiguration(ConfigurationModel):
    """ Commerce configuration """

    class Meta(object):
        app_label = "commerce"

    API_NAME = 'commerce'
    CACHE_KEY = 'commerce.api.data'

    checkout_on_ecommerce_service = models.BooleanField(
        default=False,
        help_text=_('Use the checkout page hosted by the E-Commerce service.')
    )

    single_course_checkout_page = models.CharField(
        max_length=255,
        default='/basket/single-item/',
        help_text=_('Path to single course checkout page hosted by the E-Commerce service.')
    )
    cache_ttl = models.PositiveIntegerField(
        verbose_name=_('Cache Time To Live'),
        default=0,
        help_text=_(
            'Specified in seconds. Enable caching by setting this to a value greater than 0.'
        )
    )
    receipt_page = models.CharField(
        max_length=255,
        default='/commerce/checkout/receipt/?orderNum=',
        help_text=_('Path to order receipt page.')
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __unicode__(self):
        return "Commerce configuration"

    @property
    def is_cache_enabled(self):
        """Whether responses from the Ecommerce API will be cached."""
        return self.cache_ttl > 0

    def get_receipt_page_url(self, order_number):
        """
        Return absolute receipt page URL.
        Arguments:
            order_number (str): Order number
        Returns:
            Absolute receipt page URL, consisting of site domain and site receipt page.
        """
        site = self.site
        if site:
            try:
                return '{site_domain}{receipt_page_url}{order_number}'.format(
                    site_domain=site.domain,
                    receipt_page_url=site.configuration.receipt_page_url,  # pylint: disable=no-member
                    order_number=order_number
                )
            except AttributeError:
                LOGGER.info("Site Configuration is not enabled for site (%s).", site)
        return '{default_receipt_page_url}{order_number}'.format(
            default_receipt_page_url=SiteConfiguration.DEFAULT_RECEIPT_PAGE_URL,
            order_number=order_number
        )
