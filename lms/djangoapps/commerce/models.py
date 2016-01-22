from django.db import models
from django.utils.translation import ugettext_lazy as _

from config_models.models import ConfigurationModel


class CommerceConfiguration(ConfigurationModel):
    """ Commerce configuration """

    checkout_on_ecommerce_service = models.BooleanField(
        default=False,
        help_text=_('Use the checkout page hosted by the E-Commerce service.')
    )

    single_course_checkout_page = models.CharField(
        max_length=255,
        default='/basket/single-item/',
        help_text=_('Path to single course checkout page hosted by the E-Commerce service.')
    )
