"""
Utility library for working with the edx-organizations app
"""


from django.conf import settings
from django.db.utils import DatabaseError


def add_organization(organization_data):
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
        return None
    from organizations import api as organizations_api
    return organizations_api.add_organization(organization_data=organization_data)


def add_organization_course(organization_data, course_id):
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
        return None
    from organizations import api as organizations_api
    return organizations_api.add_organization_course(organization_data=organization_data, course_key=course_id)


def get_organization(organization_id):
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
        return []
    from organizations import api as organizations_api
    return organizations_api.get_organization(organization_id)


def get_organization_by_short_name(organization_short_name):
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
        return None
    from organizations import api as organizations_api
    from organizations.exceptions import InvalidOrganizationException
    try:
        return organizations_api.get_organization_by_short_name(organization_short_name)
    except InvalidOrganizationException:
        return None


def get_organizations():
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
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
    if not organizations_enabled():
        return []
    from organizations import api as organizations_api
    return organizations_api.get_organization_courses(organization_id)


def get_course_organizations(course_id):
    """
    Client API operation adapter/wrapper
    """
    if not organizations_enabled():
        return []
    from organizations import api as organizations_api
    return organizations_api.get_course_organizations(course_id)


def get_course_organization_id(course_id):
    """
    Returns organization id for course or None if the course is not linked to an org
    """
    course_organization = get_course_organizations(course_id)
    if course_organization:
        return course_organization[0]['id']
    return None


def organizations_enabled():
    """
    Returns boolean indication if organizations app is enabled on not.
    """
    return settings.FEATURES.get('ORGANIZATIONS_APP', False)
