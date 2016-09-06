"""
EdX Branding package.

Provides a way to retrieve "branded" parts of the site.

This module provides functions to retrieve basic branded parts
such as the site visible courses, university name and logo.
"""

from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from django.conf import settings

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_visible_courses(org=None, filter_=None):
    """
    Return the set of CourseOverviews that should be visible in this branded
    instance.

    Arguments:
        org (string): Optional parameter that allows case-insensitive
            filtering by organization.
        filter_ (dict): Optional parameter that allows custom filtering by
            fields on the course.
    """
    current_site_org = configuration_helpers.get_value('course_org_filter')

    if org and current_site_org:
        # Return an empty result if the org passed by the caller does not match the designated site org.
        courses = CourseOverview.get_all_courses(
            org=org,
            filter_=filter_,
        ) if org == current_site_org else []
    else:
        # We only make it to this point if one of org or current_site_org is defined.
        # If both org and current_site_org were defined, the code would have fallen into the
        # first branch of the conditional above, wherein an equality check is performed.
        target_org = org or current_site_org
        courses = CourseOverview.get_all_courses(org=target_org, filter_=filter_)

    courses = sorted(courses, key=lambda course: course.number)

    # Filtering can stop here.
    if current_site_org:
        return courses

    # See if we have filtered course listings in this domain
    filtered_visible_ids = None

    # this is legacy format, which also handle dev case, which should not filter
    subdomain = configuration_helpers.get_value('subdomain', 'default')
    if hasattr(settings, 'COURSE_LISTINGS') and subdomain in settings.COURSE_LISTINGS and not settings.DEBUG:
        filtered_visible_ids = frozenset(
            [SlashSeparatedCourseKey.from_deprecated_string(c) for c in settings.COURSE_LISTINGS[subdomain]]
        )

    if filtered_visible_ids:
        return [course for course in courses if course.id in filtered_visible_ids]
    else:
        # Filter out any courses based on current org, to avoid leaking these.
        orgs = configuration_helpers.get_all_orgs()
        return [course for course in courses if course.location.org not in orgs]


def get_university_for_request():
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    return configuration_helpers.get_value('university')
