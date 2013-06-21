"""
Instructor Dashboard API views

Non-html views which the instructor dashboard requests.

TODO add tracking
TODO a lot of these GETs should be PUTs
"""

import json
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest

from courseware.courses import get_course_with_access
from django.contrib.auth.models import User, Group
from django_comment_common.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)

from courseware.models import StudentModule
import instructor.enrollment as enrollment
from instructor.enrollment import split_input_list, enroll_emails, unenroll_emails
import instructor.access as access
import analytics.basic
import analytics.distributions
import analytics.csvs


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def students_update_enrollment_email(request, course_id):
    """
    Enroll or unenroll students by email.
    Requires staff access.

    Query Parameters:
    - action in ['enroll', 'unenroll']
    - emails is string containing a list of emails separated by anything split_input_list can handle.
    - auto_enroll is a boolean (defaults to false)
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    action = request.GET.get('action', '')
    emails = split_input_list(request.GET.get('emails', ''))
    auto_enroll = request.GET.get('auto_enroll', '') in ['true', 'Talse', True]

    if action == 'enroll':
        results = enroll_emails(course_id, emails, auto_enroll=auto_enroll)
    elif action == 'unenroll':
        results = unenroll_emails(course_id, emails)
    else:
        raise ValueError("unrecognized action '{}'".format(action))

    response_payload = {
        'action':      action,
        'results':     results,
        'auto_enroll': auto_enroll,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def access_allow_revoke(request, course_id):
    """
    Modify staff/instructor access.
    Requires instructor access.

    Query parameters:
    email is the target users email
    rolename is one of ['instructor', 'staff', 'beta']
    mode is one of ['allow', 'revoke']
    """
    course = get_course_with_access(request.user, course_id, 'instructor', depth=None)

    email = request.GET.get('email')
    rolename = request.GET.get('rolename')
    mode = request.GET.get('mode')

    user = User.objects.get(email=email)

    if mode == 'allow':
        access.allow_access(course, user, rolename)
    elif mode == 'revoke':
        access.revoke_access(course, user, rolename)
    else:
        raise ValueError("unrecognized mode '{}'".format(mode))

    response_payload = {
        'DONE': 'YES',
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def list_course_role_members(request, course_id):
    """
    List instructors and staff.
    Requires staff access.

    rolename is one of ['instructor', 'staff', 'beta']
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    rolename = request.GET.get('rolename', '')

    if not rolename in ['instructor', 'staff', 'beta']:
        return HttpResponseBadRequest()

    def extract_user_info(user):
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    response_payload = {
        'course_id':   course_id,
        rolename:  map(extract_user_info, access.list_with_level(course, rolename)),
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


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def get_student_progress_url(request, course_id):
    """
    Get the progress url of a student.
    Limited to staff access.

    Takes query paremeter student_email and if the student exists
    returns e.g. {
        'progress_url': '/../...'
    }
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    student_email = request.GET.get('student_email')
    if not student_email:
        # TODO Is there a way to do a - say - 'raise Http400'?
        return HttpResponseBadRequest()
    user = User.objects.get(email=student_email)

    progress_url = reverse('student_progress', kwargs={'course_id': course_id, 'student_id': user.id})

    response_payload = {
        'course_id':    course_id,
        'progress_url': progress_url,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def redirect_to_student_progress(request, course_id):
    """
    Redirects to the specified students progress page
    Limited to staff access.

    Takes query parameter student_email
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    student_email = request.GET.get('student_email')
    if not student_email:
        # TODO Is there a way to do a - say - 'raise Http400'?
        return HttpResponseBadRequest()
    user = User.objects.get(email=student_email)

    progress_url = reverse('student_progress', kwargs={'course_id': course_id, 'student_id': user.id})

    response_payload = {
        'course_id':    course_id,
        'progress_url': progress_url,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def reset_student_attempts(request, course_id):
    """
    Resets a students attempts counter. Optionally deletes student state for a problem.
    Limited to staff access.

    Takes query parameter student_email
    Takes query parameter problem_to_reset
    Takes query parameter delete_module
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    student_email = request.GET.get('student_email')
    problem_to_reset = request.GET.get('problem_to_reset')
    will_delete_module = {'true': True}.get(request.GET.get('delete_module', ''), False)

    if not student_email or not problem_to_reset:
        return HttpResponseBadRequest()

    user = User.objects.get(email=student_email)

    try:
        enrollment.reset_student_attempts(course_id, user, problem_to_reset, delete_module=will_delete_module)
    except StudentModule.DoesNotExist:
        return HttpResponseBadRequest()

    response_payload = {
        'course_id':    course_id,
        'delete_module': will_delete_module,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def list_forum_members(request, course_id):
    """
    Resets a students attempts counter. Optionally deletes student state for a problem.
    Limited to staff access.

    Takes query parameter rolename
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    rolename = request.GET.get('rolename', '')

    if not rolename in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest()

    try:
        role = Role.objects.get(name=rolename, course_id=course_id)
        users = role.users.all().order_by('username')
    except Role.DoesNotExist:
        users = []

    def extract_user_info(user):
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    response_payload = {
        'course_id': course_id,
        rolename:   map(extract_user_info, users),
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def update_forum_role_membership(request, course_id):
    """
    Modify forum role access.

    Query parameters:
    email is the target users email
    rolename is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
    mode is one of ['allow', 'revoke']
    """
    course = get_course_with_access(request.user, course_id, 'instructor', depth=None)

    email = request.GET.get('email', '')
    rolename = request.GET.get('rolename', '')
    mode = request.GET.get('mode', '')

    if not rolename in [access.FORUM_ROLE_ADMINISTRATOR, access.FORUM_ROLE_MODERATOR, access.FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest()

    try:
        user = User.objects.get(email=email)
        access.update_forum_role_membership(course_id, user, rolename, mode)
    except User.DoesNotExist, Role.DoesNotExist:
        return HttpResponseBadRequest()

    response_payload = {
        'course_id': course_id,
        'mode':      mode,
        'DONE': 'YES',
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response
