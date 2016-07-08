"""Models governing integration with the catalog service."""
from django.utils.translation import ugettext_lazy as _
from django.db import models

from config_models.models import ConfigurationModel


class CatalogIntegration(ConfigurationModel):
    """Manages configuration for connecting to the catalog service and using its API."""
    API_NAME = 'catalog'
    CACHE_KEY = 'catalog.api.data'

    internal_api_url = models.URLField(
        verbose_name=_('Internal API URL'),
        help_text=_(
            'API root to be used for server-to-server requests (e.g., https://catalog-internal.example.com/api/v1/).'
        )
    )

    cache_ttl = models.PositiveIntegerField(
        verbose_name=_('Cache Time To Live'),
        default=0,
        help_text=_(
            'Specified in seconds. Enable caching of API responses by setting this to a value greater than 0.'
        )
    )

    @property
    def is_cache_enabled(self):
        """Whether responses from the catalog API will be cached."""
        return self.cache_ttl > 0

    def __unicode__(self):
        return self.internal_api_url
