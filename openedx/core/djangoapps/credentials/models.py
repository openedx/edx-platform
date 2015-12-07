"""
Models for credentials support for the LMS and Studio.
"""

from urlparse import urljoin

from django.utils.translation import ugettext_lazy as _
from django.db import models

from config_models.models import ConfigurationModel


class CredentialsApiConfig(ConfigurationModel):
    """
    Manages configuration for connecting to the Credential service and using its
    API.
    """
    api_version_number = models.IntegerField(verbose_name=_("API Version"))
    internal_service_url = models.URLField(verbose_name=_("Internal Service URL"))
    public_service_url = models.URLField(verbose_name=_("Public Service URL"))

    enable_learner_credentials = models.BooleanField(
        verbose_name=_("Enable Learner Credential"),
        default=False,
        help_text=_(
            "This flag is required to enable learner credential."
        )
    )
    enable_studio_credentials = models.BooleanField(
        verbose_name=_("Enable Learner Credential in Studio"),
        default=False,
        help_text=_(
            "This flag is required to enable learner credential for studio authoring."
        )
    )

    @property
    def internal_api_url(self):
        """
        Generate a URL based on internal service URL and API version number.
        """
        return urljoin(self.internal_service_url, '/api/v{}/'.format(self.api_version_number))

    @property
    def public_api_url(self):
        """
        Generate a URL based on public service URL and API version number.
        """
        return urljoin(self.public_service_url, '/api/v{}/'.format(self.api_version_number))

    @property
    def is_learner_credentials_enabled(self):
        """
        Indicates whether the learner credential should be enabled or not.
        """
        return self.enabled and self.enable_learner_credentials

    @property
    def is_studio_credentials_enabled(self):
        """
        Indicates whether Studio functionality related to Credential should
        be enabled or not.
        """
        return self.enabled and self.enable_studio_credentials
