"""
Model factories for unit testing views or models.
"""
from factory.django import DjangoModelFactory

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class SiteConfigurationFactory(DjangoModelFactory):
    """
    Factory class for SiteConfiguration model
    """
    class Meta(object):
        model = SiteConfiguration

    values = {}
    enabled = True
