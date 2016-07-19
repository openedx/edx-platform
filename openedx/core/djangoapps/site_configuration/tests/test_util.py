"""
Test helpers for Site Configuration.
"""

from functools import wraps
import contextlib

from mock import patch

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
    def _decorator(func):                       # pylint: disable=missing-docstring
        @wraps(func)
        def _decorated(*args, **kwargs):        # pylint: disable=missing-docstring
            # make a domain name out of directory name
            site, __ = Site.objects.get_or_create(domain=domain, name=domain)
            site_configuration, __ = SiteConfiguration.objects.get_or_create(
                site=site, enabled=True, values=configuration,
            )

            with patch('openedx.core.djangoapps.site_configuration.helpers.get_current_site_configuration',
                       return_value=site_configuration):
                with patch('openedx.core.djangoapps.theming.helpers.get_current_site', return_value=site):
                    return func(*args, **kwargs)
        return _decorated
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
    site_configuration, __ = SiteConfiguration.objects.get_or_create(
        site=site, enabled=True, values=configuration,
    )

    with patch('openedx.core.djangoapps.site_configuration.helpers.get_current_site_configuration',
               return_value=site_configuration):
        with patch('openedx.core.djangoapps.theming.helpers.get_current_site', return_value=site):
            yield
