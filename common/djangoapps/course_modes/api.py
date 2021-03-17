"""
Python APIs exposed by the course_modes app to other in-process apps.
"""

from common.djangoapps.course_modes.models import CourseMode as _CourseMode


def get_paid_modes_for_course(course_run_id):
    """
    Returns a list of non-expired mode slugs for a course run ID that have a set minimum price.

    Params:
        course_run_id (CourseKey): The course run you want to get the paid modes for
    Returns:
        A list of paid modes (strings) that the course has attached to it.
    """
    return _CourseMode.paid_modes_for_course(course_run_id)


def is_eligible_for_certificate(mode_slug, status=None):
    """
    Returns whether or not the given mode_slug is eligible for a
    certificate. Currently all modes other than 'audit' grant a
    certificate. Note that audit enrollments which existed prior
    to December 2015 *were* given certificates, so there will be
    GeneratedCertificate records with mode='audit' which are
    eligible.
    """
    return _CourseMode.is_eligible_for_certificate(mode_slug, status)
