"""
Instructor Dashboard API views

Non-html views which the instructor dashboard requests.

TODO add tracking
TODO a lot of these GETs should be PUTs
"""

import json
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.http import HttpResponse

from courseware.courses import get_course_with_access
from django.contrib.auth.models import User, Group

from instructor.enrollment import split_input_list, enroll_emails, unenroll_emails
from instructor.access import allow_access, revoke_access
import analytics.basic
import analytics.distributions
import analytics.csvs


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def enroll_unenroll(request, course_id):
    """
    Enroll or unenroll students by email.
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    emails_to_enroll = split_input_list(request.GET.get('enroll', ''))
    emails_to_unenroll = split_input_list(request.GET.get('unenroll', ''))

    enrolled_result = enroll_emails(course_id, emails_to_enroll)
    unenrolled_result = unenroll_emails(course_id, emails_to_unenroll)

    response_payload = {
        'enrolled':   enrolled_result,
        'unenrolled': unenrolled_result,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def access_allow_revoke(request, course_id):
    """
    Modify staff/instructor access. (instructor available only)

    Query parameters:
    email is the target users email
    level is one of ['instructor', 'staff']
    mode is one of ['allow', 'revoke']
    """
    course = get_course_with_access(request.user, course_id, 'instructor', depth=None)

    email = request.GET.get('email')
    level = request.GET.get('level')
    mode = request.GET.get('mode')

    user = User.objects.get(email=email)

    if mode == 'allow':
        allow_access(course, user, level)
    elif mode == 'revoke':
        revoke_access(course, user, level)
    else:
        raise ValueError("unrecognized mode '{}'".format(mode))

    response_payload = {
        'done': 'yup',
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def grading_config(request, course_id):
    """
    Respond with json which contains a html formatted grade summary.

    TODO maybe this shouldn't be html already
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)
    grading_config_summary = analytics.basic.dump_grading_context(course)

    response_payload = {
        'course_id': course_id,
        'grading_config_summary': grading_config_summary,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def enrolled_students_profiles(request, course_id, csv=False):
    """
    Respond with json which contains a summary of all enrolled students profile information.

    Response {"students": [{-student-info-}, ...]}

    TODO accept requests for different attribute sets
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    available_features = analytics.basic.AVAILABLE_STUDENT_FEATURES + analytics.basic.AVAILABLE_PROFILE_FEATURES
    query_features = ['username', 'name', 'email', 'language', 'location', 'year_of_birth', 'gender',
                      'level_of_education', 'mailing_address', 'goals']

    student_data = analytics.basic.enrolled_students_profiles(course_id, query_features)

    if not csv:
        response_payload = {
            'course_id':          course_id,
            'students':           student_data,
            'students_count':     len(student_data),
            'queried_features':   query_features,
            'available_features': available_features,
        }
        response = HttpResponse(json.dumps(response_payload), content_type="application/json")
        return response
    else:
        formatted = analytics.csvs.format_dictlist(student_data)
        return analytics.csvs.create_csv_response("enrolled_profiles.csv", formatted['header'], formatted['datarows'])


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile_distribution(request, course_id):
    """
    Respond with json of the distribution of students over selected fields which have choices.

    Ask for features through the 'features' query parameter.
    The features query parameter can be either a single feature name, or a json string of feature names.
    e.g.
        http://localhost:8000/courses/MITx/6.002x/2013_Spring/instructor_dashboard/api/profile_distribution?features=level_of_education
        http://localhost:8000/courses/MITx/6.002x/2013_Spring/instructor_dashboard/api/profile_distribution?features=%5B%22year_of_birth%22%2C%22gender%22%5D

    Example js query:
    $.get("http://localhost:8000/courses/MITx/6.002x/2013_Spring/instructor_dashboard/api/profile_distribution",
          {'features': JSON.stringify(['year_of_birth', 'gender'])},
          function(){console.log(arguments[0])})

    TODO how should query parameter interpretation work?
    TODO respond to csv requests as well
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    try:
        features = json.loads(request.GET.get('features'))
    except Exception:
        features = [request.GET.get('features')]

    feature_results = {}

    for feature in features:
        try:
            feature_results[feature] = analytics.distributions.profile_distribution(course_id, feature)
        except Exception as e:
            feature_results[feature] = {'error': "can not find distribution for '%s'" % feature}
            raise e

    response_payload = {
        'course_id':          course_id,
        'queried_features':   features,
        'available_features': analytics.distributions.AVAILABLE_PROFILE_FEATURES,
        'display_names':      {
            'gender': 'Gender',
            'level_of_education': 'Level of Education',
            'year_of_birth': 'Year Of Birth',
        },
        'feature_results':    feature_results,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response
