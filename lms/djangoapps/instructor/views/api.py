"""
Instructor Dashboard API views

JSON views which the instructor dashboard requests.

Many of these GETs may become PUTs in the future.
"""

import re
import logging
import requests
from collections import OrderedDict
from django.conf import settings
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from util.json_request import JsonResponse

from courseware.access import has_access
from courseware.courses import get_course_with_access, get_course_by_id
from django.contrib.auth.models import User
from django_comment_client.utils import has_forum_access
from django_comment_common.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)

from courseware.models import StudentModule
from student.models import unique_id_for_user
import instructor_task.api
from instructor_task.api_helper import AlreadyRunningError
import instructor.enrollment as enrollment
from instructor.enrollment import enroll_email, unenroll_email
from instructor.views.tools import strip_if_string, get_student_from_identifier
import instructor.access as access
import analytics.basic
import analytics.distributions
import analytics.csvs
import csv

log = logging.getLogger(__name__)


def common_exceptions_400(func):
    """
    Catches common exceptions and renders matching 400 errors.
    (decorator without arguments)
    """
    def wrapped(request, *args, **kwargs):  # pylint: disable=C0111
        use_json = (request.is_ajax() or
                    request.META.get("HTTP_ACCEPT", "").startswith("application/json"))
        try:
            return func(request, *args, **kwargs)
        except User.DoesNotExist:
            message = _("User does not exist.")
            if use_json:
                return JsonResponse({"error": message}, 400)
            else:
                return HttpResponseBadRequest(message)
        except AlreadyRunningError:
            message = _("Task is already running.")
            if use_json:
                return JsonResponse({"error": message}, 400)
            else:
                return HttpResponseBadRequest(message)
    return wrapped


def require_query_params(*args, **kwargs):
    """
    Checks for required paremters or renders a 400 error.
    (decorator with arguments)

    `args` is a *list of required GET parameter names.
    `kwargs` is a **dict of required GET parameter names
        to string explanations of the parameter
    """
    required_params = []
    required_params += [(arg, None) for arg in args]
    required_params += [(key, kwargs[key]) for key in kwargs]
    # required_params = e.g. [('action', 'enroll or unenroll'), ['emails', None]]

    def decorator(func):  # pylint: disable=C0111
        def wrapped(*args, **kwargs):  # pylint: disable=C0111
            request = args[0]

            error_response_data = {
                'error': 'Missing required query parameter(s)',
                'parameters': [],
                'info': {},
            }

            for (param, extra) in required_params:
                default = object()
                if request.GET.get(param, default) == default:
                    error_response_data['parameters'] += [param]
                    error_response_data['info'][param] = extra

            if len(error_response_data['parameters']) > 0:
                return JsonResponse(error_response_data, status=400)
            else:
                return func(*args, **kwargs)
        return wrapped
    return decorator


