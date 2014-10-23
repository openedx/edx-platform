"""
Instructor Dashboard API views

JSON views which the instructor dashboard requests.

Many of these GETs may become PUTs in the future.
"""
import StringIO
import json
import logging
import re
import time
import requests
from django.conf import settings
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control
from django.core.exceptions import ValidationError
from django.core.mail.message import EmailMessage
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.utils.html import strip_tags
import string  # pylint: disable=deprecated-module
import random
import urllib
from util.json_request import JsonResponse
from instructor.views.instructor_task_helpers import extract_email_features, extract_task_features

from microsite_configuration import microsite

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
from edxmako.shortcuts import render_to_response, render_to_string
from courseware.models import StudentModule
from shoppingcart.models import Coupon, CourseRegistrationCode, RegistrationCodeRedemption, Invoice, CourseMode
from student.models import CourseEnrollment, unique_id_for_user, anonymous_id_for_user
import instructor_task.api
from instructor_task.api_helper import AlreadyRunningError
from instructor_task.models import ReportStore
import instructor.enrollment as enrollment
from instructor.enrollment import (
    enroll_email,
    send_mail_to_student,
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
from user_api.models import UserPreference
from instructor.views import INVOICE_KEY

from submissions import api as sub_api  # installed from the edx-submissions repository

from bulk_email.models import CourseEmail

from .tools import (
    dump_student_extensions,
    dump_module_extensions,
    find_unit,
    get_student_from_identifier,
    require_student_from_identifier,
    handle_dashboard_error,
    parse_datetime,
    set_due_date_extension,
    strip_if_string,
    bulk_email_is_enabled_for_course,
    add_block_ids,
)
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys import InvalidKeyError
from student.models import UserProfile, Registration

log = logging.getLogger(__name__)


def common_exceptions_400(func):
    """
    Catches common exceptions and renders matching 400 errors.
    (decorator without arguments)
    """
    def wrapped(request, *args, **kwargs):  # pylint: disable=missing-docstring
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

    def decorator(func):  # pylint: disable=missing-docstring
        def wrapped(*args, **kwargs):  # pylint: disable=missing-docstring
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

    def decorator(func):  # pylint: disable=missing-docstring
        def wrapped(*args, **kwargs):  # pylint: disable=missing-docstring
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

    def decorator(func):  # pylint: disable=missing-docstring
        def wrapped(*args, **kwargs):  # pylint: disable=missing-docstring
            request = args[0]
            course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id']))

            if has_access(request.user, level, course):
                return func(*args, **kwargs)
            else:
                return HttpResponseForbidden()
        return wrapped
    return decorator


EMAIL_INDEX = 0
USERNAME_INDEX = 1
NAME_INDEX = 2
COUNTRY_INDEX = 3


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def register_and_enroll_students(request, course_id):  # pylint: disable=too-many-statements
    """
    Create new account and Enroll students in this course.
    Passing a csv file that contains a list of students.
    Order in csv should be the following email = 0; username = 1; name = 2; country = 3.
    Requires staff access.

    -If the email address and username already exists and the user is enrolled in the course,
    do nothing (including no email gets sent out)

    -If the email address already exists, but the username is different,
    match on the email address only and continue to enroll the user in the course using the email address
    as the matching criteria. Note the change of username as a warning message (but not a failure). Send a standard enrollment email
    which is the same as the existing manual enrollment

    -If the username already exists (but not the email), assume it is a different user and fail to create the new account.
     The failure will be messaged in a response in the browser.
    """

    if not microsite.get_value('ALLOW_AUTOMATED_SIGNUPS', settings.FEATURES.get('ALLOW_AUTOMATED_SIGNUPS', False)):
        return HttpResponseForbidden()

    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    warnings = []
    row_errors = []
    general_errors = []

    if 'students_list' in request.FILES:
        students = []

        try:
            upload_file = request.FILES.get('students_list')
            if upload_file.name.endswith('.csv'):
                students = [row for row in csv.reader(upload_file.read().splitlines())]
                course = get_course_by_id(course_id)
            else:
                general_errors.append({
                    'username': '', 'email': '',
                    'response': _('Make sure that the file you upload is in CSV format with no extraneous characters or rows.')
                })

        except Exception:  # pylint: disable=broad-except
            general_errors.append({
                'username': '', 'email': '', 'response': _('Could not read uploaded file.')
            })
        finally:
            upload_file.close()

        generated_passwords = []
        row_num = 0
        for student in students:
            row_num = row_num + 1

            # verify that we have exactly four columns in every row but allow for blank lines
            if len(student) != 4:
                if len(student) > 0:
                    general_errors.append({
                        'username': '',
                        'email': '',
                        'response': _('Data in row #{row_num} must have exactly four columns: email, username, full name, and country').format(row_num=row_num)
                    })
                continue

            # Iterate each student in the uploaded csv file.
            email = student[EMAIL_INDEX]
            username = student[USERNAME_INDEX]
            name = student[NAME_INDEX]
            country = student[COUNTRY_INDEX][:2]

            email_params = get_email_params(course, True, secure=request.is_secure())
            try:
                validate_email(email)  # Raises ValidationError if invalid
            except ValidationError:
                row_errors.append({
                    'username': username, 'email': email, 'response': _('Invalid email {email_address}.').format(email_address=email)})
            else:
                if User.objects.filter(email=email).exists():
                    # Email address already exists. assume it is the correct user
                    # and just register the user in the course and send an enrollment email.
                    user = User.objects.get(email=email)

                    # see if it is an exact match with email and username
                    # if it's not an exact match then just display a warning message, but continue onwards
                    if not User.objects.filter(email=email, username=username).exists():
                        warning_message = _(
                            'An account with email {email} exists but the provided username {username} '
                            'is different. Enrolling anyway with {email}.'
                        ).format(email=email, username=username)

                        warnings.append({
                            'username': username, 'email': email, 'response': warning_message})
                        log.warning('email {email} already exist'.format(email=email))
                    else:
                        log.info("user already exists with username '{username}' and email '{email}'".format(email=email, username=username))

                    # make sure user is enrolled in course
                    if not CourseEnrollment.is_enrolled(user, course_id):
                        CourseEnrollment.enroll(user, course_id)
                        log.info('user {username} enrolled in the course {course}'.format(username=username, course=course.id))
                        enroll_email(course_id=course_id, student_email=email, auto_enroll=True, email_students=True, email_params=email_params)
                else:
                    # This email does not yet exist, so we need to create a new account
                    # If username already exists in the database, then create_and_enroll_user
                    # will raise an IntegrityError exception.
                    password = generate_unique_password(generated_passwords)

                    try:
                        create_and_enroll_user(email, username, name, country, password, course_id)
                    except IntegrityError:
                        row_errors.append({
                            'username': username, 'email': email, 'response': _('Username {user} already exists.').format(user=username)})
                    except Exception as ex:
                        log.exception(type(ex).__name__)
                        row_errors.append({
                            'username': username, 'email': email, 'response': _(type(ex).__name__)})
                    else:
                        # It's a new user, an email will be sent to each newly created user.
                        email_params['message'] = 'account_creation_and_enrollment'
                        email_params['email_address'] = email
                        email_params['password'] = password
                        email_params['platform_name'] = microsite.get_value('platform_name', settings.PLATFORM_NAME)
                        send_mail_to_student(email, email_params)
                        log.info('email sent to new created user at {email}'.format(email=email))

    else:
        general_errors.append({
            'username': '', 'email': '', 'response': _('File is not attached.')
        })

    results = {
        'row_errors': row_errors,
        'general_errors': general_errors,
        'warnings': warnings
    }
    return JsonResponse(results)


def generate_random_string(length):
    """
    Create a string of random characters of specified length
    """
    chars = [
        char for char in string.ascii_uppercase + string.digits + string.ascii_lowercase
        if char not in 'aAeEiIoOuU1l'
    ]

    return string.join((random.choice(chars) for __ in range(length)), '')


def generate_unique_password(generated_passwords, password_length=12):
    """
    generate a unique password for each student.
    """

    password = generate_random_string(password_length)
    while password in generated_passwords:
        password = generate_random_string(password_length)

    generated_passwords.append(password)

    return password


def create_and_enroll_user(email, username, name, country, password, course_id):
    """ Creates a user and enroll him/her in the course"""

    user = User.objects.create_user(username, email, password)
    reg = Registration()
    reg.register(user)

    profile = UserProfile(user=user)
    profile.name = name
    profile.country = country
    profile.save()

    # try to enroll the user in this course
    CourseEnrollment.enroll(user, course_id)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params(action="enroll or unenroll", identifiers="stringified list of emails and/or usernames")
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
    action = request.POST.get('action')
    identifiers_raw = request.POST.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    auto_enroll = request.POST.get('auto_enroll') in ['true', 'True', True]
    email_students = request.POST.get('email_students') in ['true', 'True', True]

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

        except Exception as exc:  # pylint: disable=broad-except
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
@require_post_params(
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
    action = request.POST.get('action')
    identifiers_raw = request.POST.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    email_students = request.POST.get('email_students') in ['true', 'True', True]
    auto_enroll = request.POST.get('auto_enroll') in ['true', 'True', True]
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
def get_sale_records(request, course_id, csv=False):  # pylint: disable=unused-argument, redefined-outer-name
    """
    return the summary of all sales records for a particular course
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    query_features = [
        'company_name', 'company_contact_name', 'company_contact_email', 'total_codes', 'total_used_codes',
        'total_amount', 'created_at', 'customer_reference_number', 'recipient_name', 'recipient_email', 'created_by',
        'internal_reference', 'invoice_number', 'codes', 'course_id'
    ]

    sale_data = instructor_analytics.basic.sale_record_features(course_id, query_features)

    if not csv:
        for item in sale_data:
            item['created_by'] = item['created_by'].username

        response_payload = {
            'course_id': course_id.to_deprecated_string(),
            'sale': sale_data,
            'queried_features': query_features
        }
        return JsonResponse(response_payload)
    else:
        header, datarows = instructor_analytics.csvs.format_dictlist(sale_data, query_features)
        return instructor_analytics.csvs.create_csv_response("e-commerce_sale_invoice_records.csv", header, datarows)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_sale_order_records(request, course_id):  # pylint: disable=unused-argument, redefined-outer-name
    """
    return the summary of all sales records for a particular course
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    query_features = [
        ('id', 'Order Id'),
        ('company_name', 'Company Name'),
        ('company_contact_name', 'Company Contact Name'),
        ('company_contact_email', 'Company Contact Email'),
        ('total_amount', 'Total Amount'),
        ('total_codes', 'Total Codes'),
        ('total_used_codes', 'Total Used Codes'),
        ('logged_in_username', 'Login Username'),
        ('logged_in_email', 'Login User Email'),
        ('purchase_time', 'Date of Sale'),
        ('customer_reference_number', 'Customer Reference Number'),
        ('recipient_name', 'Recipient Name'),
        ('recipient_email', 'Recipient Email'),
        ('bill_to_street1', 'Street 1'),
        ('bill_to_street2', 'Street 2'),
        ('bill_to_city', 'City'),
        ('bill_to_state', 'State'),
        ('bill_to_postalcode', 'Postal Code'),
        ('bill_to_country', 'Country'),
        ('order_type', 'Order Type'),
        ('status', 'Order Item Status'),
        ('coupon_code', 'Coupon Code'),
        ('unit_cost', 'Unit Price'),
        ('list_price', 'List Price'),
        ('codes', 'Registration Codes'),
        ('course_id', 'Course Id')
    ]

    db_columns = [x[0] for x in query_features]
    csv_columns = [x[1] for x in query_features]
    sale_data = instructor_analytics.basic.sale_order_record_features(course_id, db_columns)
    header, datarows = instructor_analytics.csvs.format_dictlist(sale_data, db_columns)  # pylint: disable=unused-variable
    return instructor_analytics.csvs.create_csv_response("e-commerce_sale_order_records.csv", csv_columns, datarows)


@require_level('staff')
@require_POST
def sale_validation(request, course_id):
    """
    This method either invalidate or re validate the sale against the invoice number depending upon the event type
    """
    try:
        invoice_number = request.POST["invoice_number"]
    except KeyError:
        return HttpResponseBadRequest("Missing required invoice_number parameter")
    try:
        invoice_number = int(invoice_number)
    except ValueError:
        return HttpResponseBadRequest(
            "invoice_number must be an integer, {value} provided".format(
                value=invoice_number
            )
        )
    try:
        event_type = request.POST["event_type"]
    except KeyError:
        return HttpResponseBadRequest("Missing required event_type parameter")

    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        obj_invoice = Invoice.objects.select_related('is_valid').get(id=invoice_number, course_id=course_id)
    except Invoice.DoesNotExist:
        return HttpResponseNotFound(_("Invoice number '{0}' does not exist.".format(invoice_number)))

    if event_type == "invalidate":
        return invalidate_invoice(obj_invoice)
    else:
        return re_validate_invoice(obj_invoice)


def invalidate_invoice(obj_invoice):
    """
    This method invalidate the sale against the invoice number
    """
    if not obj_invoice.is_valid:
        return HttpResponseBadRequest(_("The sale associated with this invoice has already been invalidated."))
    obj_invoice.is_valid = False
    obj_invoice.save()
    message = _('Invoice number {0} has been invalidated.').format(obj_invoice.id)
    return JsonResponse({'message': message})


def re_validate_invoice(obj_invoice):
    """
    This method re-validate the sale against the invoice number
    """
    if obj_invoice.is_valid:
        return HttpResponseBadRequest(_("This invoice is already active."))

    obj_invoice.is_valid = True
    obj_invoice.save()
    message = _('The registration codes for invoice {0} have been re-activated.').format(obj_invoice.id)
    return JsonResponse({'message': message})


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_students_features(request, course_id, csv=False):  # pylint: disable=redefined-outer-name
    """
    Respond with json which contains a summary of all enrolled students profile information.

    Responds with JSON
        {"students": [{-student-info-}, ...]}

    TO DO accept requests for different attribute sets.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)

    available_features = instructor_analytics.basic.AVAILABLE_FEATURES

    # Allow for microsites to be able to define additional columns (e.g. )
    query_features = microsite.get_value('student_profile_download_fields')

    if not query_features:
        query_features = [
            'id', 'username', 'name', 'email', 'language', 'location',
            'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
            'goals'
        ]

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

    if course.is_cohorted:
        # Translators: 'Cohort' refers to a group of students within a course.
        query_features.append('cohort')
        query_features_names['cohort'] = _('Cohort')

    if not csv:
        student_data = instructor_analytics.basic.enrolled_students_features(course_key, query_features)
        response_payload = {
            'course_id': unicode(course_key),
            'students': student_data,
            'students_count': len(student_data),
            'queried_features': query_features,
            'feature_names': query_features_names,
            'available_features': available_features,
        }
        return JsonResponse(response_payload)
    else:
        try:
            instructor_task.api.submit_calculate_students_features_csv(request, course_key, query_features)
            success_status = _("Your enrolled student profile report is being generated! You can view the status of the generation task in the 'Pending Instructor Tasks' section.")
            return JsonResponse({"status": success_status})
        except AlreadyRunningError:
            already_running_status = _("An enrolled student profile report generation task is already in progress. Check the 'Pending Instructor Tasks' table for the status of the task. When completed, the report will be available for download in the table below.")
            return JsonResponse({"status": already_running_status})


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_coupon_codes(request, course_id):  # pylint: disable=unused-argument
    """
    Respond with csv which contains a summary of all Active Coupons.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    active_coupons = Coupon.objects.filter(course_id=course_id, is_active=True)
    query_features = [
        'course_id', 'percentage_discount', 'code_redeemed_count', 'description'
    ]
    coupons_list = instructor_analytics.basic.coupon_codes_features(query_features, active_coupons)
    header, data_rows = instructor_analytics.csvs.format_dictlist(coupons_list, query_features)
    return instructor_analytics.csvs.create_csv_response('Coupons.csv', header, data_rows)


def save_registration_code(user, course_id, invoice=None, order=None):
    """
    recursive function that generate a new code every time and saves in the Course Registration Table
    if validation check passes
    """
    code = random_code_generator()

    # check if the generated code is in the Coupon Table
    matching_coupons = Coupon.objects.filter(code=code, is_active=True)
    if matching_coupons:
        return save_registration_code(user, course_id, invoice, order)

    course_registration = CourseRegistrationCode(
        code=code,
        course_id=course_id.to_deprecated_string(),
        created_by=user,
        invoice=invoice,
        order=order
    )
    try:
        course_registration.save()
        return course_registration
    except IntegrityError:
        return save_registration_code(user, course_id, invoice, order)


def registration_codes_csv(file_name, codes_list, csv_type=None):
    """
    Respond with the csv headers and data rows
    given a dict of codes list
    :param file_name:
    :param codes_list:
    :param csv_type:
    """
    # csv headers
    query_features = [
        'code', 'course_id', 'company_name', 'created_by',
        'redeemed_by', 'invoice_id', 'purchaser', 'customer_reference_number', 'internal_reference'
    ]

    registration_codes = instructor_analytics.basic.course_registration_features(query_features, codes_list, csv_type)
    header, data_rows = instructor_analytics.csvs.format_dictlist(registration_codes, query_features)
    return instructor_analytics.csvs.create_csv_response(file_name, header, data_rows)


def random_code_generator():
    """
    generate a random alphanumeric code of length defined in
    REGISTRATION_CODE_LENGTH settings
    """
    code_length = getattr(settings, 'REGISTRATION_CODE_LENGTH', 8)
    return generate_random_string(code_length)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def get_registration_codes(request, course_id):  # pylint: disable=unused-argument
    """
    Respond with csv which contains a summary of all Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    #filter all the  course registration codes
    registration_codes = CourseRegistrationCode.objects.filter(course_id=course_id).order_by('invoice__company_name')

    company_name = request.POST['download_company_name']
    if company_name:
        registration_codes = registration_codes.filter(invoice__company_name=company_name)

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
    invoice_copy = False

    # covert the course registration code number into integer
    try:
        course_code_number = int(request.POST['total_registration_codes'])
    except ValueError:
        course_code_number = int(float(request.POST['total_registration_codes']))

    company_name = request.POST['company_name']
    company_contact_name = request.POST['company_contact_name']
    company_contact_email = request.POST['company_contact_email']
    sale_price = request.POST['sale_price']
    recipient_name = request.POST['recipient_name']
    recipient_email = request.POST['recipient_email']
    address_line_1 = request.POST['address_line_1']
    address_line_2 = request.POST['address_line_2']
    address_line_3 = request.POST['address_line_3']
    city = request.POST['city']
    state = request.POST['state']
    zip_code = request.POST['zip']
    country = request.POST['country']
    internal_reference = request.POST['internal_reference']
    customer_reference_number = request.POST['customer_reference_number']
    recipient_list = [recipient_email]
    if request.POST.get('invoice', False):
        recipient_list.append(request.user.email)
        invoice_copy = True

    UserPreference.set_preference(request.user, INVOICE_KEY, invoice_copy)
    sale_invoice = Invoice.objects.create(
        total_amount=sale_price,
        company_name=company_name,
        company_contact_email=company_contact_email,
        company_contact_name=company_contact_name,
        course_id=course_id,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        address_line_1=address_line_1,
        address_line_2=address_line_2,
        address_line_3=address_line_3,
        city=city,
        state=state,
        zip=zip_code,
        country=country,
        internal_reference=internal_reference,
        customer_reference_number=customer_reference_number
    )
    registration_codes = []
    for _ in range(course_code_number):  # pylint: disable=redefined-outer-name
        generated_registration_code = save_registration_code(request.user, course_id, sale_invoice, order=None)
        registration_codes.append(generated_registration_code)

    site_name = microsite.get_value('SITE_NAME', 'localhost')
    course = get_course_by_id(course_id, depth=None)
    course_honor_mode = CourseMode.mode_for_course(course_id, 'honor')
    course_price = course_honor_mode.min_price
    quantity = course_code_number
    discount = (float(quantity * course_price) - float(sale_price))
    course_url = '{base_url}{course_about}'.format(
        base_url=microsite.get_value('SITE_NAME', settings.SITE_NAME),
        course_about=reverse('about_course', kwargs={'course_id': course_id.to_deprecated_string()})
    )
    dashboard_url = '{base_url}{dashboard}'.format(
        base_url=microsite.get_value('SITE_NAME', settings.SITE_NAME),
        dashboard=reverse('dashboard')
    )

    from_address = microsite.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    context = {
        'invoice': sale_invoice,
        'site_name': site_name,
        'course': course,
        'course_price': course_price,
        'sub_total': course_price * quantity,
        'discount': discount,
        'sale_price': sale_price,
        'quantity': quantity,
        'registration_codes': registration_codes,
        'currency_symbol': settings.PAID_COURSE_REGISTRATION_CURRENCY[1],
        'course_url': course_url,
        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME),
        'dashboard_url': dashboard_url,
        'contact_email': from_address,
        'corp_address': microsite.get_value('invoice_corp_address', settings.INVOICE_CORP_ADDRESS),
        'payment_instructions': microsite.get_value('invoice_payment_instructions', settings. INVOICE_PAYMENT_INSTRUCTIONS),
        'date': time.strftime("%m/%d/%Y")
    }
    # composes registration codes invoice email
    subject = u'Confirmation and Invoice for {course_name}'.format(course_name=course.display_name)
    message = render_to_string('emails/registration_codes_sale_email.txt', context)

    invoice_attachment = render_to_string('emails/registration_codes_sale_invoice_attachment.txt', context)

    #send_mail(subject, message, from_address, recipient_list, fail_silently=False)
    csv_file = StringIO.StringIO()
    csv_writer = csv.writer(csv_file)
    for registration_code in registration_codes:
        csv_writer.writerow([registration_code.code])

    finance_email = microsite.get_value('finance_email', settings.FINANCE_EMAIL)
    if finance_email:
        # append the finance email into the recipient_list
        recipient_list.append(finance_email)

    # send a unique email for each recipient, don't put all email addresses in a single email
    for recipient in recipient_list:
        email = EmailMessage()
        email.subject = subject
        email.body = message
        email.from_email = from_address
        email.to = [recipient]
        email.attach(u'RegistrationCodes.csv', csv_file.getvalue(), 'text/csv')
        email.attach(u'Invoice.txt', invoice_attachment, 'text/plain')
        email.send()

    return registration_codes_csv("Registration_Codes.csv", registration_codes)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def active_registration_codes(request, course_id):  # pylint: disable=unused-argument
    """
    Respond with csv which contains a summary of all Active Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # find all the registration codes in this course
    registration_codes_list = CourseRegistrationCode.objects.filter(course_id=course_id).order_by('invoice__company_name')

    company_name = request.POST['active_company_name']
    if company_name:
        registration_codes_list = registration_codes_list.filter(invoice__company_name=company_name)
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
def spent_registration_codes(request, course_id):  # pylint: disable=unused-argument
    """
    Respond with csv which contains a summary of all Spent(used) Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # find the redeemed registration codes if any exist in the db
    code_redemption_set = RegistrationCodeRedemption.objects.select_related('registration_code').filter(
        registration_code__course_id=course_id
    )
    spent_codes_list = []
    if code_redemption_set.exists():
        redeemed_registration_codes = [code.registration_code.code for code in code_redemption_set]
        # filter the Registration Codes by course id and the redeemed codes and
        # you will get a list of all the spent(Redeemed) Registration Codes
        spent_codes_list = CourseRegistrationCode.objects.filter(
            course_id=course_id, code__in=redeemed_registration_codes
        ).order_by('invoice__company_name')

        company_name = request.POST['spent_company_name']
        if company_name:
            spent_codes_list = spent_codes_list.filter(invoice__company_name=company_name)  # pylint: disable=maybe-no-member

    csv_type = 'spent'
    return registration_codes_csv("Spent_Registration_Codes.csv", spent_codes_list, csv_type)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_anon_ids(request, course_id):  # pylint: disable=unused-argument
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

    # allow two branding points to come from Microsites: which CourseEmailTemplate should be used
    # and what the 'from' field in the email should be
    #
    # If these are None (because we are not in a Microsite or they are undefined in Microsite config) than
    # the system will use normal system defaults
    template_name = microsite.get_value('course_email_template_name')
    from_addr = microsite.get_value('course_email_from_addr')

    # Create the CourseEmail object.  This is saved immediately, so that
    # any transaction that has been pending up to this point will also be
    # committed.
    email = CourseEmail.create(
        course_id,
        request.user,
        send_to,
        subject, message,
        template_name=template_name,
        from_addr=from_addr
    )

    # Submit the task, so that the correct InstructorTask object gets created (for monitoring purposes)
    instructor_task.api.submit_bulk_course_email(request, course_id, email.id)  # pylint: disable=no-member

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
    if not (hasattr(settings, 'ANALYTICS_SERVER_URL') and
            hasattr(settings, 'ANALYTICS_API_KEY') and
            settings.ANALYTICS_SERVER_URL and settings.ANALYTICS_API_KEY):
        return HttpResponse("Analytics service not configured.", status=501)

    url = "{}get?aname={}&course_id={}&apikey={}".format(
        settings.ANALYTICS_SERVER_URL,
        analytics_name,
        urllib.quote(unicode(course_id)),
        settings.ANALYTICS_API_KEY,
    )

    try:
        res = requests.get(url)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error requesting from analytics server at %s", url)
        return HttpResponse("Error requesting from analytics server.", status=500)

    if res.status_code is 200:
        payload = json.loads(res.content)
        add_block_ids(payload)
        content = json.dumps(payload)
        # return the successful request content
        return HttpResponse(content, content_type="application/json")
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


@require_POST
def get_user_invoice_preference(request, course_id):  # pylint: disable=unused-argument
    """
    Gets invoice copy user's preferences.
    """
    invoice_copy_preference = True
    if UserPreference.get_preference(request.user, INVOICE_KEY) is not None:
        invoice_copy_preference = UserPreference.get_preference(request.user, INVOICE_KEY) == 'True'

    return JsonResponse({
        'invoice_copy': invoice_copy_preference
    })


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
    student = require_student_from_identifier(request.GET.get('student'))
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
    student = require_student_from_identifier(request.GET.get('student'))
    unit = find_unit(course, request.GET.get('url'))
    set_due_date_extension(course, unit, student, None)
    if not getattr(unit, "due", None):
        # It's possible the normal due date was deleted after an extension was granted:
        return JsonResponse(
            _("Successfully removed invalid due date extension (unit has no due date).")
        )

    original_due_date_str = unit.due.strftime('%Y-%m-%d %H:%M')
    return JsonResponse(_(
        'Successfully reset due date for student {0} for {1} '
        'to {2}').format(student.profile.name, _display_unit(unit),
                         original_due_date_str))


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
    student = require_student_from_identifier(request.GET.get('student'))
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
