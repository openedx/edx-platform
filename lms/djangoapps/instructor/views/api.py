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
import instructor_task.api
import instructor.enrollment as enrollment
from instructor.enrollment import split_input_list, enroll_emails, unenroll_emails
import instructor.access as access
import analytics.basic
import analytics.distributions
import analytics.csvs


def common_exceptions_400(fn):
    """ Catches common exceptions and renders matching 400 errors. (decorator) """
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except User.DoesNotExist:
            return HttpResponseBadRequest("User does not exist.")
    return wrapped


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

    action = request.GET.get('action')
    emails = split_input_list(request.GET.get('emails'))
    auto_enroll = request.GET.get('auto_enroll') in ['true', 'True', True]

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
@common_exceptions_400
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

    rolename = request.GET.get('rolename')

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

    available_features = analytics.basic.AVAILABLE_FEATURES
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
            feature_results[feature] = {'error': "Error finding distribution for distribution for '{}'.".format(feature)}
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
@common_exceptions_400
def redirect_to_student_progress(request, course_id):
    """
    Redirects to the specified students progress page
    Limited to staff access.

    Takes query parameter student_email
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    student_email = request.GET.get('student_email')
    if not student_email:
        return HttpResponseBadRequest("Must provide an email.")

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
@common_exceptions_400
def reset_student_attempts(request, course_id):
    """
    Resets a students attempts counter or starts a task to reset all students attempts counters. Optionally deletes student state for a problem.
    Limited to staff access.

    Takes either of the following query paremeters
        - problem_to_reset is a urlname of a problem
        - student_email is an email
        - all_students is a boolean
        - delete_module is a boolean
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    problem_to_reset = request.GET.get('problem_to_reset')
    student_email = request.GET.get('student_email')
    all_students = request.GET.get('all_students', False) in ['true', 'True', True]
    will_delete_module = request.GET.get('delete_module', False) in ['true', 'True', True]

    if not (problem_to_reset and (all_students or student_email)):
        return HttpResponseBadRequest()
    if will_delete_module and all_students:
        return HttpResponseBadRequest()

    module_state_key = _module_state_key_from_problem_urlname(course_id, problem_to_reset)

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student_email:
        try:
            student = User.objects.get(email=student_email)
            enrollment.reset_student_attempts(course_id, student, module_state_key, delete_module=will_delete_module)
        except StudentModule.DoesNotExist:
            return HttpResponseBadRequest("Module does not exist.")
    elif all_students:
        task = instructor_task.api.submit_reset_problem_attempts_for_all_students(request, course_id, module_state_key)
        response_payload['task'] = 'created'
    else:
        return HttpResponseBadRequest()

    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@common_exceptions_400
def rescore_problem(request, course_id):
    """
    Starts a background process a students attempts counter. Optionally deletes student state for a problem.
    Limited to staff access.

    Takes either of the following query paremeters
        - problem_to_reset is a urlname of a problem
        - student_email is an email
        - all_students is a boolean

    all_students will be ignored if student_email is present
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    problem_to_reset = request.GET.get('problem_to_reset')
    student_email = request.GET.get('student_email', False)
    all_students = request.GET.get('all_students') in ['true', 'True', True]

    if not (problem_to_reset and (all_students or student_email)):
        return HttpResponseBadRequest()

    module_state_key = _module_state_key_from_problem_urlname(course_id, problem_to_reset)

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student_email:
        response_payload['student_email'] = student_email
        student = User.objects.get(email=student_email)
        task = instructor_task.api.submit_rescore_problem_for_student(request, course_id, module_state_key, student)
        response_payload['task'] = 'created'
    elif all_students:
        task = instructor_task.api.submit_rescore_problem_for_all_students(request, course_id, module_state_key)
        response_payload['task'] = 'created'
    else:
        return HttpResponseBadRequest()

    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def list_instructor_tasks(request, course_id):
    """
    List instructor tasks.
    Limited to instructor access.

    Takes either of the following query paremeters
        - (optional) problem_urlname (same format as problem_to_reset in other api methods)
        - (optional) student_email
    """
    course = get_course_with_access(request.user, course_id, 'instructor', depth=None)

    problem_urlname = request.GET.get('problem_urlname', False)
    student_email = request.GET.get('student_email', False)

    if student_email and not problem_urlname:
        return HttpResponseBadRequest()

    if problem_urlname:
        module_state_key = _module_state_key_from_problem_urlname(course_id, problem_urlname)
        if student_email:
            student = User.objects.get(email=student_email)
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key, student)
        else:
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key)
    else:
        tasks = instructor_task.api.get_running_instructor_tasks(course_id)

    def extract_task_features(task):
        FEATURES = ['task_type', 'task_input', 'task_id', 'requester', 'created', 'task_state']
        return dict((feature, str(getattr(task, feature))) for feature in FEATURES)

    response_payload = {
        'tasks': map(extract_task_features, tasks),
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

    rolename = request.GET.get('rolename')

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
@common_exceptions_400
def update_forum_role_membership(request, course_id):
    """
    Modify forum role access.

    Query parameters:
    email is the target users email
    rolename is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
    mode is one of ['allow', 'revoke']
    """
    course = get_course_with_access(request.user, course_id, 'instructor', depth=None)

    email = request.GET.get('email')
    rolename = request.GET.get('rolename')
    mode = request.GET.get('mode')

    if not rolename in [access.FORUM_ROLE_ADMINISTRATOR, access.FORUM_ROLE_MODERATOR, access.FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest()

    try:
        user = User.objects.get(email=email)
        access.update_forum_role_membership(course_id, user, rolename, mode)
    except Role.DoesNotExist:
        return HttpResponseBadRequest("Role does not exist.")

    response_payload = {
        'course_id': course_id,
        'mode':      mode,
        'DONE': 'YES',
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


def _module_state_key_from_problem_urlname(course_id, urlname):
    if urlname[-4:] == ".xml":
        urlname = urlname[:-4]

    urlname = "problem/" + urlname

    (org, course_name, _) = course_id.split("/")
    module_state_key = "i4x://" + org + "/" + course_name + "/" + urlname
    return module_state_key
