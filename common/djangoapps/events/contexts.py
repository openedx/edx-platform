"""
Utilities to help with common context construction tasks.
"""

from __future__ import absolute_import

def course_context_from_id(course_id):
    """
    Given a `course_id` string, it constructs a context with the raw course_id
    as well as a breakdown of the various fields contained within it.

    Specifically:

    * course_id - the full course_id in the form "organization/course_name/course_run"
    * organization
    * course_name
    * course_run

    Any context that is overriding these fields should use this method to
    construct its context to ensure it properly overrides all relevant
    fields.
    """
    try:
        org, course, run = course_id.split('/')
    except ValueError:
        org = course = run = ''

    return {
        'course_id': course_id,
        'organization': org,
        'course_name': course,
        'course_run': run
    }