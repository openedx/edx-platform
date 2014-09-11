"""Generates common contexts"""
import logging

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from util.request import COURSE_REGEX

log = logging.getLogger(__name__)


def course_context_from_url(url):
    """
    Extracts the course_context from the given `url` and passes it on to
    `course_context_from_course_id()`.
    """
    url = url or ''

    match = COURSE_REGEX.match(url)
    course_id = None
    if match:
        course_id_string = match.group('course_id')
        try:
            course_id = CourseKey.from_string(course_id_string)
        except InvalidKeyError:
            log.warning(
                'unable to parse course_id "{course_id}"'.format(
                    course_id=course_id_string
                ),
                exc_info=True
            )

    return course_context_from_course_id(course_id)


def course_context_from_course_id(course_id):
    """
    Creates a course context from a `course_id`.

    Example Returned Context::

        {
            'course_id': 'FooX/Bar/1T2014',
            'org_id': 'FooX',
            'course_key': {
                'org': 'FooX',
                'course': 'Bar',
                'run': '1T2014'
            }
        }

    Another Example::

        {
            'course_id': 'course-v1:FooX+Bar+1T2014+branch@draft',
            'org_id': 'FooX',
            'course_key': {
                'org': 'FooX',
                'course': 'Bar',
                'run': '1T2014',
                'branch': 'draft'
            }
        }

    """
    if course_id is None:
        return {'course_id': '', 'org_id': ''}

    # TODO: Make this accept any CourseKey, and serialize it using .to_string
    assert(isinstance(course_id, CourseKey))
    course_id_detail = {
        'org': course_id.org,
        'course': course_id.course,
        'run': course_id.run,
    }

    for optional_key in ['branch', 'version_guid']:
        value = getattr(course_id, optional_key, None)
        if value:
            course_id_detail[optional_key] = value

    return {
        'course_id': unicode(course_id),
        'org_id': course_id.org,
        'course_key': course_id_detail,
    }
