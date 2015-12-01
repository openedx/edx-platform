"""
Models providing Programs support for the LMS and Studio.
"""

from urlparse import urljoin

from django.db.models import NullBooleanField, IntegerField, URLField
from django.utils.translation import ugettext_lazy as _
from django.db import models

from config_models.models import ConfigurationModel


class ProgramsApiConfig(ConfigurationModel):
    """
    Manages configuration for connecting to the Programs service and using its
    API.
    """

    internal_service_url = URLField(verbose_name=_("Internal Service URL"))
    public_service_url = URLField(verbose_name=_("Public Service URL"))
    api_version_number = IntegerField(verbose_name=_("API Version"))
    enable_student_dashboard = NullBooleanField(verbose_name=_("Enable Student Dashboard Displays"))
    cache_ttl = models.PositiveIntegerField(
        verbose_name=_("Cache Time To Live"),
        default=0,
        help_text=_(
            "Specified in seconds. Enable caching by setting this to a value greater than 0."
        )
    )

    PROGRAMS_API_CACHE_KEY = "programs.api.data"

    @property
    def internal_api_url(self):
        """
        Generate a URL based on internal service URL and api version number.
        """
        return urljoin(self.internal_service_url, "/api/v{}/".format(self.api_version_number))

    @property
    def public_api_url(self):
        """
        Generate a URL based on public service URL and api version number.
        """
        return urljoin(self.public_service_url, "/api/v{}/".format(self.api_version_number))

    @property
    def is_student_dashboard_enabled(self):
        """
        Indicate whether LMS dashboard functionality related to Programs should
        be enabled or not.
        """
        return self.enabled and self.enable_student_dashboard

    @property
    def is_cache_enabled(self):
        """Whether responses from the Programs API will be cached."""
        return self.enabled and self.cache_ttl > 0
