"""Generates common contexts"""

import re
import logging

from xmodule.course_module import CourseDescriptor


COURSE_REGEX = re.compile(r'^.*?/courses/(?P<course_id>[^/]+/[^/]+/[^/]+)')
log = logging.getLogger(__name__)


def course_context_from_url(url):
    """
    Extracts the course_id from the given `url` and passes it on to
    `course_context_from_course_id()`.
    """
    url = url or ''

    match = COURSE_REGEX.match(url)
    course_id = ''
    if match:
        course_id = match.group('course_id') or ''

    return course_context_from_course_id(course_id)


def course_context_from_course_id(course_id):
    """
    Creates a course context from a `course_id`.

    Example Returned Context::

        {
            'course_id': 'org/course/run',
            'org_id': 'org'
        }

    """

    course_id = course_id or ''
    context = {
        'course_id': course_id,
        'org_id': ''
    }

    if course_id:
        try:
            location = CourseDescriptor.id_to_location(course_id)
            context['org_id'] = location.org
        except ValueError:
            log.warning(
                'Unable to parse course_id "{course_id}"'.format(
                    course_id=course_id
                ),
                exc_info=True
            )

    return context


def user_context(user):
    """
    Creates a user context from `user`
    """
    context = {
        'user': user,
    }
    return context
