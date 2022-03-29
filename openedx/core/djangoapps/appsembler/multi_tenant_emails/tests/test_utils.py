"""
Tests utils for multi-tenant emails.
"""

import contextlib
from unittest.mock import patch

from django.conf import settings
from unittest import skipUnless
from openedx.core.djangolib.testing.utils import skip_unless_lms

from organizations.models import Organization, UserOrganizationMapping
from tahoe_sites.api import create_tahoe_site_by_link
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context

from student.tests.factories import UserFactory


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
            create_tahoe_site_by_link(organization=org, site=site)

        with patch('openedx.core.djangoapps.appsembler.sites.utils._get_current_organization', return_value=org):
            # Avoids having `get_current_organization` freak out due to missing request.
            yield org


def create_org_user(organization, is_amc_admin=False, **kwargs):
    """
    Create one user and save it to the database.
    """
    user = UserFactory.create(**kwargs)
    UserOrganizationMapping.objects.create(user=user, organization=organization, is_amc_admin=is_amc_admin)
    return user


def lms_multi_tenant_test(cls):
    """
    Ensure tests only run in lms while the APPSEMBLER_MULTI_TENANT_EMAILS feature is enabled.
    """
    cls = skip_unless_lms(cls)
    return skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This tests multi-tenancy')(cls)
