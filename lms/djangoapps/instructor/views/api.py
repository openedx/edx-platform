"""
Instructor Dashboard API views

JSON views which the instructor dashboard requests.

Many of these GETs may become PUTs in the future.
"""
from django.views.decorators.http import require_POST

import json
import logging
import re
import requests
from django.conf import settings
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.html import strip_tags
import string  # pylint: disable=W0402
import random
from util.json_request import JsonResponse
from instructor.views.instructor_task_helpers import extract_email_features, extract_task_features

from courseware.access import has_access
from courseware.courses import get_course_with_access, get_course_by_id
from django.contrib.auth.models import User
from django_comment_client.utils import has_forum_access
from django_comment_common.models import (
    Role,
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_COMMUNITY_TA,
)
from edxmako.shortcuts import render_to_response
from courseware.models import StudentModule
from shoppingcart.models import Coupon, CourseRegistrationCode, RegistrationCodeRedemption
from student.models import CourseEnrollment, unique_id_for_user, anonymous_id_for_user
import instructor_task.api
from instructor_task.api_helper import AlreadyRunningError
from instructor_task.models import ReportStore
import instructor.enrollment as enrollment
from instructor.enrollment import (
    enroll_email,
    get_email_params,
    send_beta_role_email,
    unenroll_email
)
from instructor.access import list_with_level, allow_access, revoke_access, update_forum_role
from instructor.offline_gradecalc import student_grades
import instructor_analytics.basic
import instructor_analytics.distributions
import instructor_analytics.csvs
import csv

from submissions import api as sub_api  # installed from the edx-submissions repository

from bulk_email.models import CourseEmail

from .tools import (
    dump_student_extensions,
    dump_module_extensions,
    find_unit,
    get_student_from_identifier,
    handle_dashboard_error,
    parse_datetime,
    set_due_date_extension,
    strip_if_string,
    bulk_email_is_enabled_for_course,
)
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys import InvalidKeyError

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
                    error_response_data['parameters'].append(param)
                    error_response_data['info'][param] = extra

            if len(error_response_data['parameters']) > 0:
                return JsonResponse(error_response_data, status=400)
            else:
                return func(*args, **kwargs)
        return wrapped
    return decorator


