# pylint: disable=invalid-name
"""
Utility library for working with the edx-organizations app
"""

from django.conf import settings
from django.db.utils import DatabaseError


def add_organization(organization_data):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return None
    from organizations import api as organizations_api
    return organizations_api.add_organization(organization_data=organization_data)


def add_organization_course(organization_data, course_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('ORGANIZATIONS_APP', False):
        return None
    from organizations import api as organizations_api
    return organizations_api.add_organization_course(organization_data=organization_data, course_key=course_id)


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
    # Due to the way unit tests run for edx-platform, models are not yet available at the time
    # of Django admin form instantiation.  This unfortunately results in an invocation of the following
    # workflow, because the test configuration is (correctly) configured to exercise the application
    # The good news is that this case does not manifest in the Real World, because migrations have
    # been run ahead of application instantiation and the flag set only when that is truly the case.
    try:
        return organizations_api.get_organizations()
    except DatabaseError:
        return []


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
