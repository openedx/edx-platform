"""
Test helpers for Site Configuration.
"""

import contextlib

from unittest.mock import patch, Mock

from django.contrib.sites.models import Site

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


def with_site_configuration(domain="test.localhost", configuration=None):
    """
    A decorator to run a test with a configuration enabled.

    Args:
        domain (str): domain name for the test site.
        configuration (dict): configuration to use for the test site.
    """
    # This decorator creates Site and SiteConfiguration instances for given domain
    def _get_site(*args, **kwargs):
        site, _ = Site.objects.get_or_create(domain=domain, name=domain)
        return site

    def _get_site_config(*args, **kwargs):
        site = _get_site()
        site_configuration, _ = SiteConfiguration.objects.get_or_create(
            site=site,
            defaults={"enabled": True},
        )
        return site_configuration

    def _decorator(test_class_or_func):
        config_patcher = patch('openedx.core.djangoapps.site_configuration.helpers.get_current_site_configuration',
                               Mock(side_effect=_get_site_config))
        crs_patcher = patch('openedx.core.djangoapps.theming.helpers.get_current_site', Mock(side_effect=_get_site))
        site_patcher = patch('django.contrib.sites.models.SiteManager.get_current', Mock(side_effect=_get_site))
        return config_patcher(crs_patcher(site_patcher(test_class_or_func)))
    return _decorator


@contextlib.contextmanager
def with_site_configuration_context(domain="test.localhost", configuration=None):
    """
   A function to get a context manger to run a test with a configuration enabled.

    Args:
        domain (str): domain name for the test site.
        configuration (dict): configuration to use for the test site.
    """
    site, __ = Site.objects.get_or_create(domain=domain, name=domain)
    site_configuration, created = SiteConfiguration.objects.get_or_create(
        site=site,
        defaults={"enabled": True, "site_values": configuration},
    )
    if not created:
        site_configuration.site_values = configuration
        site_configuration.save()

    with patch('openedx.core.djangoapps.site_configuration.helpers.get_current_site_configuration',
               return_value=site_configuration):
        with patch('openedx.core.djangoapps.theming.helpers.get_current_site', return_value=site):
            with patch('django.contrib.sites.models.SiteManager.get_current', return_value=site):
                yield
