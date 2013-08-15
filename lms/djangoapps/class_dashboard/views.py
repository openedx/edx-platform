from django.utils import simplejson
from django.http import HttpResponse

from courseware.courses import get_course_with_access
from courseware.access import has_access
from class_dashboard import dashboard_data

def has_instructor_access_for_class(user, course_id):
    course = get_course_with_access(user, course_id, 'staff', depth=None)
    return has_access(user, course, 'instructor')


def all_problem_attempt_distribution(request, course_id):
    """
    Creates a json with the attempt distribution for all the problems in the course.
    """

    json = {}

    # Only instructor for this particular course can request this information
    if has_instructor_access_for_class(request.user, course_id):
        json = dashboard_data.get_d3_problem_attempt_distribution(course_id)
    else:
        json = {'error':"Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")


def all_sequential_open_distribution(request, course_id):
    """
    Creates a json with the open distribution for all the subsections in the course.
    """


    json = {}

    # Only instructor for this particular course can request this information
    if has_instructor_access_for_class(request.user, course_id):
        json = dashboard_data.get_d3_sequential_open_distribution(course_id)
    else:
        json = {'error':"Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")


def all_problem_grade_distribution(request, course_id):
    """
    Creates a json with the grade distribution for all the problems in the course.
    """

    json = {}

    # Only instructor for this particular course can request this information
    if has_instructor_access_for_class(request.user, course_id):
        json = dashboard_data.get_d3_problem_grade_distribution_by_section(course_id)
    else:
        json = {'error':"Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")


def section_problem_grade_distribution(request, course_id, section):
    """
    Creates a json with the grade distribution for the problems in the specified section.

    Returns the format in dashboard_data.get_d3_section_grade_distribution.
    """

    json = {}

    # Only instructor for this particular course can request this information
    if has_instructor_access_for_class(request.user, course_id):
        json = dashboard_data.get_d3_section_grade_distribution(course_id, int(section))
    else:
        json = {'error':"Access Denied: User does not have access to this course's data"}

    return HttpResponse(simplejson.dumps(json), mimetype="application/json")

    
