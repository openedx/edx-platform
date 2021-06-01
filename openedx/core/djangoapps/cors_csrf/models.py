"""Models for cross-domain configuration. """


from config_models.models import ConfigurationModel
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class XDomainProxyConfiguration(ConfigurationModel):
    """
    Cross-domain proxy configuration.

    See `openedx.core.djangoapps.cors_csrf.views.xdomain_proxy` for an explanation of how this works.

    .. no_pii:
    """

    whitelist = models.fields.TextField(
        help_text=_(
            u"List of domains that are allowed to make cross-domain "
            "requests to this site.  Please list each domain on its own line."
        )
    )

    def __str__(self):
        return "XDomainProxyConfiguration()"
