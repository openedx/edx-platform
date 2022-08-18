"""
Helpers for Certificates in CMS.
"""
from tahoe_sites.api import get_organization_by_course, get_site_by_organization
from site_config_client.openedx.api import get_setting_value


def is_certificates_enabled_for_course_site(course_id):
    """
    Check the CERTIFICATES_HTML_VIEW setting for the course site.
    """
    course_organization = get_organization_by_course(course_id)
    course_site = get_site_by_organization(course_organization)

    course_site_config = course_site.configuration

    is_cert_enabled = get_setting_value(
        'CERTIFICATES_HTML_VIEW', default=False, site_configuration=course_site_config,
    )
    return is_cert_enabled
