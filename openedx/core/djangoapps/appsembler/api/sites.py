from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from organizations.models import (
    Organization,
    OrganizationCourse,
    UserOrganizationMapping,
)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from student.models import CourseEnrollment

from openedx.core.djangoapps.appsembler.api.helpers import as_course_key


def get_course_keys_for_site(site):
    orgs = Organization.objects.filter(sites__in=[site])
    org_courses = OrganizationCourse.objects.filter(
        organization__in=orgs)
    course_ids = org_courses.values_list('course_id', flat=True)

    return [as_course_key(cid) for cid in course_ids]


def get_courses_for_site(site):
    course_keys = get_course_keys_for_site(site)
    courses = CourseOverview.objects.filter(id__in=course_keys)
    return courses


def get_site_for_course(course_id):
    """
    Given a course, return the related site or None

    For standalone mode, will always return the site
    For multisite mode, will return the site if there is a mapping between the
    course and the site. Otherwise `None` is returned

    # Implementation notes

    There should be only one organization per course.
    TODO: Figure out how we want to handle ``DoesNotExist``
    whether to let it raise back up raw or handle with a custom exception
    """

    org_courses = OrganizationCourse.objects.filter(course_id=str(course_id))
    if org_courses:
        # Keep until this assumption analyzed
        msg = 'Multiple orgs found for course: {}'
        assert org_courses.count() == 1, msg.format(course_id)
        first_org = org_courses.first().organization
        if hasattr(first_org, 'sites'):
            msg = 'Must have one and only one site. Org is "{}"'
            assert first_org.sites.count() == 1, msg.format(first_org.name)
            site = first_org.sites.first()
        else:
            site = None
    else:
        # We don't want to make assumptions of who our consumers are
        # TODO: handle no organizations found for the course
        site = None
    return site


def course_belongs_to_site(site, course_id):
    if not isinstance(site, Site):
        raise ValueError('invalid site object')
    return site == get_site_for_course(course_id)


def get_enrollments_for_site(site):
    course_keys = get_course_keys_for_site(site)
    return CourseEnrollment.objects.filter(course_id__in=course_keys)


def get_user_ids_for_site(site):
    orgs = Organization.objects.filter(sites__in=[site])
    mappings = UserOrganizationMapping.objects.filter(organization__in=orgs)
    return mappings.values_list('user_id', flat=True)


def get_users_for_site(site):
    user_ids = get_user_ids_for_site(site)
    return get_user_model().objects.filter(id__in=user_ids)
