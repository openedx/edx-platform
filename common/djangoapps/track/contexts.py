"""Generates common contexts"""

import re


COURSE_REGEX = re.compile(r'^.*?/courses/(?P<course_id>(?P<org_id>[^/]+)/[^/]+/[^/]+)')


def course_context_from_url(url):
    """
    Extracts the course_id from the given `url.`

    Example Returned Context::

        {
            'course_id': 'org/course/run',
            'org_id': 'org'
        }

    """
    url = url or ''

    context = {
        'course_id': '',
        'org_id': ''
    }
    match = COURSE_REGEX.match(url)
    if match:
        context.update(match.groupdict())

    return context
