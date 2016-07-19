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
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import cache_control
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail.message import EmailMessage
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.utils.html import strip_tags
from django.shortcuts import redirect
import string
import random
import unicodecsv
import decimal
from student import auth
from student.roles import GlobalStaff, CourseSalesAdminRole, CourseFinanceAdminRole
from util.file import (
    store_uploaded_file, course_and_time_based_filename_generator,
    FileValidationException, UniversalNewlineIterator
)
from util.json_request import JsonResponse, JsonResponseBadRequest
from util.views import require_global_staff
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
from edxmako.shortcuts import render_to_string
from courseware.models import StudentModule
from shoppingcart.models import (
    Coupon,
    CourseRegistrationCode,
    RegistrationCodeRedemption,
    Invoice,
    CourseMode,
    CourseRegistrationCodeInvoiceItem,
)
from student.models import (
    CourseEnrollment, unique_id_for_user, anonymous_id_for_user,
    UserProfile, Registration, EntranceExamConfiguration,
    ManualEnrollmentAudit, UNENROLLED_TO_ALLOWEDTOENROLL, ALLOWEDTOENROLL_TO_ENROLLED,
    ENROLLED_TO_ENROLLED, ENROLLED_TO_UNENROLLED, UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED, ALLOWEDTOENROLL_TO_UNENROLLED, DEFAULT_TRANSITION_STATE
)
import instructor_task.api
from instructor_task.api_helper import AlreadyRunningError
from instructor_task.models import ReportStore
import instructor.enrollment as enrollment
from instructor.enrollment import (
    get_user_email_language,
    enroll_email,
    send_mail_to_student,
    get_email_params,
    send_beta_role_email,
    unenroll_email,
)
from instructor.access import list_with_level, allow_access, revoke_access, ROLES, update_forum_role
import instructor_analytics.basic
import instructor_analytics.distributions
import instructor_analytics.csvs
import csv
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, set_user_preference
from openedx.core.djangolib.markup import HTML, Text
from instructor.views import INVOICE_KEY

from submissions import api as sub_api  # installed from the edx-submissions repository

from certificates import api as certs_api
from certificates.models import CertificateWhitelist, GeneratedCertificate, CertificateStatuses, CertificateInvalidation

from bulk_email.models import CourseEmail, BulkEmailFlag
from student.models import get_user_by_username_or_email

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
)
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

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


