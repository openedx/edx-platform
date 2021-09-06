"""
EdX Branding package.

Provides a way to retrieve "branded" parts of the site.

This module provides functions to retrieve basic branded parts
such as the site visible courses, university name and logo.
"""


from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_visible_courses(org=None, filter_=None):
    """
    Yield the CourseOverviews that should be visible in this branded
    instance.

    Arguments:
        org (string): Optional parameter that allows case-insensitive
            filtering by organization.
        filter_ (dict): Optional parameter that allows custom filtering by
            fields on the course.
    """
    # Import is placed here to avoid model import at project startup.
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

    current_site_orgs = configuration_helpers.get_current_site_orgs()

    courses = CourseOverview.objects.none()

    if org:
        # Check the current site's orgs to make sure the org's courses should be displayed
        if not current_site_orgs or org in current_site_orgs:
            courses = CourseOverview.get_all_courses(orgs=[org], filter_=filter_)
    elif current_site_orgs:
        # Only display courses that should be displayed on this site
        courses = CourseOverview.get_all_courses(orgs=current_site_orgs, filter_=filter_)
    else:
        courses = CourseOverview.get_all_courses(filter_=filter_)

    courses = courses.order_by('id')

    # Filtering can stop here.
    if current_site_orgs:
        return courses

    # See if we have filtered course listings in this domain
    filtered_visible_ids = None

    # this is legacy format, which also handle dev case, which should not filter
    subdomain = configuration_helpers.get_value('subdomain', 'default')
    if hasattr(settings, 'COURSE_LISTINGS') and subdomain in settings.COURSE_LISTINGS and not settings.DEBUG:
        filtered_visible_ids = frozenset(
            [CourseKey.from_string(c) for c in settings.COURSE_LISTINGS[subdomain]]
        )

    if filtered_visible_ids:
        return courses.filter(id__in=filtered_visible_ids)
    else:
        # Filter out any courses based on current org, to avoid leaking these.
        orgs = configuration_helpers.get_all_orgs()
        return courses.exclude(org__in=orgs)


def get_university_for_request():
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    return configuration_helpers.get_value('university')
