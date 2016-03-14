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
from microsite_configuration import microsite
from django.contrib.staticfiles.storage import staticfiles_storage
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_visible_courses():
    """
    Return the set of CourseDescriptors that should be visible in this branded instance
    """
    filtered_by_org = microsite.get_value('course_org_filter')
    courses = CourseOverview.get_all_courses(org=filtered_by_org)
    courses = sorted(courses, key=lambda course: course.number)

    # See if we have filtered course listings in this domain
    filtered_visible_ids = None

    # this is legacy format which is outside of the microsite feature -- also handle dev case, which should not filter
    subdomain = microsite.get_value('subdomain', 'default')
    if hasattr(settings, 'COURSE_LISTINGS') and subdomain in settings.COURSE_LISTINGS and not settings.DEBUG:
        filtered_visible_ids = frozenset(
            [SlashSeparatedCourseKey.from_deprecated_string(c) for c in settings.COURSE_LISTINGS[subdomain]]
        )

    if filtered_by_org:
        return [course for course in courses if course.location.org == filtered_by_org]
    if filtered_visible_ids:
        return [course for course in courses if course.id in filtered_visible_ids]
    else:
        # Let's filter out any courses in an "org" that has been declared to be
        # in a Microsite
        org_filter_out_set = microsite.get_all_orgs()
        return [course for course in courses if course.location.org not in org_filter_out_set]


def get_university_for_request():
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    return microsite.get_value('university')


def get_logo_url():
    """
    Return the url for the branded logo image to be used
    """

    # if the MicrositeConfiguration has a value for the logo_image_url
    # let's use that
    image_url = microsite.get_value('logo_image_url')
    if image_url:
        return '{static_url}{image_url}'.format(
            static_url=settings.STATIC_URL,
            image_url=image_url
        )

    # otherwise, use the legacy means to configure this
    university = microsite.get_value('university')

    if university is None and settings.FEATURES.get('IS_EDX_DOMAIN', False):
        return staticfiles_storage.url('images/edx-theme/edx-logo-77x36.png')
    elif university:
        return staticfiles_storage.url('images/{uni}-on-edx-logo.png'.format(uni=university))
    else:
        return staticfiles_storage.url('images/logo.png')
