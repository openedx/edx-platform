"""
Models for credentials support for the LMS and Studio.
"""

from urlparse import urljoin

from config_models.models import ConfigurationModel
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.site_configuration import helpers

API_VERSION = 'v2'


class CredentialsApiConfig(ConfigurationModel):
    """
    Manages configuration for connecting to the Credential service and using its
    API.
    """

    class Meta(object):
        app_label = 'credentials'

    OAUTH2_CLIENT_NAME = 'credentials'
    API_NAME = 'credentials'
    CACHE_KEY = 'credentials.api.data'

    internal_service_url = models.URLField(
        verbose_name=_('Internal Service URL'),
        help_text='DEPRECATED: Use the setting CREDENTIALS_INTERNAL_SERVICE_URL.'
    )
    public_service_url = models.URLField(
        verbose_name=_('Public Service URL'),
        help_text='DEPRECATED: Use the setting CREDENTIALS_PUBLIC_SERVICE_URL.'
    )

    enable_learner_issuance = models.BooleanField(
        verbose_name=_('Enable Learner Issuance'),
        default=False,
        help_text=_(
            'Enable issuance of credentials via Credential Service.'
        )
    )
    enable_studio_authoring = models.BooleanField(
        verbose_name=_('Enable Authoring of Credential in Studio'),
        default=False,
        help_text=_(
            'Enable authoring of Credential Service credentials in Studio.'
        )
    )
    cache_ttl = models.PositiveIntegerField(
        verbose_name=_('Cache Time To Live'),
        default=0,
        help_text=_(
            'Specified in seconds. Enable caching by setting this to a value greater than 0.'
        )
    )

    def __unicode__(self):
        return self.public_api_url

    @property
    def internal_api_url(self):
        """
        Internally-accessible API URL root.
        """
        root = helpers.get_value('CREDENTIALS_INTERNAL_SERVICE_URL', settings.CREDENTIALS_INTERNAL_SERVICE_URL)
        return urljoin(root, '/api/{}/'.format(API_VERSION))

    @property
    def public_api_url(self):
        """
        Publicly-accessible API URL root.
        """
        root = helpers.get_value('CREDENTIALS_PUBLIC_SERVICE_URL', settings.CREDENTIALS_PUBLIC_SERVICE_URL)
        return urljoin(root, '/api/{}/'.format(API_VERSION))

    @property
    def is_learner_issuance_enabled(self):
        """
        Returns boolean indicating if credentials should be issued.
        """
        return self.enabled and self.enable_learner_issuance

    @property
    def is_cache_enabled(self):
        """Whether responses from the Credentials API will be cached."""
        return self.cache_ttl > 0
