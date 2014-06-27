"""
Handles requests for data, returning a json
"""

import logging

from django.utils import simplejson
from django.http import HttpResponse

from courseware.courses import get_course_with_access
from courseware.access import has_access
from class_dashboard import dashboard_data
from xmodule.modulestore.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


def has_instructor_access_for_class(user, course_id):
    """
    Returns true if the `user` is an instructor for the course.
    """

    course = get_course_with_access(user, 'staff', course_id, depth=None)
    return has_access(user, 'staff', course)


def all_sequential_open_distrib(request, course_id):
    """
    Creates a json with the open distribution for all the subsections in the course.

    `request` django request

    `course_id` the course ID for the course interested in

    Returns the format in dashboard_data.get_d3_sequential_open_distrib
    """

    json = {}

    # Only instructor for this particular course can request this information
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    if has_instructor_access_for_class(request.user, course_key):
        try:
            json = dashboard_data.get_d3_sequential_open_distrib(course_key)
        except Exception as ex:  # pylint: disable=broad-except
            log.error('Generating metrics failed with exception: %s', ex)
            json = {'error': "error"}
    else:
        json = {'error': "Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")


def all_problem_grade_distribution(request, course_id):
    """
    Creates a json with the grade distribution for all the problems in the course.

    `Request` django request

    `course_id` the course ID for the course interested in

    Returns the format in dashboard_data.get_d3_problem_grade_distrib
    """
    json = {}

    # Only instructor for this particular course can request this information
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    if has_instructor_access_for_class(request.user, course_key):
        try:
            json = dashboard_data.get_d3_problem_grade_distrib(course_key)
        except Exception as ex:  # pylint: disable=broad-except
            log.error('Generating metrics failed with exception: %s', ex)
            json = {'error': "error"}
    else:
        json = {'error': "Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")


def section_problem_grade_distrib(request, course_id, section):
    """
    Creates a json with the grade distribution for the problems in the specified section.

    `request` django request

    `course_id` the course ID for the course interested in

    `section` The zero-based index of the section for the course

    Returns the format in dashboard_data.get_d3_section_grade_distrib

    If this is requested multiple times quickly for the same course, it is better to call all_problem_grade_distribution
    and pick out the sections of interest.
    """
    json = {}

    # Only instructor for this particular course can request this information
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    if has_instructor_access_for_class(request.user, course_key):
        try:
            json = dashboard_data.get_d3_section_grade_distrib(course_key, section)
        except Exception as ex:  # pylint: disable=broad-except
            log.error('Generating metrics failed with exception: %s', ex)
            json = {'error': "error"}
    else:
        json = {'error': "Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")