def require_post_params(*args, **kwargs):
    """
    Checks for required parameters or renders a 400 error.
    (decorator with arguments)

    Functions like 'require_query_params', but checks for
    POST parameters rather than GET parameters.
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
                if request.POST.get(param, default) == default:
                    error_response_data['parameters'].append(param)
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
        if they are not in the staff group.
    """
    if level not in ['instructor', 'staff']:
        raise ValueError("unrecognized level '{}'".format(level))

    def decorator(func):  # pylint: disable=C0111
        def wrapped(*args, **kwargs):  # pylint: disable=C0111
            request = args[0]
            course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id']))

            if has_access(request.user, level, course):
                return func(*args, **kwargs)
            else:
                return HttpResponseForbidden()
        return wrapped
    return decorator


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(action="enroll or unenroll", identifiers="stringified list of emails and/or usernames")
def students_update_enrollment(request, course_id):
    """
    Enroll or unenroll students by email.
    Requires staff access.

    Query Parameters:
    - action in ['enroll', 'unenroll']
    - identifiers is string containing a list of emails and/or usernames separated by anything split_input_list can handle.
    - auto_enroll is a boolean (defaults to false)
        If auto_enroll is false, students will be allowed to enroll.
        If auto_enroll is true, students will be enrolled as soon as they register.
    - email_students is a boolean (defaults to false)
        If email_students is true, students will be sent email notification
        If email_students is false, students will not be sent email notification

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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    action = request.GET.get('action')
    identifiers_raw = request.GET.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    auto_enroll = request.GET.get('auto_enroll') in ['true', 'True', True]
    email_students = request.GET.get('email_students') in ['true', 'True', True]

    email_params = {}
    if email_students:
        course = get_course_by_id(course_id)
        email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

    results = []
    for identifier in identifiers:
        # First try to get a user object from the identifer
        user = None
        email = None
        try:
            user = get_student_from_identifier(identifier)
        except User.DoesNotExist:
            email = identifier
        else:
            email = user.email

        try:
            # Use django.core.validators.validate_email to check email address
            # validity (obviously, cannot check if email actually /exists/,
            # simply that it is plausibly valid)
            validate_email(email)  # Raises ValidationError if invalid

            if action == 'enroll':
                before, after = enroll_email(course_id, email, auto_enroll, email_students, email_params)
            elif action == 'unenroll':
                before, after = unenroll_email(course_id, email, email_students, email_params)
            else:
                return HttpResponseBadRequest(strip_tags(
                    "Unrecognized action '{}'".format(action)
                ))

        except ValidationError:
            # Flag this email as an error if invalid, but continue checking
            # the remaining in the list
            results.append({
                'identifier': identifier,
                'invalidIdentifier': True,
            })

        except Exception as exc:  # pylint: disable=W0703
            # catch and log any exceptions
            # so that one error doesn't cause a 500.
            log.exception("Error while #{}ing student")
            log.exception(exc)
            results.append({
                'identifier': identifier,
                'error': True,
            })

        else:
            results.append({
                'identifier': identifier,
                'before': before.to_dict(),
                'after': after.to_dict(),
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
    identifiers="stringified list of emails and/or usernames",
    action="add or remove",
)
def bulk_beta_modify_access(request, course_id):
    """
    Enroll or unenroll users in beta testing program.

    Query parameters:
    - identifiers is string containing a list of emails and/or usernames separated by
      anything split_input_list can handle.
    - action is one of ['add', 'remove']
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    action = request.GET.get('action')
    identifiers_raw = request.GET.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    email_students = request.GET.get('email_students') in ['true', 'True', True]
    auto_enroll = request.GET.get('auto_enroll') in ['true', 'True', True]
    results = []
    rolename = 'beta'
    course = get_course_by_id(course_id)

    email_params = {}
    if email_students:
        secure = request.is_secure()
        email_params = get_email_params(course, auto_enroll=auto_enroll, secure=secure)

    for identifier in identifiers:
        try:
            error = False
            user_does_not_exist = False
            user = get_student_from_identifier(identifier)

            if action == 'add':
                allow_access(course, user, rolename)
            elif action == 'remove':
                revoke_access(course, user, rolename)
            else:
                return HttpResponseBadRequest(strip_tags(
                    "Unrecognized action '{}'".format(action)
                ))
        except User.DoesNotExist:
            error = True
            user_does_not_exist = True
        # catch and log any unexpected exceptions
        # so that one error doesn't cause a 500.
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Error while #{}ing student")
            log.exception(exc)
            error = True
        else:
            # If no exception thrown, see if we should send an email
            if email_students:
                send_beta_role_email(action, user, email_params)
            # See if we should autoenroll the student
            if auto_enroll:
                # Check if student is already enrolled
                if not CourseEnrollment.is_enrolled(user, course_id):
                    CourseEnrollment.enroll(user, course_id)

        finally:
            # Tabulate the action result of this email address
            results.append({
                'identifier': identifier,
                'error': error,
                'userDoesNotExist': user_does_not_exist
            })

    response_payload = {
        'action': action,
        'results': results,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@common_exceptions_400
@require_query_params(
    unique_student_identifier="email or username of user to change access",
    rolename="'instructor', 'staff', or 'beta'",
    action="'allow' or 'revoke'"
)
def modify_access(request, course_id):
    """
    Modify staff/instructor access of other user.
    Requires instructor access.

    NOTE: instructors cannot remove their own instructor access.

    Query parameters:
    unique_student_identifer is the target user's username or email
    rolename is one of ['instructor', 'staff', 'beta']
    action is one of ['allow', 'revoke']
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'instructor', course_id, depth=None
    )
    try:
        user = get_student_from_identifier(request.GET.get('unique_student_identifier'))
    except User.DoesNotExist:
        response_payload = {
            'unique_student_identifier': request.GET.get('unique_student_identifier'),
            'userDoesNotExist': True,
        }
        return JsonResponse(response_payload)

    # Check that user is active, because add_users
    # in common/djangoapps/student/roles.py fails
    # silently when we try to add an inactive user.
    if not user.is_active:
        response_payload = {
            'unique_student_identifier': user.username,
            'inactiveUser': True,
        }
        return JsonResponse(response_payload)

    rolename = request.GET.get('rolename')
    action = request.GET.get('action')

    if not rolename in ['instructor', 'staff', 'beta']:
        return HttpResponseBadRequest(strip_tags(
            "unknown rolename '{}'".format(rolename)
        ))

    # disallow instructors from removing their own instructor access.
    if rolename == 'instructor' and user == request.user and action != 'allow':
        response_payload = {
            'unique_student_identifier': user.username,
            'rolename': rolename,
            'action': action,
            'removingSelfAsInstructor': True,
        }
        return JsonResponse(response_payload)

    if action == 'allow':
        allow_access(course, user, rolename)
    elif action == 'revoke':
        revoke_access(course, user, rolename)
    else:
        return HttpResponseBadRequest(strip_tags(
            "unrecognized action '{}'".format(action)
        ))

    response_payload = {
        'unique_student_identifier': user.username,
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'instructor', course_id, depth=None
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
        'course_id': course_id.to_deprecated_string(),
        rolename: map(extract_user_info, list_with_level(
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
    )
    grading_config_summary = instructor_analytics.basic.dump_grading_context(course)

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
        'grading_config_summary': grading_config_summary,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_purchase_transaction(request, course_id, csv=False):  # pylint: disable=W0613, W0621
    """
    return the summary of all purchased transactions for a particular course
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    query_features = [
        'id', 'username', 'email', 'course_id', 'list_price', 'coupon_code',
        'unit_cost', 'purchase_time', 'orderitem_id',
        'order_id',
    ]

    student_data = instructor_analytics.basic.purchase_transactions(course_id, query_features)

    if not csv:
        response_payload = {
            'course_id': course_id.to_deprecated_string(),
            'students': student_data,
            'queried_features': query_features
        }
        return JsonResponse(response_payload)
    else:
        header, datarows = instructor_analytics.csvs.format_dictlist(student_data, query_features)
        return instructor_analytics.csvs.create_csv_response("e-commerce_purchase_transactions.csv", header, datarows)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_students_features(request, course_id, csv=False):  # pylint: disable=W0613, W0621
    """
    Respond with json which contains a summary of all enrolled students profile information.

    Responds with JSON
        {"students": [{-student-info-}, ...]}

    TO DO accept requests for different attribute sets.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    available_features = instructor_analytics.basic.AVAILABLE_FEATURES
    query_features = [
        'id', 'username', 'name', 'email', 'language', 'location',
        'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
        'goals',
    ]

    student_data = instructor_analytics.basic.enrolled_students_features(course_id, query_features)

    # Provide human-friendly and translatable names for these features. These names
    # will be displayed in the table generated in data_download.coffee. It is not (yet)
    # used as the header row in the CSV, but could be in the future.
    query_features_names = {
        'id': _('User ID'),
        'username': _('Username'),
        'name': _('Name'),
        'email': _('Email'),
        'language': _('Language'),
        'location': _('Location'),
        'year_of_birth': _('Birth Year'),
        'gender': _('Gender'),
        'level_of_education': _('Level of Education'),
        'mailing_address': _('Mailing Address'),
        'goals': _('Goals'),
    }

    if not csv:
        response_payload = {
            'course_id': course_id.to_deprecated_string(),
            'students': student_data,
            'students_count': len(student_data),
            'queried_features': query_features,
            'feature_names': query_features_names,
            'available_features': available_features,
        }
        return JsonResponse(response_payload)
    else:
        header, datarows = instructor_analytics.csvs.format_dictlist(student_data, query_features)
        return instructor_analytics.csvs.create_csv_response("enrolled_profiles.csv", header, datarows)


def save_registration_codes(request, course_id, generated_codes_list, group_name):
    """
    recursive function that generate a new code every time and saves in the Course Registration Table
    if validation check passes
    """
    code = random_code_generator()

    # check if the generated code is in the Coupon Table
    matching_coupons = Coupon.objects.filter(code=code, is_active=True)
    if matching_coupons:
        return save_registration_codes(request, course_id, generated_codes_list, group_name)

    course_registration = CourseRegistrationCode(
        code=code, course_id=course_id.to_deprecated_string(),
        transaction_group_name=group_name, created_by=request.user
    )
    try:
        course_registration.save()
        generated_codes_list.append(course_registration)
    except IntegrityError:
        return save_registration_codes(request, course_id, generated_codes_list, group_name)


def registration_codes_csv(file_name, codes_list, csv_type=None):
    """
    Respond with the csv headers and data rows
    given a dict of codes list
    :param file_name:
    :param codes_list:
    :param csv_type:
    """
    # csv headers
    query_features = ['code', 'course_id', 'transaction_group_name', 'created_by', 'redeemed_by']

    registration_codes = instructor_analytics.basic.course_registration_features(query_features, codes_list, csv_type)
    header, data_rows = instructor_analytics.csvs.format_dictlist(registration_codes, query_features)
    return instructor_analytics.csvs.create_csv_response(file_name, header, data_rows)


def random_code_generator():
    """
    generate a random alphanumeric code of length defined in
    REGISTRATION_CODE_LENGTH settings
    """
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    code_length = getattr(settings, 'REGISTRATION_CODE_LENGTH', 8)
    return string.join((random.choice(chars) for _ in range(code_length)), '')


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def get_registration_codes(request, course_id):  # pylint: disable=W0613
    """
    Respond with csv which contains a summary of all Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    #filter all the  course registration codes
    registration_codes = CourseRegistrationCode.objects.filter(course_id=course_id).order_by('transaction_group_name')

    group_name = request.POST['download_transaction_group_name']
    if group_name:
        registration_codes = registration_codes.filter(transaction_group_name=group_name)

    csv_type = 'download'
    return registration_codes_csv("Registration_Codes.csv", registration_codes, csv_type)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def generate_registration_codes(request, course_id):
    """
    Respond with csv which contains a summary of all Generated Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course_registration_codes = []

    # covert the course registration code number into integer
    try:
        course_code_number = int(request.POST['course_registration_code_number'])
    except ValueError:
        course_code_number = int(float(request.POST['course_registration_code_number']))

    group_name = request.POST['transaction_group_name']

    for _ in range(course_code_number):  # pylint: disable=W0621
        save_registration_codes(request, course_id, course_registration_codes, group_name)

    return registration_codes_csv("Registration_Codes.csv", course_registration_codes)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def active_registration_codes(request, course_id):  # pylint: disable=W0613
    """
    Respond with csv which contains a summary of all Active Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # find all the registration codes in this course
    registration_codes_list = CourseRegistrationCode.objects.filter(course_id=course_id).order_by('transaction_group_name')

    group_name = request.POST['active_transaction_group_name']
    if group_name:
        registration_codes_list = registration_codes_list.filter(transaction_group_name=group_name)
    # find the redeemed registration codes if any exist in the db
    code_redemption_set = RegistrationCodeRedemption.objects.select_related('registration_code').filter(registration_code__course_id=course_id)
    if code_redemption_set.exists():
        redeemed_registration_codes = [code.registration_code.code for code in code_redemption_set]
        # exclude the redeemed registration codes from the registration codes list and you will get
        # all the registration codes that are active
        registration_codes_list = registration_codes_list.exclude(code__in=redeemed_registration_codes)

    return registration_codes_csv("Active_Registration_Codes.csv", registration_codes_list)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def spent_registration_codes(request, course_id):  # pylint: disable=W0613
    """
    Respond with csv which contains a summary of all Spent(used) Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # find the redeemed registration codes if any exist in the db
    code_redemption_set = RegistrationCodeRedemption.objects.select_related('registration_code').filter(registration_code__course_id=course_id)
    spent_codes_list = []
    if code_redemption_set.exists():
        redeemed_registration_codes = [code.registration_code.code for code in code_redemption_set]
        # filter the Registration Codes by course id and the redeemed codes and
        # you will get a list of all the spent(Redeemed) Registration Codes
        spent_codes_list = CourseRegistrationCode.objects.filter(course_id=course_id, code__in=redeemed_registration_codes).order_by('transaction_group_name')

        group_name = request.POST['spent_transaction_group_name']
        if group_name:
            spent_codes_list = spent_codes_list.filter(transaction_group_name=group_name)  # pylint:  disable=E1103

    csv_type = 'spent'
    return registration_codes_csv("Spent_Registration_Codes.csv", spent_codes_list, csv_type)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_anon_ids(request, course_id):  # pylint: disable=W0613
    """
    Respond with 2-column CSV output of user-id, anonymized-user-id
    """
    # TODO: the User.objects query and CSV generation here could be
    # centralized into instructor_analytics. Currently instructor_analytics
    # has similar functionality but not quite what's needed.
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    def csv_response(filename, header, rows):
        """Returns a CSV http response for the given header and rows (excel/utf-8)."""
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(unicode(filename).encode('utf-8'))
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
    header = ['User ID', 'Anonymized User ID', 'Course Specific Anonymized User ID']
    rows = [[s.id, unique_id_for_user(s, save=False), anonymous_id_for_user(s, course_id, save=False)] for s in students]
    return csv_response(course_id.to_deprecated_string().replace('/', '-') + '-anon-ids.csv', header, rows)


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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    feature = request.GET.get('feature')
    # alternate notations of None
    if feature in (None, 'null', ''):
        feature = None
    else:
        feature = str(feature)

    available_features = instructor_analytics.distributions.AVAILABLE_PROFILE_FEATURES
    # allow None so that requests for no feature can list available features
    if not feature in available_features + (None,):
        return HttpResponseBadRequest(strip_tags(
            "feature '{}' not available.".format(feature)
        ))

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
        'queried_feature': feature,
        'available_features': available_features,
        'feature_display_names': instructor_analytics.distributions.DISPLAY_NAMES,
    }

    p_dist = None
    if not feature is None:
        p_dist = instructor_analytics.distributions.profile_distribution(course_id, feature)
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = get_student_from_identifier(request.GET.get('unique_student_identifier'))

    progress_url = reverse('student_progress', kwargs={'course_id': course_id.to_deprecated_string(), 'student_id': user.id})

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
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
        if not has_access(request.user, 'instructor', course):
            return HttpResponseForbidden("Requires instructor access.")

    try:
        module_state_key = course_id.make_usage_key_from_deprecated_string(problem_to_reset)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student:
        try:
            enrollment.reset_student_attempts(course_id, student, module_state_key, delete_module=delete_module)
        except StudentModule.DoesNotExist:
            return HttpResponseBadRequest(_("Module does not exist."))
        except sub_api.SubmissionError:
            # Trust the submissions API to log the error
            error_msg = _("An error occurred while deleting the score.")
            return HttpResponse(error_msg, status=500)
        response_payload['student'] = student_identifier
    elif all_students:
        instructor_task.api.submit_reset_problem_attempts_for_all_students(request, module_state_key)
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
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

    try:
        module_state_key = course_id.make_usage_key_from_deprecated_string(problem_to_reset)
    except InvalidKeyError:
        return HttpResponseBadRequest("Unable to parse problem id")

    response_payload = {}
    response_payload['problem_to_reset'] = problem_to_reset

    if student:
        response_payload['student'] = student_identifier
        instructor_task.api.submit_rescore_problem_for_student(request, module_state_key, student)
        response_payload['task'] = 'created'
    elif all_students:
        instructor_task.api.submit_rescore_problem_for_all_students(request, module_state_key)
        response_payload['task'] = 'created'
    else:
        return HttpResponseBadRequest()

    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_background_email_tasks(request, course_id):  # pylint: disable=unused-argument
    """
    List background email tasks.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    task_type = 'bulk_course_email'
    # Specifying for the history of a single task type
    tasks = instructor_task.api.get_instructor_task_history(course_id, task_type=task_type)

    response_payload = {
        'tasks': map(extract_task_features, tasks),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_email_content(request, course_id):  # pylint: disable=unused-argument
    """
    List the content of bulk emails sent
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    task_type = 'bulk_course_email'
    # First get tasks list of bulk emails sent
    emails = instructor_task.api.get_instructor_task_history(course_id, task_type=task_type)

    response_payload = {
        'emails': map(extract_email_features, emails),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_instructor_tasks(request, course_id):
    """
    List instructor tasks.

    Takes optional query paremeters.
        - With no arguments, lists running tasks.
        - `problem_location_str` lists task history for problem
        - `problem_location_str` and `unique_student_identifier` lists task
            history for problem AND student (intersection)
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    problem_location_str = strip_if_string(request.GET.get('problem_location_str', False))
    student = request.GET.get('unique_student_identifier', None)
    if student is not None:
        student = get_student_from_identifier(student)

    if student and not problem_location_str:
        return HttpResponseBadRequest(
            "unique_student_identifier must accompany problem_location_str"
        )

    if problem_location_str:
        try:
            module_state_key = course_id.make_usage_key_from_deprecated_string(problem_location_str)
        except InvalidKeyError:
            return HttpResponseBadRequest()
        if student:
            # Specifying for a single student's history on this problem
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key, student)
        else:
            # Specifying for single problem's history
            tasks = instructor_task.api.get_instructor_task_history(course_id, module_state_key)
    else:
        # If no problem or student, just get currently running tasks
        tasks = instructor_task.api.get_running_instructor_tasks(course_id)

    response_payload = {
        'tasks': map(extract_task_features, tasks),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_report_downloads(_request, course_id):
    """
    List grade CSV files that are available for download for this course.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    report_store = ReportStore.from_config()

    response_payload = {
        'downloads': [
            dict(name=name, url=url, link='<a href="{}">{}</a>'.format(url, name))
            for name, url in report_store.links_for(course_id)
        ]
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def calculate_grades_csv(request, course_id):
    """
    AlreadyRunningError is raised if the course's grades are already being updated.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_calculate_grades_csv(request, course_key)
        success_status = _("Your grade report is being generated! You can view the status of the generation task in the 'Pending Instructor Tasks' section.")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("A grade report generation task is already in progress. Check the 'Pending Instructor Tasks' table for the status of the task. When completed, the report will be available for download in the table below.")
        return JsonResponse({
            "status": already_running_status
        })


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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_id)
    has_instructor_access = has_access(request.user, 'instructor', course)
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
        return HttpResponseBadRequest(strip_tags(
            "Unrecognized rolename '{}'.".format(rolename)
        ))

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
        'course_id': course_id.to_deprecated_string(),
        rolename: map(extract_user_info, users),
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params(send_to="sending to whom", subject="subject line", message="message text")
def send_email(request, course_id):
    """
    Send an email to self, staff, or everyone involved in a course.
    Query Parameters:
    - 'send_to' specifies what group the email should be sent to
       Options are defined by the CourseEmail model in
       lms/djangoapps/bulk_email/models.py
    - 'subject' specifies email's subject
    - 'message' specifies email's content
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    if not bulk_email_is_enabled_for_course(course_id):
        return HttpResponseForbidden("Email is not enabled for this course.")

    send_to = request.POST.get("send_to")
    subject = request.POST.get("subject")
    message = request.POST.get("message")

    # Create the CourseEmail object.  This is saved immediately, so that
    # any transaction that has been pending up to this point will also be
    # committed.
    email = CourseEmail.create(course_id, request.user, send_to, subject, message)

    # Submit the task, so that the correct InstructorTask object gets created (for monitoring purposes)
    instructor_task.api.submit_bulk_course_email(request, course_id, email.id)  # pylint: disable=E1101

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
        'success': True,
    }
    return JsonResponse(response_payload)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params(
    unique_student_identifier="email or username of user to change access",
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_id)
    has_instructor_access = has_access(request.user, 'instructor', course)
    has_forum_admin = has_forum_access(
        request.user, course_id, FORUM_ROLE_ADMINISTRATOR
    )

    unique_student_identifier = request.GET.get('unique_student_identifier')
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
        return HttpResponseBadRequest(strip_tags(
            "Unrecognized rolename '{}'.".format(rolename)
        ))

    user = get_student_from_identifier(unique_student_identifier)
    target_is_instructor = has_access(user, 'instructor', course)
    # cannot revoke instructor
    if target_is_instructor and action == 'revoke' and rolename == FORUM_ROLE_ADMINISTRATOR:
        return HttpResponseBadRequest("Cannot revoke instructor forum admin privileges.")

    try:
        update_forum_role(course_id, user, rolename, action)
    except Role.DoesNotExist:
        return HttpResponseBadRequest("Role does not exist.")

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    analytics_name = request.GET.get('aname')

    # abort if misconfigured
    if not (hasattr(settings, 'ANALYTICS_SERVER_URL') and hasattr(settings, 'ANALYTICS_API_KEY')):
        return HttpResponse("Analytics service not configured.", status=501)

    url = "{}get?aname={}&course_id={}&apikey={}".format(
        settings.ANALYTICS_SERVER_URL,
        analytics_name,
        course_id.to_deprecated_string(),
        settings.ANALYTICS_API_KEY,
    )

    try:
        res = requests.get(url)
    except Exception:  # pylint: disable=broad-except
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


def _display_unit(unit):
    """
    Gets string for displaying unit to user.
    """
    name = getattr(unit, 'display_name', None)
    if name:
        return u'{0} ({1})'.format(name, unit.location.to_deprecated_string())
    else:
        return unit.location.to_deprecated_string()


@handle_dashboard_error
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params('student', 'url', 'due_datetime')
def change_due_date(request, course_id):
    """
    Grants a due date extension to a student for a particular unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    student = get_student_from_identifier(request.GET.get('student'))
    unit = find_unit(course, request.GET.get('url'))
    due_date = parse_datetime(request.GET.get('due_datetime'))
    set_due_date_extension(course, unit, student, due_date)

    return JsonResponse(_(
        'Successfully changed due date for student {0} for {1} '
        'to {2}').format(student.profile.name, _display_unit(unit),
                         due_date.strftime('%Y-%m-%d %H:%M')))


@handle_dashboard_error
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params('student', 'url')
def reset_due_date(request, course_id):
    """
    Rescinds a due date extension for a student on a particular unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    student = get_student_from_identifier(request.GET.get('student'))
    unit = find_unit(course, request.GET.get('url'))
    set_due_date_extension(course, unit, student, None)

    return JsonResponse(_(
        'Successfully reset due date for student {0} for {1} '
        'to {2}').format(student.profile.name, _display_unit(unit),
                         unit.due.strftime('%Y-%m-%d %H:%M')))


@handle_dashboard_error
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params('url')
def show_unit_extensions(request, course_id):
    """
    Shows all of the students which have due date extensions for the given unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    unit = find_unit(course, request.GET.get('url'))
    return JsonResponse(dump_module_extensions(course, unit))


@handle_dashboard_error
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_query_params('student')
def show_student_extensions(request, course_id):
    """
    Shows all of the due date extensions granted to a particular student in a
    particular course.
    """
    student = get_student_from_identifier(request.GET.get('student'))
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    return JsonResponse(dump_student_extensions(course, student))


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


#---- Gradebook (shown to small courses only) ----
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def spoc_gradebook(request, course_id):
    """
    Show the gradebook for this course:
    - Only shown for courses with enrollment < settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    - Only displayed to course staff
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, 'staff', course_key, depth=None)

    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1
    ).order_by('username').select_related("profile")

    # possible extension: implement pagination to show to large courses

    student_info = [
        {
            'username': student.username,
            'id': student.id,
            'email': student.email,
            'grade_summary': student_grades(student, request, course),
            'realname': student.profile.name,
        }
        for student in enrolled_students
    ]

    return render_to_response('courseware/gradebook.html', {
        'students': student_info,
        'course': course,
        'course_id': course_key,
        # Checked above
        'staff_access': True,
        'ordered_grades': sorted(course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True),
    })
