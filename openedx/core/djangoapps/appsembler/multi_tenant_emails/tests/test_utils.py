"""
Tests utils for multi-tenant emails.
"""

import contextlib
from organizations.models import Organization, UserOrganizationMapping
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context


@contextlib.contextmanager
def with_organization_context(site_color, configs=None):
    """
    Tests helper to create organization with proper site configuration.

    This to be used like `with_site_configuration_context`.
    course_org_filter will be prefilled if not provided in configs.

    :param site_color: any name to be used for both site domain and organization name.
    :param configs: dictionary of configs.

    :yield: organization object.
    """

    configs = configs or {}
    if 'course_org_filter' not in configs:
        configs['course_org_filter'] = site_color

    with with_site_configuration_context(domain=site_color, configuration=configs) as site:
        try:
            org = Organization.objects.get(name=site_color)
        except Organization.DoesNotExist:
            org = Organization.objects.create(
                name=site_color,
                short_name=site_color,
            )
            org.sites.add(site)
        yield org
