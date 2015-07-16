# pylint: disable=invalid-name
"""
Utility library for working with the edx-organizations app
"""

from django.conf import settings


def get_organization(organization_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return []
    from organizations import api as organizations_api
    return organizations_api.get_organization(organization_id)


def get_organizations():
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return []
    from organizations import api as organizations_api
    return organizations_api.get_organizations()


def get_organization_courses(organization_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return []
    from organizations import api as organizations_api
    return organizations_api.get_organization_courses(organization_id)


def get_course_organizations(course_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return []
    from organizations import api as organizations_api
    return organizations_api.get_course_organizations(course_id)
