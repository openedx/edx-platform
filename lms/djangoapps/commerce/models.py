"""
Commerce-related models.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _

from config_models.models import ConfigurationModel


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

    def __unicode__(self):
        return "Commerce configuration"

    @property
    def is_cache_enabled(self):
        """Whether responses from the Ecommerce API will be cached."""
        return self.cache_ttl > 0