def require_level(level):
    """
    Decorator with argument that requires an access level of the requesting
    user. If the requirement is not satisfied, returns an
    HttpResponseForbidden (403).

    Assumes that request is in args[0].
    Assumes that course_id is in kwargs['course_id'].

    `level` is in ['instructor', 'staff']
    if `level` is 'staff', instructors will also be allowed, even
        if they are not int he staff group.
    """
    if level not in ['instructor', 'staff']:
        raise ValueError("unrecognized level '{}'".format(level))

    def decorator(func):  # pylint: disable=C0111
        def wrapped(*args, **kwargs):  # pylint: disable=C0111
            request = args[0]
            course = get_course_by_id(kwargs['course_id'])

            if has_access(request.user, course, level):
                return func(*args, **kwargs)
            else:
                return HttpResponseForbidden()
        return wrapped
    return decorator


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(action="enroll or unenroll", emails="stringified list of emails")
def students_update_enrollment(request, course_id):
    """
    Enroll or unenroll students by email.
    Requires staff access.

    Query Parameters:
    - action in ['enroll', 'unenroll']
    - emails is string containing a list of emails separated by anything split_input_list can handle.
    - auto_enroll is a boolean (defaults to false)
        If auto_enroll is false, students will be allowed to enroll.
        If auto_enroll is true, students will be enroled as soon as they register.

    Returns an analog to this JSON structure: {
        "action": "enroll",
        "auto_enroll": false,
        "results": [
            {
                "email": "testemail@test.org",
                "before": {
                    "enrollment": false,
                    "auto_enroll": false,
                    "user": true,
                    "allowed": false
                },
                "after": {
                    "enrollment": true,
                    "auto_enroll": false,
                    "user": true,
                    "allowed": false
                }
            }
        ]
    }
    """
    action = request.GET.get('action')
    emails_raw = request.GET.get('emails')
    emails = _split_input_list(emails_raw)
    auto_enroll = request.GET.get('auto_enroll') in ['true', 'True', True]

    results = []
    for email in emails:
        try:
            if action == 'enroll':
                before, after = enroll_email(course_id, email, auto_enroll)
            elif action == 'unenroll':
                before, after = unenroll_email(course_id, email)
            else:
                return HttpResponseBadRequest("Unrecognized action '{}'".format(action))

            results.append({
                'email': email,
                'before': before.to_dict(),
                'after': after.to_dict(),
            })
        # catch and log any exceptions
        # so that one error doesn't cause a 500.
        except Exception as exc:  # pylint: disable=W0703
            log.exception("Error while #{}ing student")
            log.exception(exc)
            results.append({
                'email': email,
                'error': True,
            })

    response_payload = {
        'action': action,
        'results': results,
        'auto_enroll': auto_enroll,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@common_exceptions_400
@require_query_params(
    email="user email",
    rolename="'instructor', 'staff', or 'beta'",
    action="'allow' or 'revoke'"
)
def modify_access(request, course_id):
    """
    Modify staff/instructor access of other user.
    Requires instructor access.

    NOTE: instructors cannot remove their own instructor access.

    Query parameters:
    email is the target users email
    rolename is one of ['instructor', 'staff', 'beta']
    action is one of ['allow', 'revoke']
    """
    course = get_course_with_access(
        request.user, course_id, 'instructor', depth=None
    )

    email = strip_if_string(request.GET.get('email'))
    rolename = request.GET.get('rolename')
    action = request.GET.get('action')

    if not rolename in ['instructor', 'staff', 'beta']:
        return HttpResponseBadRequest(
            "unknown rolename '{}'".format(rolename)
        )

    user = User.objects.get(email=email)

    # disallow instructors from removing their own instructor access.
    if rolename == 'instructor' and user == request.user and action != 'allow':
        return HttpResponseBadRequest(
            "An instructor cannot remove their own instructor access."
        )

    if action == 'allow':
        access.allow_access(course, user, rolename)
    elif action == 'revoke':
        access.revoke_access(course, user, rolename)
    else:
        return HttpResponseBadRequest("unrecognized action '{}'".format(action))

    response_payload = {
        'email': email,
        'rolename': rolename,
        'action': action,
        'success': 'yes',
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@require_query_params(rolename="'instructor', 'staff', or 'beta'")
def list_course_role_members(request, course_id):
    """
    List instructors and staff.
    Requires instructor access.

    rolename is one of ['instructor', 'staff', 'beta']

    Returns JSON of the form {
        "course_id": "some/course/id",
        "staff": [
            {
                "username": "staff1",
                "email": "staff1@example.org",
                "first_name": "Joe",
                "last_name": "Shmoe",
            }
        ]
    }
    """
    course = get_course_with_access(
        request.user, course_id, 'instructor', depth=None
    )

    rolename = request.GET.get('rolename')

    if not rolename in ['instructor', 'staff', 'beta']:
        return HttpResponseBadRequest()

    def extract_user_info(user):
        """ convert user into dicts for json view """
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    response_payload = {
        'course_id': course_id,
        rolename: map(extract_user_info, access.list_with_level(
            course, rolename
        )),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_grading_config(request, course_id):
    """
    Respond with json which contains a html formatted grade summary.
    """
    course = get_course_with_access(
        request.user, course_id, 'staff', depth=None
    )
    grading_config_summary = analytics.basic.dump_grading_context(course)

    response_payload = {
        'course_id': course_id,
        'grading_config_summary': grading_config_summary,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_students_features(request, course_id, csv=False):  # pylint: disable=W0613
    """
    Respond with json which contains a summary of all enrolled students profile information.

    Responds with JSON
        {"students": [{-student-info-}, ...]}

    TO DO accept requests for different attribute sets.
    """
    available_features = analytics.basic.AVAILABLE_FEATURES
    query_features = ['username', 'name', 'email', 'language', 'location', 'year_of_birth', 'gender',
                      'level_of_education', 'mailing_address', 'goals']

    student_data = analytics.basic.enrolled_students_features(course_id, query_features)

    if not csv:
        response_payload = {
            'course_id': course_id,
            'students': student_data,
            'students_count': len(student_data),
            'queried_features': query_features,
            'available_features': available_features,
        }
        return JsonResponse(response_payload)
    else:
        header, datarows = analytics.csvs.format_dictlist(student_data, query_features)
        return analytics.csvs.create_csv_response("enrolled_profiles.csv", header, datarows)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_anon_ids(request, course_id):  # pylint: disable=W0613
    """
    Respond with 2-column CSV output of user-id, anonymized-user-id
    """
    # TODO: the User.objects query and CSV generation here could be
    # centralized into analytics. Currently analytics has similar functionality
    # but not quite what's needed.
    def csv_response(filename, header, rows):
        """Returns a CSV http response for the given header and rows (excel/utf-8)."""
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        # In practice, there should not be non-ascii data in this query,
        # but trying to do the right thing anyway.
        encoded = [unicode(s).encode('utf-8') for s in header]
        writer.writerow(encoded)
        for row in rows:
            encoded = [unicode(s).encode('utf-8') for s in row]
            writer.writerow(encoded)
        return response

    students = User.objects.filter(
        courseenrollment__course_id=course_id,
    ).order_by('id')
    header =['User ID', 'Anonymized user ID']
    rows = [[s.id, unique_id_for_user(s)] for s in students]
    return csv_response(course_id.replace('/', '-') + '-anon-ids.csv', header, rows)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_distribution(request, course_id):
    """
    Respond with json of the distribution of students over selected features which have choices.

    Ask for a feature through the `feature` query parameter.
    If no `feature` is supplied, will return response with an
        empty response['feature_results'] object.
    A list of available will be available in the response['available_features']
    """
    feature = request.GET.get('feature')
    # alternate notations of None
    if feature in (None, 'null', ''):
        feature = None
    else:
        feature = str(feature)

    available_features = analytics.distributions.AVAILABLE_PROFILE_FEATURES
    # allow None so that requests for no feature can list available features
    if not feature in available_features + (None,):
        return HttpResponseBadRequest(
            "feature '{}' not available.".format(feature)
        )

    response_payload = {
        'course_id': course_id,
        'queried_feature': feature,
        'available_features': available_features,
        'feature_display_names': analytics.distributions.DISPLAY_NAMES,
    }

    p_dist = None
    if not feature is None:
        p_dist = analytics.distributions.profile_distribution(course_id, feature)
        response_payload['feature_results'] = {
            'feature': p_dist.feature,
            'feature_display_name': p_dist.feature_display_name,
            'data': p_dist.data,
            'type': p_dist.type,
        }

        if p_dist.type == 'EASY_CHOICE':
            response_payload['feature_results']['choices_display_names'] = p_dist.choices_display_names

    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@common_exceptions_400
@require_level('staff')
@require_query_params(
    unique_student_identifier="email or username of student for whom to get progress url"
)
def get_student_progress_url(request, course_id):
    """
    Get the progress url of a student.
    Limited to staff access.

    Takes query paremeter unique_student_identifier and if the student exists
    returns e.g. {
        'progress_url': '/../...'
    }
    """
    user = get_student_from_identifier(request.GET.get('unique_student_identifier'))

    progress_url = reverse('student_progress', kwargs={'course_id': course_id, 'student_id': user.id})

    response_payload = {
        'course_id': course_id,
        'progress_url': progress_url,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(
    problem_to_reset="problem urlname to reset"
)
@common_exceptions_400
def reset_student_attempts(request, course_id):
    """

    Resets a students attempts counter or starts a task to reset all students
    attempts counters. Optionally deletes student state for a problem. Limited
    to staff access. Some sub-methods limited to instructor access.

    Takes some of the following query paremeters
        - problem_to_reset is a urlname of a problem
        - unique_student_identifier is an email or username
        - all_students is a boolean
            requires instructor access
            mutually exclusive with delete_module
            mutually exclusive with delete_module
        - delete_module is a boolean
            requires instructor access
            mutually exclusive with all_students
    """
    course = get_course_with_access(
        request.user, course_id, 'staff', depth=None
    )

    problem_to_reset = strip_if_string(request.GET.get('problem_to_reset'))
    student_identifier = request.GET.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)
    all_students = request.GET.get('all_students', False) in ['true', 'True', True]
    delete_module = request.GET.get('delete_module', False) in ['true', 'True', True]

    # parameter combinations
    if all_students and student:
        return HttpResponseBadRequest(
            "all_students and unique_student_identifier are mutually exclusive."
        )
    if all_students and delete_module:
        return HttpResponseBadRequest(
            "all_students and delete_module are mutually exclusive."
        )

    # instructor authorization
    if all_students or delete_module:
        if not has_access(request.user, course, 'instructor'):
            return HttpResponseForbidden("Requires instructor access.")

    module_state_key = _msk_from_problem_urlname(course_id, problem_to_reset)

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student:
        try:
            enrollment.reset_student_attempts(course_id, student, module_state_key, delete_module=delete_module)
        except StudentModule.DoesNotExist:
            return HttpResponseBadRequest("Module does not exist.")
        response_payload['student'] = student_identifier
    elif all_students:
        instructor_task.api.submit_reset_problem_attempts_for_all_students(request, course_id, module_state_key)
        response_payload['task'] = 'created'
        response_payload['student'] = 'All Students'
    else:
        return HttpResponseBadRequest()

    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@require_query_params(problem_to_reset="problem urlname to reset")
@common_exceptions_400
def rescore_problem(request, course_id):
    """
    Starts a background process a students attempts counter. Optionally deletes student state for a problem.
    Limited to instructor access.

    Takes either of the following query paremeters
        - problem_to_reset is a urlname of a problem
        - unique_student_identifier is an email or username
        - all_students is a boolean

    all_students and unique_student_identifier cannot both be present.
    """
    problem_to_reset = strip_if_string(request.GET.get('problem_to_reset'))
    student_identifier = request.GET.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)

    all_students = request.GET.get('all_students') in ['true', 'True', True]

    if not (problem_to_reset and (all_students or student)):
        return HttpResponseBadRequest("Missing query parameters.")

    if all_students and student:
        return HttpResponseBadRequest(
            "Cannot rescore with all_students and unique_student_identifier."
        )

    module_state_key = _msk_from_problem_urlname(course_id, problem_to_reset)

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student:
        response_payload['student'] = student_identifier
        instructor_task.api.submit_rescore_problem_for_student(request, course_id, module_state_key, student)
        response_payload['task'] = 'created'
    elif all_students:
        instructor_task.api.submit_rescore_problem_for_all_students(request, course_id, module_state_key)
        response_payload['task'] = 'created'
    else:
        return HttpResponseBadRequest()

    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
def list_instructor_tasks(request, course_id):
    """
    List instructor tasks.
    Limited to instructor access.

    Takes optional query paremeters.
        - With no arguments, lists running tasks.
        - `problem_urlname` lists task history for problem
        - `problem_urlname` and `unique_student_identifier` lists task
            history for problem AND student (intersection)
    """
    problem_urlname = strip_if_string(request.GET.get('problem_urlname', False))
    student = request.GET.get('unique_student_identifier', None)
    if student is not None:
        student = get_student_from_identifier(student)

    if student and not problem_urlname:
        return HttpResponseBadRequest(
            "unique_student_identifier must accompany problem_urlname"
        )

    if problem_urlname:
        module_state_key = _msk_from_problem_urlname(course_id, problem_urlname)
        if student:
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key, student)
        else:
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key)
    else:
        tasks = instructor_task.api.get_running_instructor_tasks(course_id)

    def extract_task_features(task):
        """ Convert task to dict for json rendering """
        features = ['task_type', 'task_input', 'task_id', 'requester', 'created', 'task_state']
        return dict((feature, str(getattr(task, feature))) for feature in features)

    response_payload = {
        'tasks': map(extract_task_features, tasks),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params('rolename')
def list_forum_members(request, course_id):
    """
    Lists forum members of a certain rolename.
    Limited to staff access.

    The requesting user must be at least staff.
    Staff forum admins can access all roles EXCEPT for FORUM_ROLE_ADMINISTRATOR
        which is limited to instructors.

    Takes query parameter `rolename`.
    """
    course = get_course_by_id(course_id)
    has_instructor_access = has_access(request.user, course, 'instructor')
    has_forum_admin = has_forum_access(
        request.user, course_id, FORUM_ROLE_ADMINISTRATOR
    )

    rolename = request.GET.get('rolename')

    # default roles require either (staff & forum admin) or (instructor)
    if not (has_forum_admin or has_instructor_access):
        return HttpResponseBadRequest(
            "Operation requires staff & forum admin or instructor access"
        )

    # EXCEPT FORUM_ROLE_ADMINISTRATOR requires (instructor)
    if rolename == FORUM_ROLE_ADMINISTRATOR and not has_instructor_access:
        return HttpResponseBadRequest("Operation requires instructor access.")

    # filter out unsupported for roles
    if not rolename in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest("Unrecognized rolename '{}'.".format(rolename))

    try:
        role = Role.objects.get(name=rolename, course_id=course_id)
        users = role.users.all().order_by('username')
    except Role.DoesNotExist:
        users = []

    def extract_user_info(user):
        """ Convert user to dict for json rendering. """
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    response_payload = {
        'course_id': course_id,
        rolename: map(extract_user_info, users),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(
    email="the target users email",
    rolename="the forum role",
    action="'allow' or 'revoke'",
)
@common_exceptions_400
def update_forum_role_membership(request, course_id):
    """
    Modify user's forum role.

    The requesting user must be at least staff.
    Staff forum admins can access all roles EXCEPT for FORUM_ROLE_ADMINISTRATOR
        which is limited to instructors.
    No one can revoke an instructors FORUM_ROLE_ADMINISTRATOR status.

    Query parameters:
    - `email` is the target users email
    - `rolename` is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
    - `action` is one of ['allow', 'revoke']
    """
    course = get_course_by_id(course_id)
    has_instructor_access = has_access(request.user, course, 'instructor')
    has_forum_admin = has_forum_access(
        request.user, course_id, FORUM_ROLE_ADMINISTRATOR
    )

    email = strip_if_string(request.GET.get('email'))
    rolename = request.GET.get('rolename')
    action = request.GET.get('action')

    # default roles require either (staff & forum admin) or (instructor)
    if not (has_forum_admin or has_instructor_access):
        return HttpResponseBadRequest(
            "Operation requires staff & forum admin or instructor access"
        )

    # EXCEPT FORUM_ROLE_ADMINISTRATOR requires (instructor)
    if rolename == FORUM_ROLE_ADMINISTRATOR and not has_instructor_access:
        return HttpResponseBadRequest("Operation requires instructor access.")

    if not rolename in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest("Unrecognized rolename '{}'.".format(rolename))

    user = User.objects.get(email=email)
    target_is_instructor = has_access(user, course, 'instructor')
    # cannot revoke instructor
    if target_is_instructor and action == 'revoke' and rolename == FORUM_ROLE_ADMINISTRATOR:
        return HttpResponseBadRequest("Cannot revoke instructor forum admin privelages.")

    try:
        access.update_forum_role_membership(course_id, user, rolename, action)
    except Role.DoesNotExist:
        return HttpResponseBadRequest("Role does not exist.")

    response_payload = {
        'course_id': course_id,
        'action': action,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(
    aname="name of analytic to query",
)
@common_exceptions_400
def proxy_legacy_analytics(request, course_id):
    """
    Proxies to the analytics cron job server.

    `aname` is a query parameter specifying which analytic to query.
    """
    analytics_name = request.GET.get('aname')

    # abort if misconfigured
    if not (hasattr(settings, 'ANALYTICS_SERVER_URL') and hasattr(settings, 'ANALYTICS_API_KEY')):
        return HttpResponse("Analytics service not configured.", status=501)

    url = "{}get?aname={}&course_id={}&apikey={}".format(
        settings.ANALYTICS_SERVER_URL,
        analytics_name,
        course_id,
        settings.ANALYTICS_API_KEY,
    )

    try:
        res = requests.get(url)
    except Exception:
        log.exception("Error requesting from analytics server at %s", url)
        return HttpResponse("Error requesting from analytics server.", status=500)

    if res.status_code is 200:
        # return the successful request content
        return HttpResponse(res.content, content_type="application/json")
    elif res.status_code is 404:
        # forward the 404 and content
        return HttpResponse(res.content, content_type="application/json", status=404)
    else:
        # 500 on all other unexpected status codes.
        log.error(
            "Error fetching {}, code: {}, msg: {}".format(
                url, res.status_code, res.content
            )
        )
        return HttpResponse(
            "Error from analytics server ({}).".format(res.status_code),
            status=500
        )


def _split_input_list(str_list):
    """
    Separate out individual student email from the comma, or space separated string.

    e.g.
    in: "Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed"
    out: ['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus', 'ut@lacinia.Sed']

    `str_list` is a string coming from an input text area
    returns a list of separated values
    """

    new_list = re.split(r'[\n\r\s,]', str_list)
    new_list = [s.strip() for s in new_list]
    new_list = [s for s in new_list if s != '']

    return new_list


def _msk_from_problem_urlname(course_id, urlname):
    """
    Convert a 'problem urlname' (name that instructor's input into dashboard)
    to a module state key (db field)
    """
    if urlname.endswith(".xml"):
        urlname = urlname[:-4]

    # Combined open ended problems also have state that can be deleted.  However,
    # appending "problem" will only allow capa problems to be reset.
    # Get around this for combinedopenended problems.
    if "combinedopenended" not in urlname:
        urlname = "problem/" + urlname

    (org, course_name, __) = course_id.split("/")
    module_state_key = "i4x://" + org + "/" + course_name + "/" + urlname
    return module_state_key
