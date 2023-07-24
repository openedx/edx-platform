"""
Contains methods for accessing course highlights and course due dates.
Course highlights is a schedule experience built on the Schedules app.
"""


from datetime import timedelta
import logging

from lms.djangoapps.courseware.courses import get_course
from lms.djangoapps.courseware.exceptions import CourseRunNotFound
from openedx.core.djangoapps.course_date_signals.utils import spaced_out_sections
from openedx.core.djangoapps.course_date_signals.waffle import CUSTOM_RELATIVE_DATES
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.lib.request_utils import get_request_or_stub

log = logging.getLogger(__name__)
DUE_DATE_FORMAT = "%b %d, %Y at %H:%M %Z"


def get_all_course_highlights(course_key):
    """
    This ignores access checks, since highlights may be lurking in currently
    inaccessible content.
    Returns a list of all the section highlights in the course
    """
    try:
        course = _get_course_with_highlights(course_key)

    except CourseUpdateDoesNotExist:
        return []
    else:
        highlights = [section.highlights for section in course.get_children() if not section.hide_from_toc]
        return highlights


def course_has_highlights(course):
    """
    Does the course have any highlights for any section/week in it?
    This ignores access checks, since highlights may be lurking in currently
    inaccessible content.

    Arguments:
        course (CourseBlock): course block to check
    """
    if not course.highlights_enabled_for_messaging:
        return False

    else:
        highlights_are_available = any(
            section.highlights
            for section in course.get_children()
            if not section.hide_from_toc
        )

        if not highlights_are_available:
            log.warning(
                f'Course team enabled highlights and provided no highlights in {course.id}'
            )

        return highlights_are_available


def course_has_highlights_from_store(course_key):
    """
    Does the course have any highlights for any section/week in it?
    This ignores access checks, since highlights may be lurking in currently
    inaccessible content.

    Arguments:
        course_key (CourseKey): course to lookup from the modulestore
    """
    try:
        course = get_course(course_key, depth=1)
    except CourseRunNotFound:
        return False
    return course_has_highlights(course)


def get_week_highlights(user, course_key, week_num):
    """
    Get highlights (list of unicode strings) for a given week.
    week_num starts at 1.

    Raises:
        CourseUpdateDoesNotExist: if highlights do not exist for
            the requested week_num.
    """
    course_descriptor = _get_course_with_highlights(course_key)
    course_block = _get_course_block(course_descriptor, user)
    sections_with_highlights = _get_sections_with_highlights(course_block)
    highlights = _get_highlights_for_week(
        sections_with_highlights,
        week_num,
        course_key,
    )
    return highlights


def get_upcoming_subsection_due_dates(user, course_key, start_date, target_date, current_date, duration=None):
    """
    Get section due dates, based upon the current date.
    """
    course_descriptor = get_course(course_key, depth=2)
    course_block = _get_course_block(course_descriptor, user)
    return _get_upcoming_due_dates(course_block, start_date, target_date, current_date, duration)


def get_next_section_highlights(user, course_key, start_date, target_date, duration=None):
    """
    Get highlights (list of unicode strings) for a week, based upon the current date.

    Raises:
        CourseUpdateDoeNotExist: if highlights do not exist for the requested date
    """
    course_descriptor = _get_course_with_highlights(course_key)
    course_block = _get_course_block(course_descriptor, user)
    return _get_highlights_for_next_section(course_block, start_date, target_date, duration)


def _get_course_with_highlights(course_key):
    """ Gets Course descriptor if highlights are enabled for the course """
    course_descriptor = get_course(course_key, depth=1)
    if not course_descriptor.highlights_enabled_for_messaging:
        raise CourseUpdateDoesNotExist(
            f'{course_key} Course Update Messages are disabled.'
        )

    return course_descriptor


def _get_course_block(course_descriptor, user):
    """ Gets course block that takes into account user state and permissions """
    # Adding courseware imports here to insulate other apps (e.g. schedules) to
    # avoid import errors.
    from lms.djangoapps.courseware.model_data import FieldDataCache
    from lms.djangoapps.courseware.block_render import get_block_for_descriptor

    # Fake a request to fool parts of the courseware that want to inspect it.
    request = get_request_or_stub()
    request.user = user

    # Now evil modulestore magic to inflate our block with user state and
    # permissions checks.
    field_data_cache = FieldDataCache.cache_for_block_descendents(
        course_descriptor.id, user, course_descriptor, depth=1, read_only=True,
    )
    course_block = get_block_for_descriptor(
        user, request, course_descriptor, field_data_cache, course_descriptor.id, course=course_descriptor,
    )
    if not course_block:
        raise CourseRunNotFound(course_descriptor.id)
    return course_block


def _section_has_highlights(section):
    """ Returns if the section has highlights """
    return section.highlights and not section.hide_from_toc


def _get_sections_with_highlights(course_block):
    """ Returns all sections that have highlights in a course """
    return list(filter(_section_has_highlights, course_block.get_children()))


def _get_highlights_for_week(sections, week_num, course_key):
    """ Gets highlights from the section at week num """
    # assume each provided section maps to a single week
    num_sections = len(sections)
    if not 1 <= week_num <= num_sections:
        raise CourseUpdateDoesNotExist(
            'Requested week {} but {} has only {} sections.'.format(
                week_num, course_key, num_sections
            )
        )

    section = sections[week_num - 1]
    return section.highlights


def _get_highlights_for_next_section(course, start_date, target_date, duration=None):
    """ Using the target date, retrieves highlights for the next section. """
    use_next_sections_highlights = False
    for index, section, weeks_to_complete in spaced_out_sections(course, duration):
        # We calculate section due date ourselves (rather than grabbing the due attribute),
        # since not every section has a real due date (i.e. not all are graded), but we still
        # want to know when this section should have been completed by the learner.
        section_due_date = start_date + weeks_to_complete

        if section_due_date.date() == target_date:
            use_next_sections_highlights = True
        elif use_next_sections_highlights and not _section_has_highlights(section):
            raise CourseUpdateDoesNotExist(
                f'Next section [{section.display_name}] has no highlights for {course.id}'
            )
        elif use_next_sections_highlights:
            return section.highlights, index + 1

    if use_next_sections_highlights:
        raise CourseUpdateDoesNotExist(
            f'Last section was reached. There are no more highlights for {course.id}'
        )

    return None, None


def _get_upcoming_due_dates(course, start_date, target_date, current_date, duration=None):
    """ Retrieves section names and due dates within the provided target_date. """
    date_items = []
    # Apply the same relative due date to all content inside a section,
    # unless that item already has a relative date set
    for _, section, days_to_complete in spaced_out_sections(course, duration):
        # Default to Personalized Learner Schedules (PLS) logic for self paced courses.
        section_due_date = start_date + days_to_complete
        section_date_items = []

        for subsection in section.get_children():
            # Get custom due date for subsection if it is set
            relative_weeks_due = subsection.fields['relative_weeks_due'].read_from(subsection)
            if CUSTOM_RELATIVE_DATES.is_enabled(course.id) and relative_weeks_due:
                section_due_date = start_date + timedelta(weeks=relative_weeks_due)

            # If the section_due_date is within current date and the target date range, include it in reminder list.
            if current_date <= section_due_date <= target_date:
                section_date_items.append((subsection.display_name, section_due_date.strftime(DUE_DATE_FORMAT)))
        date_items.extend(section_date_items)
    return date_items
