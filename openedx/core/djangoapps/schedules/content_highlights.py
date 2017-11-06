from courseware.module_render import get_module_for_descriptor
from courseware.model_data import FieldDataCache
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from request_cache import get_request_or_stub

from xmodule.modulestore.django import modulestore


def course_has_highlights(course_key):
    """
    Does the course have any highlights for any section/week in it?
    This ignores access checks, since highlights may be lurking in currently
    inaccessible content.
    """
    if not COURSE_UPDATE_WAFFLE_FLAG.is_enabled(course_key):
        return False

    course = modulestore().get_course(course_key, depth=1)
    return any(
        section.highlights
        for section in course.get_children()
        if not section.hide_from_toc
    )


def get_week_highlights(user, course_key, week_num):
    """
    Get highlights (list of unicode strings) for a given week.
    week_num starts at 1.
    Raises CourseUpdateDoesNotExist if highlights do not exist for
    the requested week_num.
    """
    if not COURSE_UPDATE_WAFFLE_FLAG.is_enabled(course_key):
        raise CourseUpdateDoesNotExist(
            "%s does not have Course Updates enabled.",
            course_key
        )

    course_descriptor = _get_course_descriptor(course_key)
    course_module = _get_course_module(course_descriptor, user)
    sections_with_highlights = _get_sections_with_highlights(course_module)
    highlights = _get_highlights_for_week(sections_with_highlights, week_num, course_key)
    return highlights


def _get_course_descriptor(course_key):
    course_descriptor = modulestore().get_course(course_key, depth=1)
    if course_descriptor is None:
        raise CourseUpdateDoesNotExist(
            "Course {} not found.".format(course_key)
        )
    return course_descriptor


def _get_course_module(course_descriptor, user):
    # Fake a request to fool parts of the courseware that want to inspect it.
    request = get_request_or_stub()
    request.user = user

    # Now evil modulestore magic to inflate our descriptor with user state and
    # permissions checks.
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_descriptor.id, user, course_descriptor, depth=1, read_only=True,
    )
    return get_module_for_descriptor(
        user, request, course_descriptor, field_data_cache, course_descriptor.id, course=course_descriptor,
    )


def _get_sections_with_highlights(course_module):
    return [
        section for section in course_module.get_children()
        if section.highlights and not section.hide_from_toc
    ]


def _get_highlights_for_week(sections, week_num, course_key):
    # assume each provided section maps to a single week
    num_sections = len(sections)
    if not (1 <= week_num <= num_sections):
        raise CourseUpdateDoesNotExist(
            "Requested week {} but {} has only {} sections.".format(
                week_num, course_key, num_sections
            )
        )

    section = sections[week_num - 1]
    return section.highlights