def require_post_params(*args, **kwargs):
    """
    Checks for required parameters or renders a 400 error.
    (decorator with arguments)

    `args` is a *list of required POST parameter names.
    `kwargs` is a **dict of required POST parameter names
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
            course = get_course_by_id(CourseKey.from_string(kwargs['course_id']))

            if has_access(request.user, level, course):
                return func(*args, **kwargs)
            else:
                return HttpResponseForbidden()
        return wrapped
    return decorator


def require_sales_admin(func):
    """
    Decorator for checking sales administrator access before executing an HTTP endpoint. This decorator
    is designed to be used for a request based action on a course. It assumes that there will be a
    request object as well as a course_id attribute to leverage to check course level privileges.

    If the user does not have privileges for this operation, this will return HttpResponseForbidden (403).
    """
    def wrapped(request, course_id):  # pylint: disable=missing-docstring

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s", course_id)
            return HttpResponseNotFound()

        access = auth.user_has_role(request.user, CourseSalesAdminRole(course_key))

        if access:
            return func(request, course_id)
        else:
            return HttpResponseForbidden()
    return wrapped


def require_finance_admin(func):
    """
    Decorator for checking finance administrator access before executing an HTTP endpoint. This decorator
    is designed to be used for a request based action on a course. It assumes that there will be a
    request object as well as a course_id attribute to leverage to check course level privileges.

    If the user does not have privileges for this operation, this will return HttpResponseForbidden (403).
    """
    def wrapped(request, course_id):  # pylint: disable=missing-docstring

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s", course_id)
            return HttpResponseNotFound()

        access = auth.user_has_role(request.user, CourseFinanceAdminRole(course_key))

        if access:
            return func(request, course_id)
        else:
            return HttpResponseForbidden()
    return wrapped


EMAIL_INDEX = 0
USERNAME_INDEX = 1
NAME_INDEX = 2
COUNTRY_INDEX = 3


@require_POST
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

    if not configuration_helpers.get_value(
            'ALLOW_AUTOMATED_SIGNUPS',
            settings.FEATURES.get('ALLOW_AUTOMATED_SIGNUPS', False),
    ):
        return HttpResponseForbidden()

    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    warnings = []
    row_errors = []
    general_errors = []

    # for white labels we use 'shopping cart' which uses CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG as
    # course mode for creating course enrollments.
    if CourseMode.is_white_label(course_id):
        course_mode = CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
    else:
        course_mode = None

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
                            'username': username, 'email': email, 'response': warning_message
                        })
                        log.warning(u'email %s already exist', email)
                    else:
                        log.info(
                            u"user already exists with username '%s' and email '%s'",
                            username,
                            email
                        )

                    # enroll a user if it is not already enrolled.
                    if not CourseEnrollment.is_enrolled(user, course_id):
                        # Enroll user to the course and add manual enrollment audit trail
                        create_manual_course_enrollment(
                            user=user,
                            course_id=course_id,
                            mode=course_mode,
                            enrolled_by=request.user,
                            reason='Enrolling via csv upload',
                            state_transition=UNENROLLED_TO_ENROLLED,
                        )
                        enroll_email(course_id=course_id, student_email=email, auto_enroll=True, email_students=True, email_params=email_params)
                else:
                    # This email does not yet exist, so we need to create a new account
                    # If username already exists in the database, then create_and_enroll_user
                    # will raise an IntegrityError exception.
                    password = generate_unique_password(generated_passwords)
                    errors = create_and_enroll_user(
                        email, username, name, country, password, course_id, course_mode, request.user, email_params
                    )
                    row_errors.extend(errors)

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


def create_user_and_user_profile(email, username, name, country, password):
    """
    Create a new user, add a new Registration instance for letting user verify its identity and create a user profile.

    :param email: user's email address
    :param username: user's username
    :param name: user's name
    :param country: user's country
    :param password: user's password

    :return: User instance of the new user.
    """
    user = User.objects.create_user(username, email, password)
    reg = Registration()
    reg.register(user)

    profile = UserProfile(user=user)
    profile.name = name
    profile.country = country
    profile.save()

    return user


def create_manual_course_enrollment(user, course_id, mode, enrolled_by, reason, state_transition):
    """
    Create course enrollment for the given student and create manual enrollment audit trail.

    :param user: User who is to enroll in course
    :param course_id: course identifier of the course in which to enroll the user.
    :param mode: mode for user enrollment, e.g. 'honor', 'audit' etc.
    :param enrolled_by: User who made the manual enrollment entry (usually instructor or support)
    :param reason: Reason behind manual enrollment
    :param state_transition: state transition denoting whether student enrolled from un-enrolled,
            un-enrolled from enrolled etc.
    :return CourseEnrollment instance.
    """
    enrollment_obj = CourseEnrollment.enroll(user, course_id, mode=mode)
    ManualEnrollmentAudit.create_manual_enrollment_audit(
        enrolled_by, user.email, state_transition, reason, enrollment_obj
    )

    log.info(u'user %s enrolled in the course %s', user.username, course_id)
    return enrollment_obj


def create_and_enroll_user(email, username, name, country, password, course_id, course_mode, enrolled_by, email_params):
    """
    Create a new user and enroll him/her to the given course, return list of errors in the following format
        Error format:
            each error is key-value pait dict with following key-value pairs.
            1. username: username of the user to enroll
            1. email: email of the user to enroll
            1. response: readable error message

    :param email: user's email address
    :param username: user's username
    :param name: user's name
    :param country: user's country
    :param password: user's password
    :param course_id: course identifier of the course in which to enroll the user.
    :param course_mode: mode for user enrollment, e.g. 'honor', 'audit' etc.
    :param enrolled_by: User who made the manual enrollment entry (usually instructor or support)
    :param email_params: information to send to the user via email

    :return: list of errors
    """
    errors = list()
    try:
        with transaction.atomic():
            # Create a new user
            user = create_user_and_user_profile(email, username, name, country, password)

            # Enroll user to the course and add manual enrollment audit trail
            create_manual_course_enrollment(
                user=user,
                course_id=course_id,
                mode=course_mode,
                enrolled_by=enrolled_by,
                reason='Enrolling via csv upload',
                state_transition=UNENROLLED_TO_ENROLLED,
            )
    except IntegrityError:
        errors.append({
            'username': username, 'email': email, 'response': _('Username {user} already exists.').format(user=username)
        })
    except Exception as ex:  # pylint: disable=broad-except
        log.exception(type(ex).__name__)
        errors.append({
            'username': username, 'email': email, 'response': type(ex).__name__,
        })
    else:
        try:
            # It's a new user, an email will be sent to each newly created user.
            email_params.update({
                'message': 'account_creation_and_enrollment',
                'email_address': email,
                'password': password,
                'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
            })
            send_mail_to_student(email, email_params)
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(
                "Exception '{exception}' raised while sending email to new user.".format(exception=type(ex).__name__)
            )
            errors.append({
                'username': username,
                'email': email,
                'response':
                    _("Error '{error}' while sending email to new user (user email={email}). "
                      "Without the email student would not be able to login. "
                      "Please contact support for further information.").format(error=type(ex).__name__, email=email),
            })
        else:
            log.info(u'email sent to new created user at %s', email)

    return errors


@require_POST
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
    is_white_label = CourseMode.is_white_label(course_id)
    reason = request.POST.get('reason')
    if is_white_label:
        if not reason:
            return JsonResponse(
                {
                    'action': action,
                    'results': [{'error': True}],
                    'auto_enroll': auto_enroll,
                }, status=400)
    enrollment_obj = None
    state_transition = DEFAULT_TRANSITION_STATE

    email_params = {}
    if email_students:
        course = get_course_by_id(course_id)
        email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

    results = []
    for identifier in identifiers:
        # First try to get a user object from the identifer
        user = None
        email = None
        language = None
        try:
            user = get_student_from_identifier(identifier)
        except User.DoesNotExist:
            email = identifier
        else:
            email = user.email
            language = get_user_email_language(user)

        try:
            # Use django.core.validators.validate_email to check email address
            # validity (obviously, cannot check if email actually /exists/,
            # simply that it is plausibly valid)
            validate_email(email)  # Raises ValidationError if invalid
            if action == 'enroll':
                before, after, enrollment_obj = enroll_email(
                    course_id, email, auto_enroll, email_students, email_params, language=language
                )
                before_enrollment = before.to_dict()['enrollment']
                before_user_registered = before.to_dict()['user']
                before_allowed = before.to_dict()['allowed']
                after_enrollment = after.to_dict()['enrollment']
                after_allowed = after.to_dict()['allowed']

                if before_user_registered:
                    if after_enrollment:
                        if before_enrollment:
                            state_transition = ENROLLED_TO_ENROLLED
                        else:
                            if before_allowed:
                                state_transition = ALLOWEDTOENROLL_TO_ENROLLED
                            else:
                                state_transition = UNENROLLED_TO_ENROLLED
                else:
                    if after_allowed:
                        state_transition = UNENROLLED_TO_ALLOWEDTOENROLL

            elif action == 'unenroll':
                before, after = unenroll_email(
                    course_id, email, email_students, email_params, language=language
                )
                before_enrollment = before.to_dict()['enrollment']
                before_allowed = before.to_dict()['allowed']
                enrollment_obj = CourseEnrollment.get_enrollment(user, course_id)

                if before_enrollment:
                    state_transition = ENROLLED_TO_UNENROLLED
                else:
                    if before_allowed:
                        state_transition = ALLOWEDTOENROLL_TO_UNENROLLED
                    else:
                        state_transition = UNENROLLED_TO_UNENROLLED

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
            log.exception(u"Error while #{}ing student")
            log.exception(exc)
            results.append({
                'identifier': identifier,
                'error': True,
            })

        else:
            ManualEnrollmentAudit.create_manual_enrollment_audit(
                request.user, email, state_transition, reason, enrollment_obj
            )
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


@require_POST
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
            log.exception(u"Error while #{}ing student")
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


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@common_exceptions_400
@require_post_params(
    unique_student_identifier="email or username of user to change access",
    rolename="'instructor', 'staff', 'beta', or 'ccx_coach'",
    action="'allow' or 'revoke'"
)
def modify_access(request, course_id):
    """
    Modify staff/instructor access of other user.
    Requires instructor access.

    NOTE: instructors cannot remove their own instructor access.

    Query parameters:
    unique_student_identifer is the target user's username or email
    rolename is one of ['instructor', 'staff', 'beta', 'ccx_coach']
    action is one of ['allow', 'revoke']
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'instructor', course_id, depth=None
    )
    try:
        user = get_student_from_identifier(request.POST.get('unique_student_identifier'))
    except User.DoesNotExist:
        response_payload = {
            'unique_student_identifier': request.POST.get('unique_student_identifier'),
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

    rolename = request.POST.get('rolename')
    action = request.POST.get('action')

    if rolename not in ROLES:
        error = strip_tags("unknown rolename '{}'".format(rolename))
        log.error(error)
        return HttpResponseBadRequest(error)

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


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@require_post_params(rolename="'instructor', 'staff', or 'beta'")
def list_course_role_members(request, course_id):
    """
    List instructors and staff.
    Requires instructor access.

    rolename is one of ['instructor', 'staff', 'beta', 'ccx_coach']

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

    rolename = request.POST.get('rolename')

    if rolename not in ROLES:
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


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_problem_responses(request, course_id):
    """
    Initiate generation of a CSV file containing all student answers
    to a given problem.

    Responds with JSON
        {"status": "... status message ..."}

    if initiation is successful (or generation task is already running).

    Responds with BadRequest if problem location is faulty.
    """
    course_key = CourseKey.from_string(course_id)
    problem_location = request.POST.get('problem_location', '')

    try:
        problem_key = UsageKey.from_string(problem_location)
        # Are we dealing with an "old-style" problem location?
        run = problem_key.run
        if not run:
            problem_key = course_key.make_usage_key_from_deprecated_string(problem_location)
        if problem_key.course_key != course_key:
            raise InvalidKeyError(type(problem_key), problem_key)
    except InvalidKeyError:
        return JsonResponseBadRequest(_("Could not find problem with this location."))

    try:
        instructor_task.api.submit_calculate_problem_responses_csv(request, course_key, problem_location)
        success_status = _(
            "The problem responses report is being created."
            " To view the status of the report, see Pending Tasks below."
        )
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _(
            "A problem responses report generation task is already in progress. "
            "Check the 'Pending Tasks' table for the status of the task. "
            "When completed, the report will be available for download in the table below."
        )
        return JsonResponse({"status": already_running_status})


@require_POST
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
        'total_amount', 'created', 'customer_reference_number', 'recipient_name', 'recipient_email', 'created_by',
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
def get_sale_order_records(request, course_id):  # pylint: disable=unused-argument
    """
    return the summary of all sales records for a particular course
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    query_features = [
        ('id', 'Order Id'),
        ('company_name', 'Company Name'),
        ('company_contact_name', 'Company Contact Name'),
        ('company_contact_email', 'Company Contact Email'),
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
        ('list_price', 'List Price'),
        ('unit_cost', 'Unit Price'),
        ('quantity', 'Quantity'),
        ('total_discount', 'Total Discount'),
        ('total_amount', 'Total Amount Paid'),
    ]

    db_columns = [x[0] for x in query_features]
    csv_columns = [x[1] for x in query_features]
    sale_data = instructor_analytics.basic.sale_order_record_features(course_id, db_columns)
    __, datarows = instructor_analytics.csvs.format_dictlist(sale_data, db_columns)
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
        obj_invoice = CourseRegistrationCodeInvoiceItem.objects.select_related('invoice').get(
            invoice_id=invoice_number,
            course_id=course_id
        )
        obj_invoice = obj_invoice.invoice
    except CourseRegistrationCodeInvoiceItem.DoesNotExist:  # Check for old type invoices
        return HttpResponseNotFound(_("Invoice number '{num}' does not exist.").format(num=invoice_number))

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


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_issued_certificates(request, course_id):
    """
    Responds with JSON if CSV is not required. contains a list of issued certificates.
    Arguments:
        course_id
    Returns:
        {"certificates": [{course_id: xyz, mode: 'honor'}, ...]}

    """
    course_key = CourseKey.from_string(course_id)
    csv_required = request.GET.get('csv', 'false')

    query_features = ['course_id', 'mode', 'total_issued_certificate', 'report_run_date']
    query_features_names = [
        ('course_id', _('CourseID')),
        ('mode', _('Certificate Type')),
        ('total_issued_certificate', _('Total Certificates Issued')),
        ('report_run_date', _('Date Report Run'))
    ]
    certificates_data = instructor_analytics.basic.issued_certificates(course_key, query_features)
    if csv_required.lower() == 'true':
        __, data_rows = instructor_analytics.csvs.format_dictlist(certificates_data, query_features)
        return instructor_analytics.csvs.create_csv_response(
            'issued_certificates.csv',
            [col_header for __, col_header in query_features_names],
            data_rows
        )
    else:
        response_payload = {
            'certificates': certificates_data,
            'queried_features': query_features,
            'feature_names': dict(query_features_names)
        }
        return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
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

    # Allow for sites to be able to define additional columns.
    # Note that adding additional columns has the potential to break
    # the student profile report due to a character limit on the
    # asynchronous job input which in this case is a JSON string
    # containing the list of columns to include in the report.
    # TODO: Refactor the student profile report code to remove the list of columns
    # that should be included in the report from the asynchronous job input.
    # We need to clone the list because we modify it below
    query_features = list(configuration_helpers.get_value('student_profile_download_fields', []))

    if not query_features:
        query_features = [
            'id', 'username', 'name', 'email', 'language', 'location',
            'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
            'goals',
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

    if is_course_cohorted(course.id):
        # Translators: 'Cohort' refers to a group of students within a course.
        query_features.append('cohort')
        query_features_names['cohort'] = _('Cohort')

    if course.teams_enabled:
        query_features.append('team')
        query_features_names['team'] = _('Team')

    # For compatibility reasons, city and country should always appear last.
    query_features.append('city')
    query_features_names['city'] = _('City')
    query_features.append('country')
    query_features_names['country'] = _('Country')

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
            success_status = _("The enrolled learner profile report is being created."
                               " To view the status of the report, see Pending Tasks below.")
            return JsonResponse({"status": success_status})
        except AlreadyRunningError:
            already_running_status = _(
                "This enrollment report is currently being created."
                " To view the status of the report, see Pending Tasks below."
                " You will be able to download the report when it is complete.")
            return JsonResponse({"status": already_running_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_students_who_may_enroll(request, course_id):
    """
    Initiate generation of a CSV file containing information about
    students who may enroll in a course.

    Responds with JSON
        {"status": "... status message ..."}

    """
    course_key = CourseKey.from_string(course_id)
    query_features = ['email']
    try:
        instructor_task.api.submit_calculate_may_enroll_csv(request, course_key, query_features)
        success_status = _(
            "The enrollment report is being created. This report contains"
            " information about learners who can enroll in the course."
            " To view the status of the report, see Pending Tasks below."
        )
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _(
            "This enrollment report is currently being created."
            " To view the status of the report, see Pending Tasks below."
            " You will be able to download the report when it is complete."
        )
        return JsonResponse({"status": already_running_status})


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@require_level('staff')
def add_users_to_cohorts(request, course_id):
    """
    View method that accepts an uploaded file (using key "uploaded-file")
    containing cohort assignments for users. This method spawns a celery task
    to do the assignments, and a CSV file with results is provided via data downloads.
    """
    course_key = SlashSeparatedCourseKey.from_string(course_id)

    try:
        def validator(file_storage, file_to_validate):
            """
            Verifies that the expected columns are present.
            """
            with file_storage.open(file_to_validate) as f:
                reader = unicodecsv.reader(UniversalNewlineIterator(f), encoding='utf-8')
                try:
                    fieldnames = next(reader)
                except StopIteration:
                    fieldnames = []
                msg = None
                if "cohort" not in fieldnames:
                    msg = _("The file must contain a 'cohort' column containing cohort names.")
                elif "email" not in fieldnames and "username" not in fieldnames:
                    msg = _("The file must contain a 'username' column, an 'email' column, or both.")
                if msg:
                    raise FileValidationException(msg)

        __, filename = store_uploaded_file(
            request, 'uploaded-file', ['.csv'],
            course_and_time_based_filename_generator(course_key, "cohorts"),
            max_file_size=2000000,  # limit to 2 MB
            validator=validator
        )
        # The task will assume the default file storage.
        instructor_task.api.submit_cohort_students(request, course_key, filename)
    except (FileValidationException, PermissionDenied) as err:
        return JsonResponse({"error": unicode(err)}, status=400)

    return JsonResponse()


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_coupon_codes(request, course_id):  # pylint: disable=unused-argument
    """
    Respond with csv which contains a summary of all Active Coupons.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    coupons = Coupon.objects.filter(course_id=course_id)

    query_features = [
        ('code', _('Coupon Code')),
        ('course_id', _('Course Id')),
        ('percentage_discount', _('% Discount')),
        ('description', _('Description')),
        ('expiration_date', _('Expiration Date')),
        ('is_active', _('Is Active')),
        ('code_redeemed_count', _('Code Redeemed Count')),
        ('total_discounted_seats', _('Total Discounted Seats')),
        ('total_discounted_amount', _('Total Discounted Amount')),
    ]
    db_columns = [x[0] for x in query_features]
    csv_columns = [x[1] for x in query_features]

    coupons_list = instructor_analytics.basic.coupon_codes_features(db_columns, coupons, course_id)
    __, data_rows = instructor_analytics.csvs.format_dictlist(coupons_list, db_columns)
    return instructor_analytics.csvs.create_csv_response('Coupons.csv', csv_columns, data_rows)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_finance_admin
def get_enrollment_report(request, course_id):
    """
    get the enrollment report for the particular course.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_detailed_enrollment_features_csv(request, course_key)
        success_status = _("The detailed enrollment report is being created."
                           " To view the status of the report, see Pending Tasks below.")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("The detailed enrollment report is being created."
                                   " To view the status of the report, see Pending Tasks below."
                                   " You will be able to download the report when it is complete.")
        return JsonResponse({
            "status": already_running_status
        })


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_finance_admin
def get_exec_summary_report(request, course_id):
    """
    get the executive summary report for the particular course.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_executive_summary_report(request, course_key)
        status_response = _("The executive summary report is being created."
                            " To view the status of the report, see Pending Tasks below.")
    except AlreadyRunningError:
        status_response = _(
            "The executive summary report is currently being created."
            " To view the status of the report, see Pending Tasks below."
            " You will be able to download the report when it is complete."
        )
    return JsonResponse({
        "status": status_response
    })


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_course_survey_results(request, course_id):
    """
    get the survey results report for the particular course.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_course_survey_report(request, course_key)
        status_response = _("The survey report is being created."
                            " To view the status of the report, see Pending Tasks below.")
    except AlreadyRunningError:
        status_response = _(
            "The survey report is currently being created."
            " To view the status of the report, see Pending Tasks below."
            " You will be able to download the report when it is complete."
        )
    return JsonResponse({
        "status": status_response
    })


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_proctored_exam_results(request, course_id):
    """
    get the proctored exam resultsreport for the particular course.
    """
    query_features = [
        'user_email',
        'exam_name',
        'attempt_code',
        'allowed_time_limit_mins',
        'is_sample_attempt',
        'started_at',
        'completed_at',
        'status',
    ]

    course_key = CourseKey.from_string(course_id)
    try:
        instructor_task.api.submit_proctored_exam_results_report(request, course_key, query_features)
        status_response = _("The proctored exam results report is being created."
                            " To view the status of the report, see Pending Tasks below.")
    except AlreadyRunningError:
        status_response = _(
            "The proctored exam results report is currently being created."
            " To view the status of the report, see Pending Tasks below."
            " You will be able to download the report when it is complete."
        )
    return JsonResponse({
        "status": status_response
    })


def save_registration_code(user, course_id, mode_slug, invoice=None, order=None, invoice_item=None):
    """
    recursive function that generate a new code every time and saves in the Course Registration Table
    if validation check passes

    Args:
        user (User): The user creating the course registration codes.
        course_id (str): The string representation of the course ID.
        mode_slug (str): The Course Mode Slug associated with any enrollment made by these codes.
        invoice (Invoice): (Optional) The associated invoice for this code.
        order (Order): (Optional) The associated order for this code.
        invoice_item (CourseRegistrationCodeInvoiceItem) : (Optional) The associated CourseRegistrationCodeInvoiceItem

    Returns:
        The newly created CourseRegistrationCode.

    """
    code = random_code_generator()

    # check if the generated code is in the Coupon Table
    matching_coupons = Coupon.objects.filter(code=code, is_active=True)
    if matching_coupons:
        return save_registration_code(
            user, course_id, mode_slug, invoice=invoice, order=order, invoice_item=invoice_item
        )

    course_registration = CourseRegistrationCode(
        code=code,
        course_id=unicode(course_id),
        created_by=user,
        invoice=invoice,
        order=order,
        mode_slug=mode_slug,
        invoice_item=invoice_item
    )
    try:
        with transaction.atomic():
            course_registration.save()
        return course_registration
    except IntegrityError:
        return save_registration_code(
            user, course_id, mode_slug, invoice=invoice, order=order, invoice_item=invoice_item
        )


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
        'code', 'redeem_code_url', 'course_id', 'company_name', 'created_by',
        'redeemed_by', 'invoice_id', 'purchaser', 'customer_reference_number', 'internal_reference', 'is_valid'
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
def get_registration_codes(request, course_id):
    """
    Respond with csv which contains a summary of all Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    #filter all the  course registration codes
    registration_codes = CourseRegistrationCode.objects.filter(
        course_id=course_id
    ).order_by('invoice_item__invoice__company_name')

    company_name = request.POST['download_company_name']
    if company_name:
        registration_codes = registration_codes.filter(invoice_item__invoice__company_name=company_name)

    csv_type = 'download'
    return registration_codes_csv("Registration_Codes.csv", registration_codes, csv_type)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_sales_admin
@require_POST
def generate_registration_codes(request, course_id):
    """
    Respond with csv which contains a summary of all Generated Codes.
    """
    course_id = CourseKey.from_string(course_id)
    invoice_copy = False

    # covert the course registration code number into integer
    try:
        course_code_number = int(request.POST['total_registration_codes'])
    except ValueError:
        course_code_number = int(float(request.POST['total_registration_codes']))

    company_name = request.POST['company_name']
    company_contact_name = request.POST['company_contact_name']
    company_contact_email = request.POST['company_contact_email']
    unit_price = request.POST['unit_price']

    try:
        unit_price = (
            decimal.Decimal(unit_price)
        ).quantize(
            decimal.Decimal('.01'),
            rounding=decimal.ROUND_DOWN
        )
    except decimal.InvalidOperation:
        return HttpResponse(
            status=400,
            content=_(u"Could not parse amount as a decimal")
        )

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

    sale_price = unit_price * course_code_number
    set_user_preference(request.user, INVOICE_KEY, invoice_copy)
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

    invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
        invoice=sale_invoice,
        qty=course_code_number,
        unit_price=unit_price,
        course_id=course_id
    )

    course = get_course_by_id(course_id, depth=0)
    paid_modes = CourseMode.paid_modes_for_course(course_id)

    if len(paid_modes) != 1:
        msg = (
            u"Generating Code Redeem Codes for Course '{course_id}', which must have a single paid course mode. "
            u"This is a configuration issue. Current course modes with payment options: {paid_modes}"
        ).format(course_id=course_id, paid_modes=paid_modes)
        log.error(msg)
        return HttpResponse(
            status=500,
            content=_(u"Unable to generate redeem codes because of course misconfiguration.")
        )

    course_mode = paid_modes[0]
    course_price = course_mode.min_price

    registration_codes = []
    for __ in range(course_code_number):
        generated_registration_code = save_registration_code(
            request.user, course_id, course_mode.slug, invoice=sale_invoice, order=None, invoice_item=invoice_item
        )
        registration_codes.append(generated_registration_code)

    site_name = configuration_helpers.get_value('SITE_NAME', 'localhost')
    quantity = course_code_number
    discount = (float(quantity * course_price) - float(sale_price))
    course_url = '{base_url}{course_about}'.format(
        base_url=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
        course_about=reverse('about_course', kwargs={'course_id': course_id.to_deprecated_string()})
    )
    dashboard_url = '{base_url}{dashboard}'.format(
        base_url=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
        dashboard=reverse('dashboard')
    )

    try:
        pdf_file = sale_invoice.generate_pdf_invoice(course, course_price, int(quantity), float(sale_price))
    except Exception:  # pylint: disable=broad-except
        log.exception('Exception at creating pdf file.')
        pdf_file = None

    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
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
        'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        'dashboard_url': dashboard_url,
        'contact_email': from_address,
        'corp_address': configuration_helpers.get_value('invoice_corp_address', settings.INVOICE_CORP_ADDRESS),
        'payment_instructions': configuration_helpers.get_value(
            'invoice_payment_instructions',
            settings. INVOICE_PAYMENT_INSTRUCTIONS,
        ),
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
        full_redeem_code_url = 'http://{base_url}{redeem_code_url}'.format(
            base_url=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            redeem_code_url=reverse('register_code_redemption', kwargs={'registration_code': registration_code.code})
        )
        csv_writer.writerow([registration_code.code, full_redeem_code_url])
    finance_email = configuration_helpers.get_value('finance_email', settings.FINANCE_EMAIL)
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
        if pdf_file is not None:
            email.attach(u'Invoice.pdf', pdf_file.getvalue(), 'application/pdf')
        else:
            file_buffer = StringIO.StringIO(_('pdf download unavailable right now, please contact support.'))
            email.attach(u'pdf_unavailable.txt', file_buffer.getvalue(), 'text/plain')
        email.send()

    return registration_codes_csv("Registration_Codes.csv", registration_codes)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def active_registration_codes(request, course_id):
    """
    Respond with csv which contains a summary of all Active Registration Codes.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # find all the registration codes in this course
    registration_codes_list = CourseRegistrationCode.objects.filter(
        course_id=course_id
    ).order_by('invoice_item__invoice__company_name')

    company_name = request.POST['active_company_name']
    if company_name:
        registration_codes_list = registration_codes_list.filter(invoice_item__invoice__company_name=company_name)
    # find the redeemed registration codes if any exist in the db
    code_redemption_set = RegistrationCodeRedemption.objects.select_related(
        'registration_code', 'registration_code__invoice_item__invoice'
    ).filter(registration_code__course_id=course_id)
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
def spent_registration_codes(request, course_id):
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
        ).order_by('invoice_item__invoice__company_name').select_related('invoice_item__invoice')

        company_name = request.POST['spent_company_name']
        if company_name:
            spent_codes_list = spent_codes_list.filter(invoice_item__invoice__company_name=company_name)  # pylint: disable=maybe-no-member

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
        response = HttpResponse(content_type='text/csv')
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


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@common_exceptions_400
@require_level('staff')
@require_post_params(
    unique_student_identifier="email or username of student for whom to get progress url"
)
def get_student_progress_url(request, course_id):
    """
    Get the progress url of a student.
    Limited to staff access.

    Takes query parameter unique_student_identifier and if the student exists
    returns e.g. {
        'progress_url': '/../...'
    }
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = get_student_from_identifier(request.POST.get('unique_student_identifier'))

    progress_url = reverse('student_progress', kwargs={'course_id': course_id.to_deprecated_string(), 'student_id': user.id})

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
        'progress_url': progress_url,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params(
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

    problem_to_reset = strip_if_string(request.POST.get('problem_to_reset'))
    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)
    all_students = request.POST.get('all_students', False) in ['true', 'True', True]
    delete_module = request.POST.get('delete_module', False) in ['true', 'True', True]

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
            enrollment.reset_student_attempts(
                course_id,
                student,
                module_state_key,
                requesting_user=request.user,
                delete_module=delete_module
            )
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


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@common_exceptions_400
def reset_student_attempts_for_entrance_exam(request, course_id):  # pylint: disable=invalid-name
    """

    Resets a students attempts counter or starts a task to reset all students
    attempts counters for entrance exam. Optionally deletes student state for
    entrance exam. Limited to staff access. Some sub-methods limited to instructor access.

    Following are possible query parameters
        - unique_student_identifier is an email or username
        - all_students is a boolean
            requires instructor access
            mutually exclusive with delete_module
        - delete_module is a boolean
            requires instructor access
            mutually exclusive with all_students
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
    )

    if not course.entrance_exam_id:
        return HttpResponseBadRequest(
            _("Course has no entrance exam section.")
        )

    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)
    all_students = request.POST.get('all_students', False) in ['true', 'True', True]
    delete_module = request.POST.get('delete_module', False) in ['true', 'True', True]

    # parameter combinations
    if all_students and student:
        return HttpResponseBadRequest(
            _("all_students and unique_student_identifier are mutually exclusive.")
        )
    if all_students and delete_module:
        return HttpResponseBadRequest(
            _("all_students and delete_module are mutually exclusive.")
        )

    # instructor authorization
    if all_students or delete_module:
        if not has_access(request.user, 'instructor', course):
            return HttpResponseForbidden(_("Requires instructor access."))

    try:
        entrance_exam_key = course_id.make_usage_key_from_deprecated_string(course.entrance_exam_id)
        if delete_module:
            instructor_task.api.submit_delete_entrance_exam_state_for_student(request, entrance_exam_key, student)
        else:
            instructor_task.api.submit_reset_problem_attempts_in_entrance_exam(request, entrance_exam_key, student)
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))

    response_payload = {'student': student_identifier or _('All Students'), 'task': 'created'}
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@require_post_params(problem_to_reset="problem urlname to reset")
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
    problem_to_reset = strip_if_string(request.POST.get('problem_to_reset'))
    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)

    all_students = request.POST.get('all_students') in ['true', 'True', True]

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


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('instructor')
@common_exceptions_400
def rescore_entrance_exam(request, course_id):
    """
    Starts a background process a students attempts counter for entrance exam.
    Optionally deletes student state for a problem. Limited to instructor access.

    Takes either of the following query parameters
        - unique_student_identifier is an email or username
        - all_students is a boolean

    all_students and unique_student_identifier cannot both be present.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
    )

    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)

    all_students = request.POST.get('all_students') in ['true', 'True', True]

    if not course.entrance_exam_id:
        return HttpResponseBadRequest(
            _("Course has no entrance exam section.")
        )

    if all_students and student:
        return HttpResponseBadRequest(
            _("Cannot rescore with all_students and unique_student_identifier.")
        )

    try:
        entrance_exam_key = course_id.make_usage_key_from_deprecated_string(course.entrance_exam_id)
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))

    response_payload = {}
    if student:
        response_payload['student'] = student_identifier
    else:
        response_payload['student'] = _("All Students")
    instructor_task.api.submit_rescore_entrance_exam_for_student(request, entrance_exam_key, student)
    response_payload['task'] = 'created'
    return JsonResponse(response_payload)


@require_POST
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


@require_POST
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


@require_POST
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
    problem_location_str = strip_if_string(request.POST.get('problem_location_str', False))
    student = request.POST.get('unique_student_identifier', None)
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


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_entrance_exam_instructor_tasks(request, course_id):  # pylint: disable=invalid-name
    """
    List entrance exam related instructor tasks.

    Takes either of the following query parameters
        - unique_student_identifier is an email or username
        - all_students is a boolean
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_id)
    student = request.POST.get('unique_student_identifier', None)
    if student is not None:
        student = get_student_from_identifier(student)

    try:
        entrance_exam_key = course_id.make_usage_key_from_deprecated_string(course.entrance_exam_id)
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))
    if student:
        # Specifying for a single student's entrance exam history
        tasks = instructor_task.api.get_entrance_exam_instructor_task_history(course_id, entrance_exam_key, student)
    else:
        # Specifying for all student's entrance exam history
        tasks = instructor_task.api.get_entrance_exam_instructor_task_history(course_id, entrance_exam_key)

    response_payload = {
        'tasks': map(extract_task_features, tasks),
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_report_downloads(_request, course_id):
    """
    List grade CSV files that are available for download for this course.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')

    response_payload = {
        'downloads': [
            dict(name=name, url=url, link=HTML('<a href="{}">{}</a>').format(HTML(url), Text(name)))
            for name, url in report_store.links_for(course_id)
        ]
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_finance_admin
def list_financial_report_downloads(_request, course_id):
    """
    List grade CSV files that are available for download for this course.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    report_store = ReportStore.from_config(config_name='FINANCIAL_REPORTS')

    response_payload = {
        'downloads': [
            dict(name=name, url=url, link=HTML('<a href="{}">{}</a>').format(HTML(url), Text(name)))
            for name, url in report_store.links_for(course_id)
        ]
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def export_ora2_data(request, course_id):
    """
    Pushes a Celery task which will aggregate ora2 responses for a course into a .csv
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_export_ora2_data(request, course_key)
        success_status = _("The ORA data report is being generated.")

        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _(
            "An ORA data report generation task is already in "
            "progress. Check the 'Pending Tasks' table "
            "for the status of the task. When completed, the report "
            "will be available for download in the table below."
        )

        return JsonResponse({"status": already_running_status})


@transaction.non_atomic_requests
@require_POST
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
        success_status = _("The grade report is being created."
                           " To view the status of the report, see Pending Tasks below.")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("The grade report is currently being created."
                                   " To view the status of the report, see Pending Tasks below."
                                   " You will be able to download the report when it is complete.")
        return JsonResponse({"status": already_running_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def problem_grade_report(request, course_id):
    """
    Request a CSV showing students' grades for all problems in the
    course.

    AlreadyRunningError is raised if the course's grades are already being
    updated.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        instructor_task.api.submit_problem_grade_report(request, course_key)
        success_status = _("The problem grade report is being created."
                           " To view the status of the report, see Pending Tasks below.")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("A problem grade report is already being generated."
                                   " To view the status of the report, see Pending Tasks below."
                                   " You will be able to download the report when it is complete.")
        return JsonResponse({
            "status": already_running_status
        })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params('rolename')
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

    rolename = request.POST.get('rolename')

    # default roles require either (staff & forum admin) or (instructor)
    if not (has_forum_admin or has_instructor_access):
        return HttpResponseBadRequest(
            "Operation requires staff & forum admin or instructor access"
        )

    # EXCEPT FORUM_ROLE_ADMINISTRATOR requires (instructor)
    if rolename == FORUM_ROLE_ADMINISTRATOR and not has_instructor_access:
        return HttpResponseBadRequest("Operation requires instructor access.")

    # filter out unsupported for roles
    if rolename not in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]:
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


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params(send_to="sending to whom", subject="subject line", message="message text")
def send_email(request, course_id):
    """
    Send an email to self, staff, cohorts, or everyone involved in a course.
    Query Parameters:
    - 'send_to' specifies what group the email should be sent to
       Options are defined by the CourseEmail model in
       lms/djangoapps/bulk_email/models.py
    - 'subject' specifies email's subject
    - 'message' specifies email's content
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    if not BulkEmailFlag.feature_enabled(course_id):
        return HttpResponseForbidden("Email is not enabled for this course.")

    targets = json.loads(request.POST.get("send_to"))
    subject = request.POST.get("subject")
    message = request.POST.get("message")

    # allow two branding points to come from Site Configuration: which CourseEmailTemplate should be used
    # and what the 'from' field in the email should be
    #
    # If these are None (there is no site configuration enabled for the current site) than
    # the system will use normal system defaults
    template_name = configuration_helpers.get_value('course_email_template_name')
    from_addr = configuration_helpers.get_value('course_email_from_addr')

    # Create the CourseEmail object.  This is saved immediately, so that
    # any transaction that has been pending up to this point will also be
    # committed.
    try:
        email = CourseEmail.create(
            course_id,
            request.user,
            targets,
            subject, message,
            template_name=template_name,
            from_addr=from_addr
        )
    except ValueError as err:
        return HttpResponseBadRequest(repr(err))

    # Submit the task, so that the correct InstructorTask object gets created (for monitoring purposes)
    instructor_task.api.submit_bulk_course_email(request, course_id, email.id)

    response_payload = {
        'course_id': course_id.to_deprecated_string(),
        'success': True,
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params(
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

    unique_student_identifier = request.POST.get('unique_student_identifier')
    rolename = request.POST.get('rolename')
    action = request.POST.get('action')

    # default roles require either (staff & forum admin) or (instructor)
    if not (has_forum_admin or has_instructor_access):
        return HttpResponseBadRequest(
            "Operation requires staff & forum admin or instructor access"
        )

    # EXCEPT FORUM_ROLE_ADMINISTRATOR requires (instructor)
    if rolename == FORUM_ROLE_ADMINISTRATOR and not has_instructor_access:
        return HttpResponseBadRequest("Operation requires instructor access.")

    if rolename not in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]:
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


@require_POST
def get_user_invoice_preference(request, course_id):  # pylint: disable=unused-argument
    """
    Gets invoice copy user's preferences.
    """
    invoice_copy_preference = True
    invoice_preference_value = get_user_preference(request.user, INVOICE_KEY)
    if invoice_preference_value is not None:
        invoice_copy_preference = invoice_preference_value == 'True'

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
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params('student', 'url', 'due_datetime')
def change_due_date(request, course_id):
    """
    Grants a due date extension to a student for a particular unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    student = require_student_from_identifier(request.POST.get('student'))
    unit = find_unit(course, request.POST.get('url'))
    due_date = parse_datetime(request.POST.get('due_datetime'))
    set_due_date_extension(course, unit, student, due_date)

    return JsonResponse(_(
        'Successfully changed due date for student {0} for {1} '
        'to {2}').format(student.profile.name, _display_unit(unit),
                         due_date.strftime('%Y-%m-%d %H:%M')))


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params('student', 'url')
def reset_due_date(request, course_id):
    """
    Rescinds a due date extension for a student on a particular unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    student = require_student_from_identifier(request.POST.get('student'))
    unit = find_unit(course, request.POST.get('url'))
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
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params('url')
def show_unit_extensions(request, course_id):
    """
    Shows all of the students which have due date extensions for the given unit.
    """
    course = get_course_by_id(SlashSeparatedCourseKey.from_deprecated_string(course_id))
    unit = find_unit(course, request.POST.get('url'))
    return JsonResponse(dump_module_extensions(course, unit))


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_post_params('student')
def show_student_extensions(request, course_id):
    """
    Shows all of the due date extensions granted to a particular student in a
    particular course.
    """
    student = require_student_from_identifier(request.POST.get('student'))
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


def _instructor_dash_url(course_key, section=None):
    """Return the URL for a section in the instructor dashboard.

    Arguments:
        course_key (CourseKey)

    Keyword Arguments:
        section (str): The name of the section to load.

    Returns:
        unicode: The URL of a section in the instructor dashboard.

    """
    url = reverse('instructor_dashboard', kwargs={'course_id': unicode(course_key)})
    if section is not None:
        url += u'#view-{section}'.format(section=section)
    return url


@require_global_staff
@require_POST
def generate_example_certificates(request, course_id=None):  # pylint: disable=unused-argument
    """Start generating a set of example certificates.

    Example certificates are used to verify that certificates have
    been configured correctly for the course.

    Redirects back to the intructor dashboard once certificate
    generation has begun.

    """
    course_key = CourseKey.from_string(course_id)
    certs_api.generate_example_certificates(course_key)
    return redirect(_instructor_dash_url(course_key, section='certificates'))


@require_global_staff
@require_POST
def enable_certificate_generation(request, course_id=None):
    """Enable/disable self-generated certificates for a course.

    Once self-generated certificates have been enabled, students
    who have passed the course will be able to generate certificates.

    Redirects back to the intructor dashboard once the
    setting has been updated.

    """
    course_key = CourseKey.from_string(course_id)
    is_enabled = (request.POST.get('certificates-enabled', 'false') == 'true')
    certs_api.set_cert_generation_enabled(course_key, is_enabled)
    return redirect(_instructor_dash_url(course_key, section='certificates'))


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def mark_student_can_skip_entrance_exam(request, course_id):  # pylint: disable=invalid-name
    """
    Mark a student to skip entrance exam.
    Takes `unique_student_identifier` as required POST parameter.
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    student_identifier = request.POST.get('unique_student_identifier')
    student = get_student_from_identifier(student_identifier)

    __, created = EntranceExamConfiguration.objects.get_or_create(user=student, course_id=course_id)
    if created:
        message = _('This student (%s) will skip the entrance exam.') % student_identifier
    else:
        message = _('This student (%s) is already allowed to skip the entrance exam.') % student_identifier
    response_payload = {
        'message': message,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_POST
def start_certificate_generation(request, course_id):
    """
    Start generating certificates for all students enrolled in given course.
    """
    course_key = CourseKey.from_string(course_id)
    task = instructor_task.api.generate_certificates_for_students(request, course_key)
    message = _('Certificate generation task for all students of this course has been started. '
                'You can view the status of the generation task in the "Pending Tasks" section.')
    response_payload = {
        'message': message,
        'task_id': task.task_id
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_POST
def start_certificate_regeneration(request, course_id):
    """
    Start regenerating certificates for students whose certificate statuses lie with in 'certificate_statuses'
    entry in POST data.
    """
    course_key = CourseKey.from_string(course_id)
    certificates_statuses = request.POST.getlist('certificate_statuses', [])
    if not certificates_statuses:
        return JsonResponse(
            {'message': _('Please select one or more certificate statuses that require certificate regeneration.')},
            status=400
        )

    # Check if the selected statuses are allowed
    allowed_statuses = [CertificateStatuses.downloadable, CertificateStatuses.error, CertificateStatuses.notpassing]
    if not set(certificates_statuses).issubset(allowed_statuses):
        return JsonResponse(
            {'message': _('Please select certificate statuses from the list only.')},
            status=400
        )
    try:
        instructor_task.api.regenerate_certificates(request, course_key, certificates_statuses)
    except AlreadyRunningError as error:
        return JsonResponse({'message': error.message}, status=400)

    response_payload = {
        'message': _('Certificate regeneration task has been started. '
                     'You can view the status of the generation task in the "Pending Tasks" section.'),
        'success': True
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_http_methods(['POST', 'DELETE'])
def certificate_exception_view(request, course_id):
    """
    Add/Remove students to/from certificate white list.

    :param request: HttpRequest object
    :param course_id: course identifier of the course for whom to add/remove certificates exception.
    :return: JsonResponse object with success/error message or certificate exception data.
    """
    course_key = CourseKey.from_string(course_id)
    # Validate request data and return error response in case of invalid data
    try:
        certificate_exception, student = parse_request_data_and_get_user(request, course_key)
    except ValueError as error:
        return JsonResponse({'success': False, 'message': error.message}, status=400)

    # Add new Certificate Exception for the student passed in request data
    if request.method == 'POST':
        try:
            exception = add_certificate_exception(course_key, student, certificate_exception)
        except ValueError as error:
            return JsonResponse({'success': False, 'message': error.message}, status=400)
        return JsonResponse(exception)

    # Remove Certificate Exception for the student passed in request data
    elif request.method == 'DELETE':
        try:
            remove_certificate_exception(course_key, student)
        except ValueError as error:
            return JsonResponse({'success': False, 'message': error.message}, status=400)

        return JsonResponse({}, status=204)


def add_certificate_exception(course_key, student, certificate_exception):
    """
    Add a certificate exception to CertificateWhitelist table.
    Raises ValueError in case Student is already white listed.

    :param course_key: identifier of the course whose certificate exception will be added.
    :param student: User object whose certificate exception will be added.
    :param certificate_exception: A dict object containing certificate exception info.
    :return: CertificateWhitelist item in dict format containing certificate exception info.
    """
    if len(CertificateWhitelist.get_certificate_white_list(course_key, student)) > 0:
        raise ValueError(
            _("Student (username/email={user}) already in certificate exception list.").format(user=student.username)
        )

    certificate_white_list, __ = CertificateWhitelist.objects.get_or_create(
        user=student,
        course_id=course_key,
        defaults={
            'whitelist': True,
            'notes': certificate_exception.get('notes', '')
        }
    )

    generated_certificate = GeneratedCertificate.eligible_certificates.filter(
        user=student,
        course_id=course_key,
        status=CertificateStatuses.downloadable,
    ).first()

    exception = dict({
        'id': certificate_white_list.id,
        'user_email': student.email,
        'user_name': student.username,
        'user_id': student.id,
        'certificate_generated': generated_certificate and generated_certificate.created_date.strftime("%B %d, %Y"),
        'created': certificate_white_list.created.strftime("%A, %B %d, %Y"),
    })

    return exception


def remove_certificate_exception(course_key, student):
    """
    Remove certificate exception for given course and student from CertificateWhitelist table and
    invalidate its GeneratedCertificate if present.
    Raises ValueError in case no exception exists for the student in the given course.

    :param course_key: identifier of the course whose certificate exception needs to be removed.
    :param student: User object whose certificate exception needs to be removed.
    :return:
    """
    try:
        certificate_exception = CertificateWhitelist.objects.get(user=student, course_id=course_key)
    except ObjectDoesNotExist:
        raise ValueError(
            _('Certificate exception (user={user}) does not exist in certificate white list. '
              'Please refresh the page and try again.').format(user=student.username)
        )

    try:
        generated_certificate = GeneratedCertificate.objects.get(  # pylint: disable=no-member
            user=student,
            course_id=course_key
        )
        generated_certificate.invalidate()
        log.info(
            u'Certificate invalidated for %s in course %s when removed from certificate exception list',
            student.username,
            course_key
        )
    except ObjectDoesNotExist:
        # Certificate has not been generated yet, so just remove the certificate exception from white list
        pass
    certificate_exception.delete()


def parse_request_data_and_get_user(request, course_key):
    """
        Parse request data into Certificate Exception and User object.
        Certificate Exception is the dict object containing information about certificate exception.

    :param request:
    :param course_key: Course Identifier of the course for whom to process certificate exception
    :return: key-value pairs containing certificate exception data and User object
    """
    certificate_exception = parse_request_data(request)

    user = certificate_exception.get('user_name', '') or certificate_exception.get('user_email', '')
    if not user:
        raise ValueError(_('Student username/email field is required and can not be empty. '
                           'Kindly fill in username/email and then press "Add to Exception List" button.'))
    db_user = get_student(user, course_key)

    return certificate_exception, db_user


def parse_request_data(request):
    """
    Parse and return request data, raise ValueError in case of invalid JSON data.

    :param request: HttpRequest request object.
    :return: dict object containing parsed json data.
    """
    try:
        data = json.loads(request.body or '{}')
    except ValueError:
        raise ValueError(_('The record is not in the correct format. Please add a valid username or email address.'))

    return data


def get_student(username_or_email, course_key):
    """
    Retrieve and return User object from db, raise ValueError
    if user is does not exists or is not enrolled in the given course.

    :param username_or_email: String containing either user name or email of the student.
    :param course_key: CourseKey object identifying the current course.
    :return: User object
    """
    try:
        student = get_user_by_username_or_email(username_or_email)
    except ObjectDoesNotExist:
        raise ValueError(_("{user} does not exist in the LMS. Please check your spelling and retry.").format(
            user=username_or_email
        ))

    # Make Sure the given student is enrolled in the course
    if not CourseEnrollment.is_enrolled(student, course_key):
        raise ValueError(_("{user} is not enrolled in this course. Please check your spelling and retry.")
                         .format(user=username_or_email))
    return student


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_POST
def generate_certificate_exceptions(request, course_id, generate_for=None):
    """
    Generate Certificate for students in the Certificate White List.

    :param request: HttpRequest object,
    :param course_id: course identifier of the course for whom to generate certificates
    :param generate_for: string to identify whether to generate certificates for 'all' or 'new'
            additions to the certificate white-list
    :return: JsonResponse object containing success/failure message and certificate exception data
    """
    course_key = CourseKey.from_string(course_id)

    if generate_for == 'all':
        # Generate Certificates for all white listed students
        students = 'all_whitelisted'

    elif generate_for == 'new':
        students = 'whitelisted_not_generated'

    else:
        # Invalid data, generate_for must be present for all certificate exceptions
        return JsonResponse(
            {
                'success': False,
                'message': _('Invalid data, generate_for must be "new" or "all".'),
            },
            status=400
        )

    instructor_task.api.generate_certificates_for_students(request, course_key, student_set=students)

    response_payload = {
        'success': True,
        'message': _('Certificate generation started for white listed students.'),
    }

    return JsonResponse(response_payload)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_POST
def generate_bulk_certificate_exceptions(request, course_id):  # pylint: disable=invalid-name
    """
    Add Students to certificate white list from the uploaded csv file.
    :return response in dict format.
    {
        general_errors: [errors related to csv file e.g. csv uploading, csv attachment, content reading etc. ],
        row_errors: {
            data_format_error:              [users/data in csv file that are not well formatted],
            user_not_exist:                 [csv with none exiting users in LMS system],
            user_already_white_listed:      [users that are already white listed],
            user_not_enrolled:              [rows with not enrolled users in the given course]
        },
        success: [list of successfully added users to the certificate white list model]
    }
    """
    user_index = 0
    notes_index = 1
    row_errors_key = ['data_format_error', 'user_not_exist', 'user_already_white_listed', 'user_not_enrolled']
    course_key = CourseKey.from_string(course_id)
    students, general_errors, success = [], [], []
    row_errors = {key: [] for key in row_errors_key}

    def build_row_errors(key, _user, row_count):
        """
        inner method to build dict of csv data as row errors.
        """
        row_errors[key].append(_('user "{user}" in row# {row}').format(user=_user, row=row_count))

    if 'students_list' in request.FILES:
        try:
            upload_file = request.FILES.get('students_list')
            if upload_file.name.endswith('.csv'):
                students = [row for row in csv.reader(upload_file.read().splitlines())]
            else:
                general_errors.append(_('Make sure that the file you upload is in CSV format with no '
                                        'extraneous characters or rows.'))

        except Exception:  # pylint: disable=broad-except
            general_errors.append(_('Could not read uploaded file.'))
        finally:
            upload_file.close()

        row_num = 0
        for student in students:
            row_num += 1
            # verify that we have exactly two column in every row either email or username and notes but allow for
            # blank lines
            if len(student) != 2:
                if len(student) > 0:
                    build_row_errors('data_format_error', student[user_index], row_num)
                    log.info(u'invalid data/format in csv row# %s', row_num)
                continue

            user = student[user_index]
            try:
                user = get_user_by_username_or_email(user)
            except ObjectDoesNotExist:
                build_row_errors('user_not_exist', user, row_num)
                log.info(u'student %s does not exist', user)
            else:
                if len(CertificateWhitelist.get_certificate_white_list(course_key, user)) > 0:
                    build_row_errors('user_already_white_listed', user, row_num)
                    log.warning(u'student %s already exist.', user.username)

                # make sure user is enrolled in course
                elif not CourseEnrollment.is_enrolled(user, course_key):
                    build_row_errors('user_not_enrolled', user, row_num)
                    log.warning(u'student %s is not enrolled in course.', user.username)

                else:
                    CertificateWhitelist.objects.create(
                        user=user,
                        course_id=course_key,
                        whitelist=True,
                        notes=student[notes_index]
                    )
                    success.append(_('user "{username}" in row# {row}').format(username=user.username, row=row_num))

    else:
        general_errors.append(_('File is not attached.'))

    results = {
        'general_errors': general_errors,
        'row_errors': row_errors,
        'success': success
    }

    return JsonResponse(results)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_http_methods(['POST', 'DELETE'])
def certificate_invalidation_view(request, course_id):
    """
    Invalidate/Re-Validate students to/from certificate.

    :param request: HttpRequest object
    :param course_id: course identifier of the course for whom to add/remove certificates exception.
    :return: JsonResponse object with success/error message or certificate invalidation data.
    """
    course_key = CourseKey.from_string(course_id)
    # Validate request data and return error response in case of invalid data
    try:
        certificate_invalidation_data = parse_request_data(request)
        certificate = validate_request_data_and_get_certificate(certificate_invalidation_data, course_key)
    except ValueError as error:
        return JsonResponse({'message': error.message}, status=400)

    # Invalidate certificate of the given student for the course course
    if request.method == 'POST':
        try:
            certificate_invalidation = invalidate_certificate(request, certificate, certificate_invalidation_data)
        except ValueError as error:
            return JsonResponse({'message': error.message}, status=400)
        return JsonResponse(certificate_invalidation)

    # Re-Validate student certificate for the course course
    elif request.method == 'DELETE':
        try:
            re_validate_certificate(request, course_key, certificate)
        except ValueError as error:
            return JsonResponse({'message': error.message}, status=400)

        return JsonResponse({}, status=204)


def invalidate_certificate(request, generated_certificate, certificate_invalidation_data):
    """
    Invalidate given GeneratedCertificate and add CertificateInvalidation record for future reference or re-validation.

    :param request: HttpRequest object
    :param generated_certificate: GeneratedCertificate object, the certificate we want to invalidate
    :param certificate_invalidation_data: dict object containing data for CertificateInvalidation.
    :return: dict object containing updated certificate invalidation data.
    """
    if len(CertificateInvalidation.get_certificate_invalidations(
            generated_certificate.course_id,
            generated_certificate.user,
    )) > 0:
        raise ValueError(
            _("Certificate of {user} has already been invalidated. Please check your spelling and retry.").format(
                user=generated_certificate.user.username,
            )
        )

    # Verify that certificate user wants to invalidate is a valid one.
    if not generated_certificate.is_valid():
        raise ValueError(
            _("Certificate for student {user} is already invalid, kindly verify that certificate was generated "
              "for this student and then proceed.").format(user=generated_certificate.user.username)
        )

    # Add CertificateInvalidation record for future reference or re-validation
    certificate_invalidation, __ = CertificateInvalidation.objects.update_or_create(
        generated_certificate=generated_certificate,
        defaults={
            'invalidated_by': request.user,
            'notes': certificate_invalidation_data.get("notes", ""),
            'active': True,
        }
    )

    # Invalidate GeneratedCertificate
    generated_certificate.invalidate()
    return {
        'id': certificate_invalidation.id,
        'user': certificate_invalidation.generated_certificate.user.username,
        'invalidated_by': certificate_invalidation.invalidated_by.username,
        'created': certificate_invalidation.created.strftime("%B %d, %Y"),
        'notes': certificate_invalidation.notes,
    }


def re_validate_certificate(request, course_key, generated_certificate):
    """
    Remove certificate invalidation from db and start certificate generation task for this student.
    Raises ValueError if certificate invalidation is present.

    :param request: HttpRequest object
    :param course_key: CourseKey object identifying the current course.
    :param generated_certificate: GeneratedCertificate object of the student for the given course
    """
    try:
        # Fetch CertificateInvalidation object
        certificate_invalidation = CertificateInvalidation.objects.get(generated_certificate=generated_certificate)
    except ObjectDoesNotExist:
        raise ValueError(_("Certificate Invalidation does not exist, Please refresh the page and try again."))
    else:
        # Deactivate certificate invalidation if it was fetched successfully.
        certificate_invalidation.deactivate()

    # We need to generate certificate only for a single student here
    student = certificate_invalidation.generated_certificate.user
    instructor_task.api.generate_certificates_for_students(
        request, course_key, student_set="specific_student", specific_student_id=student.id
    )


def validate_request_data_and_get_certificate(certificate_invalidation, course_key):
    """
    Fetch and return GeneratedCertificate of the student passed in request data for the given course.

    Raises ValueError in case of missing student username/email or
    if student does not have certificate for the given course.

    :param certificate_invalidation: dict containing certificate invalidation data
    :param course_key: CourseKey object identifying the current course.
    :return: GeneratedCertificate object of the student for the given course
    """
    user = certificate_invalidation.get("user")

    if not user:
        raise ValueError(
            _('Student username/email field is required and can not be empty. '
              'Kindly fill in username/email and then press "Invalidate Certificate" button.')
        )

    student = get_student(user, course_key)

    certificate = GeneratedCertificate.certificate_for_student(student, course_key)
    if not certificate:
        raise ValueError(_(
            "The student {student} does not have certificate for the course {course}. Kindly verify student "
            "username/email and the selected course are correct and try again."
        ).format(student=student.username, course=course_key.course))
    return certificate
