import logging

from django.conf import settings

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site

LOG = logging.getLogger(__name__)


# TODO: consider using a LoggerAdapter instead of this mixin:
# https://docs.python.org/2/library/logging.html#logging.LoggerAdapter
class PrefixedDebugLoggerMixin(object):
    log_prefix = None

    def __init__(self, *args, **kwargs):
        super(PrefixedDebugLoggerMixin, self).__init__(*args, **kwargs)
        if self.log_prefix is None:
            self.log_prefix = self.__class__.__name__

    def log_debug(self, message, *args, **kwargs):
        LOG.debug(self.log_prefix + ': ' + message, *args, **kwargs)


def get_config_value_from_site_or_settings(name, site=None, site_config_name=None):
    """
    Given a configuration setting name, try to get it from the site configuration and then fall back on the settings.

    If site_config_name is not specified then "name" is used as the key for both collections.

    Args:
        name (str): The name of the setting to get the value of.
        site: The site that we are trying to fetch the value for.
        site_config_name: The name of the setting within the site configuration.

    Returns:
        The value stored in the configuration.
    """
    if site_config_name is None:
        site_config_name = name

    if site is None:
        site = get_current_site()

    site_configuration = None
    if site is not None:
        try:
            site_configuration = getattr(site, "configuration", None)
        except SiteConfiguration.DoesNotExist:
            pass

    value_from_settings = getattr(settings, name, None)
    if site_configuration is not None:
        return site_configuration.get_value(site_config_name, default=value_from_settings)
    else:
        return value_from_settings
