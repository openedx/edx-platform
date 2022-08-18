"""
Helpers for Certificates in CMS.
"""

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def is_certificates_enabled_for_course_site(course_id):
    """
    Check the CERTIFICATES_HTML_VIEW setting for the course site.
    """
    return configuration_helpers.get_value_for_org(
        course_id.org,
        'CERTIFICATES_HTML_VIEW',
        False
    )
