"""Generates common contexts"""
import logging

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.keys import CourseKey
from util.request import COURSE_REGEX

log = logging.getLogger(__name__)


def course_context_from_url(url):
    """
    Extracts the course_context from the given `url` and passes it on to
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

    assert(isinstance(course_id, CourseKey))

    context = {
        'course_id': course_id._to_string(),
        'org_id': ''
    }

    if course_id:
        try:
            context['org_id'] = course_id.org
        except ValueError:
            log.warning(
                'Unable to parse course_id "{course_id}"'.format(
                    course_id=course_id
                ),
                exc_info=True
            )

    return context
