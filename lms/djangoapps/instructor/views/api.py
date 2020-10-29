"""
Instructor Dashboard API views

JSON views which the instructor dashboard requests.

Many of these GETs may become PUTs in the future.
"""


import csv
import json
import logging
import random
import re
import string

import six
import unicodecsv
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from edx_when.api import get_date_for_block
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from six.moves import map, range
from submissions import api as sub_api  # installed from the edx-submissions repository

from lms.djangoapps.instructor_analytics import basic as instructor_analytics_basic
from lms.djangoapps.instructor_analytics import csvs as instructor_analytics_csvs
from lms.djangoapps.instructor_analytics import distributions as instructor_analytics_distributions
from lms.djangoapps.bulk_email.api import is_bulk_email_feature_enabled
from lms.djangoapps.bulk_email.models import CourseEmail
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates import api as certs_api
from lms.djangoapps.certificates.models import (
    CertificateInvalidation,
    CertificateStatuses,
    CertificateWhitelist,
    GeneratedCertificate
)
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_by_id, get_course_with_access
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.discussion.django_comment_client.utils import (
    get_course_discussion_settings,
    get_group_id_for_user,
    get_group_name,
    has_forum_access
)
from lms.djangoapps.instructor import enrollment
from lms.djangoapps.instructor.access import ROLES, allow_access, list_with_level, revoke_access, update_forum_role
from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    get_user_email_language,
    send_beta_role_email,
    send_mail_to_student,
    unenroll_email
)
from lms.djangoapps.instructor.views import INVOICE_KEY
from lms.djangoapps.instructor.views.instructor_task_helpers import extract_email_features, extract_task_features
from lms.djangoapps.instructor_task import api as task_api
from lms.djangoapps.instructor_task.api_helper import AlreadyRunningError, QueueConnectionError
from lms.djangoapps.instructor_task.models import ReportStore
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    Role
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from common.djangoapps.student import auth
from common.djangoapps.student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE,
    ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    EntranceExamConfiguration,
    ManualEnrollmentAudit,
    Registration,
    UserProfile,
    anonymous_id_for_user,
    get_user_by_username_or_email,
    is_email_retired,
    unique_id_for_user
)
from common.djangoapps.student.roles import CourseFinanceAdminRole, CourseSalesAdminRole
from common.djangoapps.util.file import (
    FileValidationException,
    UniversalNewlineIterator,
    course_and_time_based_filename_generator,
    store_uploaded_file
)
from common.djangoapps.util.json_request import JsonResponse, JsonResponseBadRequest
from common.djangoapps.util.views import require_global_staff
from xmodule.modulestore.django import modulestore

from .. import permissions

from .tools import (
    dump_module_extensions,
    dump_student_extensions,
    find_unit,
    get_student_from_identifier,
    handle_dashboard_error,
    parse_datetime,
    require_student_from_identifier,
    set_due_date_extension,
    strip_if_string
)

log = logging.getLogger(__name__)

TASK_SUBMISSION_OK = 'created'

SUCCESS_MESSAGE_TEMPLATE = _(u"The {report_type} report is being created. "
                             "To view the status of the report, see Pending Tasks below.")


def common_exceptions_400(func):
    """
    Catches common exceptions and renders matching 400 errors.
    (decorator without arguments)
    """

    def wrapped(request, *args, **kwargs):
        use_json = (request.is_ajax() or
                    request.META.get("HTTP_ACCEPT", "").startswith("application/json"))
        try:
            return func(request, *args, **kwargs)
        except User.DoesNotExist:
            message = _('User does not exist.')
        except MultipleObjectsReturned:
            message = _('Found a conflict with given identifier. Please try an alternative identifier')
        except (AlreadyRunningError, QueueConnectionError, AttributeError) as err:
            message = six.text_type(err)

        if use_json:
            return JsonResponseBadRequest(message)
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

    def decorator(func):
        def wrapped(*args, **kwargs):
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

            if error_response_data['parameters']:
                return JsonResponse(error_response_data, status=400)
            else:
                return func(*args, **kwargs)
        return wrapped
    return decorator


def require_course_permission(permission):
    """
    Decorator with argument that requires a specific permission of the requesting
    user. If the requirement is not satisfied, returns an
    HttpResponseForbidden (403).

    Assumes that request is in args[0].
    Assumes that course_id is in kwargs['course_id'].
    """
    def decorator(func):
        def wrapped(*args, **kwargs):
            request = args[0]
            course = get_course_by_id(CourseKey.from_string(kwargs['course_id']))

            if request.user.has_perm(permission, course):
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
    def wrapped(request, course_id):

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
    def wrapped(request, course_id):

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
@require_course_permission(permissions.CAN_ENROLL)
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
    as the matching criteria. Note the change of username as a warning message (but not a failure).
    Send a standard enrollment email which is the same as the existing manual enrollment

    -If the username already exists (but not the email), assume it is a different user and fail
    to create the new account.
    The failure will be messaged in a response in the browser.
    """

    if not configuration_helpers.get_value(
            'ALLOW_AUTOMATED_SIGNUPS',
            settings.FEATURES.get('ALLOW_AUTOMATED_SIGNUPS', False),
    ):
        return HttpResponseForbidden()

    course_id = CourseKey.from_string(course_id)
    warnings = []
    row_errors = []
    general_errors = []

    # for white labels we use 'shopping cart' which uses CourseMode.HONOR as
    # course mode for creating course enrollments.
    if CourseMode.is_white_label(course_id):
        course_mode = CourseMode.HONOR
    else:
        course_mode = None

    if 'students_list' in request.FILES:
        students = []

        try:
            upload_file = request.FILES.get('students_list')
            if upload_file.name.endswith('.csv'):
                students = [row for row in csv.reader(upload_file.read().decode('utf-8').splitlines())]
                course = get_course_by_id(course_id)
            else:
                general_errors.append({
                    'username': '', 'email': '',
                    'response': _(
                        'Make sure that the file you upload is in CSV format with no extraneous characters or rows.')
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
                if student:
                    error = _(u'Data in row #{row_num} must have exactly four columns: '
                              'email, username, full name, and country').format(row_num=row_num)
                    general_errors.append({
                        'username': '',
                        'email': '',
                        'response': error
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
                    'username': username,
                    'email': email,
                    'response': _(u'Invalid email {email_address}.').format(email_address=email)
                })
            else:
                if User.objects.filter(email=email).exists():
                    # Email address already exists. assume it is the correct user
                    # and just register the user in the course and send an enrollment email.
                    user = User.objects.get(email=email)

                    # see if it is an exact match with email and username
                    # if it's not an exact match then just display a warning message, but continue onwards
                    if not User.objects.filter(email=email, username=username).exists():
                        warning_message = _(
                            u'An account with email {email} exists but the provided username {username} '
                            u'is different. Enrolling anyway with {email}.'
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
                        enroll_email(course_id=course_id,
                                     student_email=email,
                                     auto_enroll=True,
                                     email_students=True,
                                     email_params=email_params)
                elif is_email_retired(email):
                    # We are either attempting to enroll a retired user or create a new user with an email which is
                    # already associated with a retired account.  Simply block these attempts.
                    row_errors.append({
                        'username': username,
                        'email': email,
                        'response': _(u'Invalid email {email_address}.').format(email_address=email),
                    })
                    log.warning(u'Email address %s is associated with a retired user, so course enrollment was ' +
                                u'blocked.', email)
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
    return ''.join((random.choice(chars) for i in range(length)))


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
            'username': username,
            'email': email,
            'response': _(u'Username {user} already exists.').format(user=username)
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
                'message_type': 'account_creation_and_enrollment',
                'email_address': email,
                'password': password,
                'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
            })
            send_mail_to_student(email, email_params)
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(
                u"Exception '{exception}' raised while sending email to new user.".format(exception=type(ex).__name__)
            )
            errors.append({
                'username': username,
                'email': email,
                'response':
                    _(u"Error '{error}' while sending email to new user (user email={email}). "
                      u"Without the email student would not be able to login. "
                      u"Please contact support for further information.").format(error=type(ex).__name__, email=email),
            })
        else:
            log.info(u'email sent to new created user at %s', email)

    return errors


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_ENROLL)
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
    course_id = CourseKey.from_string(course_id)
    action = request.POST.get('action')
    identifiers_raw = request.POST.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    auto_enroll = _get_boolean_param(request, 'auto_enroll')
    email_students = _get_boolean_param(request, 'email_students')
    reason = request.POST.get('reason')
    role = request.POST.get('role')

    allowed_role_choices = configuration_helpers.get_value('MANUAL_ENROLLMENT_ROLE_CHOICES',
                                                           settings.MANUAL_ENROLLMENT_ROLE_CHOICES)
    if role and role not in allowed_role_choices:
        return JsonResponse(
            {
                'action': action,
                'results': [{'error': True, 'message': 'Not a valid role choice'}],
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
                enrollment_obj = CourseEnrollment.get_enrollment(user, course_id) if user else None

                if before_enrollment:
                    state_transition = ENROLLED_TO_UNENROLLED
                else:
                    if before_allowed:
                        state_transition = ALLOWEDTOENROLL_TO_UNENROLLED
                    else:
                        state_transition = UNENROLLED_TO_UNENROLLED

            else:
                return HttpResponseBadRequest(strip_tags(
                    u"Unrecognized action '{}'".format(action)
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
                request.user, email, state_transition, reason, enrollment_obj, role
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
@require_course_permission(permissions.CAN_BETATEST)
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
    course_id = CourseKey.from_string(course_id)
    action = request.POST.get('action')
    identifiers_raw = request.POST.get('identifiers')
    identifiers = _split_input_list(identifiers_raw)
    email_students = _get_boolean_param(request, 'email_students')
    auto_enroll = _get_boolean_param(request, 'auto_enroll')
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
            user_active = user.is_active

            if action == 'add':
                allow_access(course, user, rolename)
            elif action == 'remove':
                revoke_access(course, user, rolename)
            else:
                return HttpResponseBadRequest(strip_tags(
                    u"Unrecognized action '{}'".format(action)
                ))
        except User.DoesNotExist:
            error = True
            user_does_not_exist = True
            user_active = None
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
                'userDoesNotExist': user_does_not_exist,
                'is_active': user_active
            })

    response_payload = {
        'action': action,
        'results': results,
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EDIT_COURSE_ACCESS)
@require_post_params(
    unique_student_identifier="email or username of user to change access",
    rolename="'instructor', 'staff', 'beta', or 'ccx_coach'",
    action="'allow' or 'revoke'"
)
@common_exceptions_400
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
    course_id = CourseKey.from_string(course_id)
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
        error = strip_tags(u"unknown rolename '{}'".format(rolename))
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
            u"unrecognized action u'{}'".format(action)
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
@require_course_permission(permissions.EDIT_COURSE_ACCESS)
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
    course_id = CourseKey.from_string(course_id)
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
        'course_id': text_type(course_id),
        rolename: list(map(extract_user_info, list_with_level(
            course, rolename
        ))),
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def get_problem_responses(request, course_id):
    """
    Initiate generation of a CSV file containing all student answers
    to a given problem.

    **Example requests**

        POST /courses/{course_id}/instructor/api/get_problem_responses {
            "problem_location": "{usage_key1},{usage_key2},{usage_key3}""
        }
        POST /courses/{course_id}/instructor/api/get_problem_responses {
            "problem_location": "{usage_key}",
            "problem_types_filter": "problem"
        }

        **POST Parameters**

        A POST request can include the following parameters:

        * problem_location: A comma-separated list of usage keys for the blocks
          to include in the report. If the location is a block that contains
          other blocks, (such as the course, section, subsection, or unit blocks)
          then all blocks under that block will be included in the report.
        * problem_types_filter: Optional. A comma-separated list of block types
          to include in the repot. If set, only blocks of the specified types will
          be included in the report.

        To get data on all the poll and survey blocks in a course, you could
        POST the usage key of the course for `problem_location`, and
        "poll, survey" as the value for `problem_types_filter`.


    **Example Response:**
    If initiation is successful (or generation task is already running):
    ```json
    {
        "status": "The problem responses report is being created. ...",
        "task_id": "4e49522f-31d9-431a-9cff-dd2a2bf4c85a"
    }
    ```

    Responds with BadRequest if any of the provided problem locations are faulty.
    """
    course_key = CourseKey.from_string(course_id)
    # A comma-separated list of problem locations
    # The name of the POST parameter is `problem_location` (not pluralised) in
    # order to preserve backwards compatibility with existing third-party
    # scripts.
    problem_locations = request.POST.get('problem_location', '')
    # A comma-separated list of block types
    problem_types_filter = request.POST.get('problem_types_filter', '')
    report_type = _('problem responses')

    try:
        for problem_location in problem_locations.split(','):
            problem_key = UsageKey.from_string(problem_location).map_into_course(course_key)
    except InvalidKeyError:
        return JsonResponseBadRequest(_("Could not find problem with this location."))

    task = task_api.submit_calculate_problem_responses_csv(
        request, course_key, problem_locations, problem_types_filter,
    )
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status, "task_id": task.task_id})


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
def get_grading_config(request, course_id):
    """
    Respond with json which contains a html formatted grade summary.
    """
    course_id = CourseKey.from_string(course_id)
    # course = get_course_with_access(
    #     request.user, 'staff', course_id, depth=None
    # )
    course = get_course_by_id(course_id)

    grading_config_summary = instructor_analytics_basic.dump_grading_context(course)

    response_payload = {
        'course_id': text_type(course_id),
        'grading_config_summary': grading_config_summary,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.VIEW_ISSUED_CERTIFICATES)
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
    certificates_data = instructor_analytics_basic.issued_certificates(course_key, query_features)
    if csv_required.lower() == 'true':
        __, data_rows = instructor_analytics_csvs.format_dictlist(certificates_data, query_features)
        return instructor_analytics_csvs.create_csv_response(
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
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def get_students_features(request, course_id, csv=False):  # pylint: disable=redefined-outer-name
    """
    Respond with json which contains a summary of all enrolled students profile information.

    Responds with JSON
        {"students": [{-student-info-}, ...]}

    TO DO accept requests for different attribute sets.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    report_type = _('enrolled learner profile')
    available_features = instructor_analytics_basic.AVAILABLE_FEATURES

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
            'goals', 'enrollment_mode', 'verification_status',
            'last_login', 'date_joined',
        ]

    # Provide human-friendly and translatable names for these features. These names
    # will be displayed in the table generated in data_download.js. It is not (yet)
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
        'enrollment_mode': _('Enrollment Mode'),
        'verification_status': _('Verification Status'),
        'last_login': _('Last Login'),
        'date_joined': _('Date Joined'),
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
        student_data = instructor_analytics_basic.enrolled_students_features(course_key, query_features)
        response_payload = {
            'course_id': six.text_type(course_key),
            'students': student_data,
            'students_count': len(student_data),
            'queried_features': query_features,
            'feature_names': query_features_names,
            'available_features': available_features,
        }
        return JsonResponse(response_payload)

    else:
        task_api.submit_calculate_students_features_csv(
            request,
            course_key,
            query_features
        )
        success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

        return JsonResponse({"status": success_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def get_students_who_may_enroll(request, course_id):
    """
    Initiate generation of a CSV file containing information about
    students who may enroll in a course.

    Responds with JSON
        {"status": "... status message ..."}

    """
    course_key = CourseKey.from_string(course_id)
    query_features = ['email']
    report_type = _('enrollment')
    task_api.submit_calculate_may_enroll_csv(request, course_key, query_features)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


def _cohorts_csv_validator(file_storage, file_to_validate):
    """
    Verifies that the expected columns are present in the CSV used to add users to cohorts.
    """
    with file_storage.open(file_to_validate) as f:
        if six.PY2:
            reader = unicodecsv.reader(UniversalNewlineIterator(f), encoding='utf-8')
        else:
            reader = csv.reader(f.read().decode('utf-8').splitlines())

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


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@require_course_permission(permissions.ASSIGN_TO_COHORTS)
@common_exceptions_400
def add_users_to_cohorts(request, course_id):
    """
    View method that accepts an uploaded file (using key "uploaded-file")
    containing cohort assignments for users. This method spawns a celery task
    to do the assignments, and a CSV file with results is provided via data downloads.
    """
    course_key = CourseKey.from_string(course_id)

    try:
        __, filename = store_uploaded_file(
            request, 'uploaded-file', ['.csv'],
            course_and_time_based_filename_generator(course_key, "cohorts"),
            max_file_size=2000000,  # limit to 2 MB
            validator=_cohorts_csv_validator
        )
        # The task will assume the default file storage.
        task_api.submit_cohort_students(request, course_key, filename)
    except (FileValidationException, PermissionDenied) as err:
        return JsonResponse({"error": six.text_type(err)}, status=400)

    return JsonResponse()


# The non-atomic decorator is required because this view calls a celery
# task which uses the 'outer_atomic' context manager.
@method_decorator(transaction.non_atomic_requests, name='dispatch')
class CohortCSV(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Submit a CSV file to assign users to cohorts

    **Example Requests**:

        POST /api/cohorts/v1/courses/{course_id}/users/

    **Response Values**
        * Empty as this is executed asynchronously.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, course_key_string):
        """
        View method that accepts an uploaded file (using key "uploaded-file")
        containing cohort assignments for users. This method spawns a celery task
        to do the assignments, and a CSV file with results is provided via data downloads.
        """
        course_key = CourseKey.from_string(course_key_string)
        try:
            __, file_name = store_uploaded_file(
                request, 'uploaded-file', ['.csv'],
                course_and_time_based_filename_generator(course_key, 'cohorts'),
                max_file_size=2000000,  # limit to 2 MB
                validator=_cohorts_csv_validator
            )
            task_api.submit_cohort_students(request, course_key, file_name)
        except (FileValidationException, ValueError) as e:
            raise self.api_error(status.HTTP_400_BAD_REQUEST, str(e), 'failed-validation')
        return Response(status=status.HTTP_204_NO_CONTENT)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.ENROLLMENT_REPORT)
@common_exceptions_400
def get_course_survey_results(request, course_id):
    """
    get the survey results report for the particular course.
    """
    course_key = CourseKey.from_string(course_id)
    report_type = _('survey')
    task_api.submit_course_survey_report(request, course_key)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EXAM_RESULTS)
@common_exceptions_400
def get_proctored_exam_results(request, course_id):
    """
    get the proctored exam resultsreport for the particular course.
    """
    course_key = CourseKey.from_string(course_id)
    report_type = _('proctored exam results')
    task_api.submit_proctored_exam_results_report(request, course_key)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
def get_anon_ids(request, course_id):
    """
    Respond with 2-column CSV output of user-id, anonymized-user-id
    """
    # TODO: the User.objects query and CSV generation here could be
    # centralized into instructor_analytics. Currently instructor_analytics
    # has similar functionality but not quite what's needed.
    course_id = CourseKey.from_string(course_id)

    def csv_response(filename, header, rows):
        """Returns a CSV http response for the given header and rows (excel/utf-8)."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = u'attachment; filename={0}'.format(
            text_type(filename).encode('utf-8') if six.PY2 else text_type(filename)
        )
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        # In practice, there should not be non-ascii data in this query,
        # but trying to do the right thing anyway.
        encoded = [text_type(s) for s in header]
        writer.writerow(encoded)
        for row in rows:
            encoded = [text_type(s) for s in row]
            writer.writerow(encoded)
        return response

    students = User.objects.filter(
        courseenrollment__course_id=course_id,
    ).order_by('id')
    header = ['User ID', 'Anonymized User ID', 'Course Specific Anonymized User ID']
    rows = [[s.id, unique_id_for_user(s, save=False), anonymous_id_for_user(s, course_id, save=False)]
            for s in students]
    return csv_response(text_type(course_id).replace('/', '-') + '-anon-ids.csv', header, rows)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_ENROLL)
@require_post_params(
    unique_student_identifier="email or username of student for whom to get enrollment status"
)
def get_student_enrollment_status(request, course_id):
    """
    Get the enrollment status of a student.
    Limited to staff access.

    Takes query parameter unique_student_identifier
    """

    error = ''
    user = None
    mode = None
    is_active = None

    course_id = CourseKey.from_string(course_id)
    unique_student_identifier = request.POST.get('unique_student_identifier')

    try:
        user = get_student_from_identifier(unique_student_identifier)
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_id)
    except User.DoesNotExist:
        # The student could have been invited to enroll without having
        # registered. We'll also look at CourseEnrollmentAllowed
        # records, so let the lack of a User slide.
        pass

    enrollment_status = _(u'Enrollment status for {student}: unknown').format(student=unique_student_identifier)

    if user and mode:
        if is_active:
            enrollment_status = _(u'Enrollment status for {student}: active').format(student=user)
        else:
            enrollment_status = _(u'Enrollment status for {student}: inactive').format(student=user)
    else:
        email = user.email if user else unique_student_identifier
        allowed = CourseEnrollmentAllowed.may_enroll_and_unenrolled(course_id)
        if allowed and email in [cea.email for cea in allowed]:
            enrollment_status = _(u'Enrollment status for {student}: pending').format(student=email)
        else:
            enrollment_status = _(u'Enrollment status for {student}: never enrolled').format(student=email)

    response_payload = {
        'course_id': text_type(course_id),
        'error': error,
        'enrollment_status': enrollment_status
    }

    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@common_exceptions_400
@require_course_permission(permissions.ENROLLMENT_REPORT)
@require_post_params(
    unique_student_identifier="email or username of student for whom to get progress url"
)
@common_exceptions_400
def get_student_progress_url(request, course_id):
    """
    Get the progress url of a student.
    Limited to staff access.

    Takes query parameter unique_student_identifier and if the student exists
    returns e.g. {
        'progress_url': '/../...'
    }
    """
    course_id = CourseKey.from_string(course_id)
    user = get_student_from_identifier(request.POST.get('unique_student_identifier'))

    progress_url = reverse('student_progress', kwargs={'course_id': text_type(course_id), 'student_id': user.id})

    response_payload = {
        'course_id': text_type(course_id),
        'progress_url': progress_url,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
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
    course_id = CourseKey.from_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
    )
    all_students = _get_boolean_param(request, 'all_students')

    if all_students and not has_access(request.user, 'instructor', course):
        return HttpResponseForbidden("Requires instructor access.")

    problem_to_reset = strip_if_string(request.POST.get('problem_to_reset'))
    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)
    delete_module = _get_boolean_param(request, 'delete_module')

    # parameter combinations
    if all_students and student:
        return HttpResponseBadRequest(
            "all_students and unique_student_identifier are mutually exclusive."
        )
    if all_students and delete_module:
        return HttpResponseBadRequest(
            "all_students and delete_module are mutually exclusive."
        )

    try:
        module_state_key = UsageKey.from_string(problem_to_reset).map_into_course(course_id)
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
        task_api.submit_reset_problem_attempts_for_all_students(request, module_state_key)
        response_payload['task'] = TASK_SUBMISSION_OK
        response_payload['student'] = 'All Students'
    else:
        return HttpResponseBadRequest()

    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
@common_exceptions_400
def reset_student_attempts_for_entrance_exam(request, course_id):
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
    course_id = CourseKey.from_string(course_id)
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
    all_students = _get_boolean_param(request, 'all_students')
    delete_module = _get_boolean_param(request, 'delete_module')

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
        entrance_exam_key = UsageKey.from_string(course.entrance_exam_id).map_into_course(course_id)
        if delete_module:
            task_api.submit_delete_entrance_exam_state_for_student(
                request,
                entrance_exam_key,
                student
            )
        else:
            task_api.submit_reset_problem_attempts_in_entrance_exam(
                request,
                entrance_exam_key,
                student
            )
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))

    response_payload = {'student': student_identifier or _('All Students'), 'task': TASK_SUBMISSION_OK}
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.OVERRIDE_GRADES)
@require_post_params(problem_to_reset="problem urlname to reset")
@common_exceptions_400
def rescore_problem(request, course_id):
    """
    Starts a background process a students attempts counter. Optionally deletes student state for a problem.
    Rescore for all students is limited to instructor access.

    Takes either of the following query paremeters
        - problem_to_reset is a urlname of a problem
        - unique_student_identifier is an email or username
        - all_students is a boolean

    all_students and unique_student_identifier cannot both be present.
    """
    course_id = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'staff', course_id)
    all_students = _get_boolean_param(request, 'all_students')

    if all_students and not has_access(request.user, 'instructor', course):
        return HttpResponseForbidden("Requires instructor access.")

    only_if_higher = _get_boolean_param(request, 'only_if_higher')
    problem_to_reset = strip_if_string(request.POST.get('problem_to_reset'))
    student_identifier = request.POST.get('unique_student_identifier', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)

    if not (problem_to_reset and (all_students or student)):
        return HttpResponseBadRequest("Missing query parameters.")

    if all_students and student:
        return HttpResponseBadRequest(
            "Cannot rescore with all_students and unique_student_identifier."
        )

    try:
        module_state_key = UsageKey.from_string(problem_to_reset).map_into_course(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest("Unable to parse problem id")

    response_payload = {'problem_to_reset': problem_to_reset}

    if student:
        response_payload['student'] = student_identifier
        try:
            task_api.submit_rescore_problem_for_student(
                request,
                module_state_key,
                student,
                only_if_higher,
            )
        except NotImplementedError as exc:
            return HttpResponseBadRequest(text_type(exc))

    elif all_students:
        try:
            task_api.submit_rescore_problem_for_all_students(
                request,
                module_state_key,
                only_if_higher,
            )
        except NotImplementedError as exc:
            return HttpResponseBadRequest(text_type(exc))
    else:
        return HttpResponseBadRequest()

    response_payload['task'] = TASK_SUBMISSION_OK
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.OVERRIDE_GRADES)
@require_post_params(problem_to_reset="problem urlname to reset", score='overriding score')
@common_exceptions_400
def override_problem_score(request, course_id):
    course_key = CourseKey.from_string(course_id)
    score = strip_if_string(request.POST.get('score'))
    problem_to_reset = strip_if_string(request.POST.get('problem_to_reset'))
    student_identifier = request.POST.get('unique_student_identifier', None)

    if not problem_to_reset:
        return HttpResponseBadRequest("Missing query parameter problem_to_reset.")

    if not student_identifier:
        return HttpResponseBadRequest("Missing query parameter student_identifier.")

    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)
    else:
        return _create_error_response(request, u"Invalid student ID {}.".format(student_identifier))

    try:
        usage_key = UsageKey.from_string(problem_to_reset).map_into_course(course_key)
    except InvalidKeyError:
        return _create_error_response(request, u"Unable to parse problem id {}.".format(problem_to_reset))

    # check the user's access to this specific problem
    if not has_access(request.user, "staff", modulestore().get_item(usage_key)):
        _create_error_response(request, u"User {} does not have permission to override scores for problem {}.".format(
            request.user.id,
            problem_to_reset
        ))

    response_payload = {
        'problem_to_reset': problem_to_reset,
        'student': student_identifier
    }
    try:
        task_api.submit_override_score(
            request,
            usage_key,
            student,
            score,
        )
    except NotImplementedError as exc:  # if we try to override the score of a non-scorable block, catch it here
        return _create_error_response(request, text_type(exc))

    except ValueError as exc:
        return _create_error_response(request, text_type(exc))

    response_payload['task'] = TASK_SUBMISSION_OK
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.RESCORE_EXAMS)
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
    course_id = CourseKey.from_string(course_id)
    course = get_course_with_access(
        request.user, 'staff', course_id, depth=None
    )

    student_identifier = request.POST.get('unique_student_identifier', None)
    only_if_higher = request.POST.get('only_if_higher', None)
    student = None
    if student_identifier is not None:
        student = get_student_from_identifier(student_identifier)

    all_students = _get_boolean_param(request, 'all_students')

    if not course.entrance_exam_id:
        return HttpResponseBadRequest(
            _("Course has no entrance exam section.")
        )

    if all_students and student:
        return HttpResponseBadRequest(
            _("Cannot rescore with all_students and unique_student_identifier.")
        )

    try:
        entrance_exam_key = UsageKey.from_string(course.entrance_exam_id).map_into_course(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))

    response_payload = {}
    if student:
        response_payload['student'] = student_identifier
    else:
        response_payload['student'] = _("All Students")

    task_api.submit_rescore_entrance_exam_for_student(
        request, entrance_exam_key, student, only_if_higher,
    )
    response_payload['task'] = TASK_SUBMISSION_OK
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EMAIL)
def list_background_email_tasks(request, course_id):
    """
    List background email tasks.
    """
    course_id = CourseKey.from_string(course_id)
    task_type = 'bulk_course_email'
    # Specifying for the history of a single task type
    tasks = task_api.get_instructor_task_history(
        course_id,
        task_type=task_type
    )

    response_payload = {
        'tasks': list(map(extract_task_features, tasks)),
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EMAIL)
def list_email_content(request, course_id):
    """
    List the content of bulk emails sent
    """
    course_id = CourseKey.from_string(course_id)
    task_type = 'bulk_course_email'
    # First get tasks list of bulk emails sent
    emails = task_api.get_instructor_task_history(course_id, task_type=task_type)

    response_payload = {
        'emails': list(map(extract_email_features, emails)),
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.SHOW_TASKS)
def list_instructor_tasks(request, course_id):
    """
    List instructor tasks.

    Takes optional query paremeters.
        - With no arguments, lists running tasks.
        - `problem_location_str` lists task history for problem
        - `problem_location_str` and `unique_student_identifier` lists task
            history for problem AND student (intersection)
    """
    course_id = CourseKey.from_string(course_id)
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
            module_state_key = UsageKey.from_string(problem_location_str).map_into_course(course_id)
        except InvalidKeyError:
            return HttpResponseBadRequest()
        if student:
            # Specifying for a single student's history on this problem
            tasks = task_api.get_instructor_task_history(course_id, module_state_key, student)
        else:
            # Specifying for single problem's history
            tasks = task_api.get_instructor_task_history(course_id, module_state_key)
    else:
        # If no problem or student, just get currently running tasks
        tasks = task_api.get_running_instructor_tasks(course_id)

    response_payload = {
        'tasks': list(map(extract_task_features, tasks)),
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.SHOW_TASKS)
def list_entrance_exam_instructor_tasks(request, course_id):
    """
    List entrance exam related instructor tasks.

    Takes either of the following query parameters
        - unique_student_identifier is an email or username
        - all_students is a boolean
    """
    course_id = CourseKey.from_string(course_id)
    course = get_course_by_id(course_id)
    student = request.POST.get('unique_student_identifier', None)
    if student is not None:
        student = get_student_from_identifier(student)

    try:
        entrance_exam_key = UsageKey.from_string(course.entrance_exam_id).map_into_course(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest(_("Course has no valid entrance exam section."))
    if student:
        # Specifying for a single student's entrance exam history
        tasks = task_api.get_entrance_exam_instructor_task_history(
            course_id,
            entrance_exam_key,
            student
        )
    else:
        # Specifying for all student's entrance exam history
        tasks = task_api.get_entrance_exam_instructor_task_history(
            course_id,
            entrance_exam_key
        )

    response_payload = {
        'tasks': list(map(extract_task_features, tasks)),
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
def list_report_downloads(request, course_id):
    """
    List grade CSV files that are available for download for this course.

    Takes the following query parameters:
    - (optional) report_name - name of the report
    """
    course_id = CourseKey.from_string(course_id)
    report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
    report_name = request.POST.get("report_name", None)

    response_payload = {
        'downloads': [
            dict(name=name, url=url, link=HTML(u'<a href="{}">{}</a>').format(HTML(url), Text(name)))
            for name, url in report_store.links_for(course_id) if report_name is None or name == report_name
        ]
    }
    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@require_finance_admin
def list_financial_report_downloads(_request, course_id):
    """
    List grade CSV files that are available for download for this course.
    """
    course_id = CourseKey.from_string(course_id)
    report_store = ReportStore.from_config(config_name='FINANCIAL_REPORTS')

    response_payload = {
        'downloads': [
            dict(name=name, url=url, link=HTML(u'<a href="{}">{}</a>').format(HTML(url), Text(name)))
            for name, url in report_store.links_for(course_id)
        ]
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def export_ora2_data(request, course_id):
    """
    Pushes a Celery task which will aggregate ora2 responses for a course into a .csv
    """
    course_key = CourseKey.from_string(course_id)
    report_type = _('ORA data')
    task_api.submit_export_ora2_data(request, course_key)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def export_ora2_submission_files(request, course_id):
    """
    Pushes a Celery task which will download and compress all submission
    files (texts, attachments) into a zip archive.
    """
    course_key = CourseKey.from_string(course_id)

    task_api.submit_export_ora2_submission_files(request, course_key)

    return JsonResponse({
        "status": _(
            "Attachments archive is being created."
        )
    })


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def calculate_grades_csv(request, course_id):
    """
    AlreadyRunningError is raised if the course's grades are already being updated.
    """
    report_type = _('grade')
    course_key = CourseKey.from_string(course_id)
    task_api.submit_calculate_grades_csv(request, course_key)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def problem_grade_report(request, course_id):
    """
    Request a CSV showing students' grades for all problems in the
    course.

    AlreadyRunningError is raised if the course's grades are already being
    updated.
    """
    course_key = CourseKey.from_string(course_id)
    report_type = _('problem grade')
    task_api.submit_problem_grade_report(request, course_key)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_ENROLL)
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
    course_id = CourseKey.from_string(course_id)
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
    if rolename not in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_GROUP_MODERATOR,
                        FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest(strip_tags(
            u"Unrecognized rolename '{}'.".format(rolename)
        ))

    try:
        role = Role.objects.get(name=rolename, course_id=course_id)
        users = role.users.all().order_by('username')
    except Role.DoesNotExist:
        users = []

    course_discussion_settings = get_course_discussion_settings(course_id)

    def extract_user_info(user):
        """ Convert user to dict for json rendering. """
        group_id = get_group_id_for_user(user, course_discussion_settings)
        group_name = get_group_name(group_id, course_discussion_settings)

        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'group_name': group_name,
        }

    response_payload = {
        'course_id': text_type(course_id),
        rolename: list(map(extract_user_info, users)),
        'division_scheme': course_discussion_settings.division_scheme,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EMAIL)
@require_post_params(send_to="sending to whom", subject="subject line", message="message text")
@common_exceptions_400
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
    course_id = CourseKey.from_string(course_id)

    if not is_bulk_email_feature_enabled(course_id):
        log.warning(u'Email is not enabled for course %s', course_id)
        return HttpResponseForbidden("Email is not enabled for this course.")

    targets = json.loads(request.POST.get("send_to"))
    subject = request.POST.get("subject")
    message = request.POST.get("message")

    # allow two branding points to come from Site Configuration: which CourseEmailTemplate should be used
    # and what the 'from' field in the email should be
    #
    # If these are None (there is no site configuration enabled for the current site) than
    # the system will use normal system defaults
    course_overview = CourseOverview.get_from_id(course_id)
    from_addr = configuration_helpers.get_value('course_email_from_addr')
    if isinstance(from_addr, dict):
        # If course_email_from_addr is a dict, we are customizing
        # the email template for each organization that has courses
        # on the site. The dict maps from addresses by org allowing
        # us to find the correct from address to use here.
        from_addr = from_addr.get(course_overview.display_org_with_default)

    template_name = configuration_helpers.get_value('course_email_template_name')
    if isinstance(template_name, dict):
        # If course_email_template_name is a dict, we are customizing
        # the email template for each organization that has courses
        # on the site. The dict maps template names by org allowing
        # us to find the correct template to use here.
        template_name = template_name.get(course_overview.display_org_with_default)

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
        log.exception(u'Cannot create course email for course %s requested by user %s for targets %s',
                      course_id, request.user, targets)
        return HttpResponseBadRequest(repr(err))

    # Submit the task, so that the correct InstructorTask object gets created (for monitoring purposes)
    task_api.submit_bulk_course_email(request, course_id, email.id)

    response_payload = {
        'course_id': text_type(course_id),
        'success': True,
    }

    return JsonResponse(response_payload)


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.EDIT_FORUM_ROLES)
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
    - `rolename` is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_GROUP_MODERATOR,
        FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
    - `action` is one of ['allow', 'revoke']
    """
    course_id = CourseKey.from_string(course_id)
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

    if rolename not in [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_GROUP_MODERATOR,
                        FORUM_ROLE_COMMUNITY_TA]:
        return HttpResponseBadRequest(strip_tags(
            u"Unrecognized rolename '{}'.".format(rolename)
        ))

    user = get_student_from_identifier(unique_student_identifier)

    try:
        update_forum_role(course_id, user, rolename, action)
    except Role.DoesNotExist:
        return HttpResponseBadRequest("Role does not exist.")

    response_payload = {
        'course_id': text_type(course_id),
        'action': action,
    }
    return JsonResponse(response_payload)


@require_POST
def get_user_invoice_preference(request, course_id):
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
        return u'{0} ({1})'.format(name, text_type(unit.location))
    else:
        return text_type(unit.location)


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
@require_post_params('student', 'url', 'due_datetime')
def change_due_date(request, course_id):
    """
    Grants a due date extension to a student for a particular unit.
    """
    course = get_course_by_id(CourseKey.from_string(course_id))
    student = require_student_from_identifier(request.POST.get('student'))
    unit = find_unit(course, request.POST.get('url'))
    due_date = parse_datetime(request.POST.get('due_datetime'))
    reason = strip_tags(request.POST.get('reason', ''))

    set_due_date_extension(course, unit, student, due_date, request.user, reason=reason)

    return JsonResponse(_(
        u'Successfully changed due date for student {0} for {1} '
        u'to {2}').format(student.profile.name, _display_unit(unit),
                          due_date.strftime(u'%Y-%m-%d %H:%M')))


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
@require_post_params('student', 'url')
def reset_due_date(request, course_id):
    """
    Rescinds a due date extension for a student on a particular unit.
    """
    course = get_course_by_id(CourseKey.from_string(course_id))
    student = require_student_from_identifier(request.POST.get('student'))
    unit = find_unit(course, request.POST.get('url'))
    reason = strip_tags(request.POST.get('reason', ''))

    original_due_date = get_date_for_block(course_id, unit.location)

    set_due_date_extension(course, unit, student, None, request.user, reason=reason)
    if not original_due_date:
        # It's possible the normal due date was deleted after an extension was granted:
        return JsonResponse(
            _("Successfully removed invalid due date extension (unit has no due date).")
        )

    original_due_date_str = original_due_date.strftime(u'%Y-%m-%d %H:%M')
    return JsonResponse(_(
        u'Successfully reset due date for student {0} for {1} '
        u'to {2}').format(student.profile.name, _display_unit(unit),
                          original_due_date_str))


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
@require_post_params('url')
def show_unit_extensions(request, course_id):
    """
    Shows all of the students which have due date extensions for the given unit.
    """
    course = get_course_by_id(CourseKey.from_string(course_id))
    unit = find_unit(course, request.POST.get('url'))
    return JsonResponse(dump_module_extensions(course, unit))


@handle_dashboard_error
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GIVE_STUDENT_EXTENSION)
@require_post_params('student')
def show_student_extensions(request, course_id):
    """
    Shows all of the due date extensions granted to a particular student in a
    particular course.
    """
    student = require_student_from_identifier(request.POST.get('student'))
    course = get_course_by_id(CourseKey.from_string(course_id))
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
    url = reverse('instructor_dashboard', kwargs={'course_id': six.text_type(course_key)})
    if section is not None:
        url += u'#view-{section}'.format(section=section)
    return url


@require_global_staff
@require_POST
def generate_example_certificates(request, course_id=None):
    """Start generating a set of example certificates.

    Example certificates are used to verify that certificates have
    been configured correctly for the course.

    Redirects back to the intructor dashboard once certificate
    generation has begun.

    """
    course_key = CourseKey.from_string(course_id)
    certs_api.generate_example_certificates(course_key)
    return redirect(_instructor_dash_url(course_key, section='certificates'))


@require_course_permission(permissions.ENABLE_CERTIFICATE_GENERATION)
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
@require_course_permission(permissions.ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM)
@require_POST
def mark_student_can_skip_entrance_exam(request, course_id):
    """
    Mark a student to skip entrance exam.
    Takes `unique_student_identifier` as required POST parameter.
    """
    course_id = CourseKey.from_string(course_id)
    student_identifier = request.POST.get('unique_student_identifier')
    student = get_student_from_identifier(student_identifier)

    __, created = EntranceExamConfiguration.objects.get_or_create(user=student, course_id=course_id)
    if created:
        message = _(u'This student (%s) will skip the entrance exam.') % student_identifier
    else:
        message = _(u'This student (%s) is already allowed to skip the entrance exam.') % student_identifier
    response_payload = {
        'message': message,
    }
    return JsonResponse(response_payload)


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_global_staff
@require_POST
@common_exceptions_400
def start_certificate_generation(request, course_id):
    """
    Start generating certificates for all students enrolled in given course.
    """
    course_key = CourseKey.from_string(course_id)
    task = task_api.generate_certificates_for_students(request, course_key)
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
@common_exceptions_400
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
    allowed_statuses = [
        CertificateStatuses.downloadable,
        CertificateStatuses.error,
        CertificateStatuses.notpassing,
        CertificateStatuses.audit_passing,
        CertificateStatuses.audit_notpassing,
    ]
    if not set(certificates_statuses).issubset(allowed_statuses):
        return JsonResponse(
            {'message': _('Please select certificate statuses from the list only.')},
            status=400
        )

    task_api.regenerate_certificates(request, course_key, certificates_statuses)
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
        return JsonResponse({'success': False, 'message': text_type(error)}, status=400)

    # Add new Certificate Exception for the student passed in request data
    if request.method == 'POST':
        try:
            exception = add_certificate_exception(course_key, student, certificate_exception)
        except ValueError as error:
            return JsonResponse({'success': False, 'message': text_type(error)}, status=400)
        return JsonResponse(exception)

    # Remove Certificate Exception for the student passed in request data
    elif request.method == 'DELETE':
        try:
            remove_certificate_exception(course_key, student)
        except ValueError as error:
            return JsonResponse({'success': False, 'message': text_type(error)}, status=400)

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
    if CertificateWhitelist.get_certificate_white_list(course_key, student):
        raise ValueError(
            _(u"Student (username/email={user}) already in certificate exception list.").format(user=student.username)
        )

    certificate_white_list, __ = CertificateWhitelist.objects.get_or_create(
        user=student,
        course_id=course_key,
        defaults={
            'whitelist': True,
            'notes': certificate_exception.get('notes', '')
        }
    )
    log.info(u'%s has been added to the whitelist in course %s', student.username, course_key)

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
        'certificate_generated': generated_certificate and generated_certificate.created_date.strftime(u"%B %d, %Y"),
        'created': certificate_white_list.created.strftime(u"%A, %B %d, %Y"),
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
            _(u'Certificate exception (user={user}) does not exist in certificate white list. '
              'Please refresh the page and try again.').format(user=student.username)
        )

    try:
        generated_certificate = GeneratedCertificate.objects.get(
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
    log.info(u'%s has been removed from the whitelist in course %s', student.username, course_key)
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
        data = json.loads(request.body.decode('utf8') or u'{}')
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
        raise ValueError(_(u"{user} does not exist in the LMS. Please check your spelling and retry.").format(
            user=username_or_email
        ))

    # Make Sure the given student is enrolled in the course
    if not CourseEnrollment.is_enrolled(student, course_key):
        raise ValueError(_(u"{user} is not enrolled in this course. Please check your spelling and retry.")
                         .format(user=username_or_email))
    return student


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GENERATE_CERTIFICATE_EXCEPTIONS)
@require_POST
@common_exceptions_400
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

    task_api.generate_certificates_for_students(request, course_key, student_set=students)
    response_payload = {
        'success': True,
        'message': _('Certificate generation started for white listed students.'),
    }

    return JsonResponse(response_payload)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.GENERATE_BULK_CERTIFICATE_EXCEPTIONS)
@require_POST
def generate_bulk_certificate_exceptions(request, course_id):
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
        row_errors[key].append(_(u'user "{user}" in row# {row}').format(user=_user, row=row_count))

    if 'students_list' in request.FILES:
        try:
            upload_file = request.FILES.get('students_list')
            if upload_file.name.endswith('.csv'):
                students = [row for row in csv.reader(upload_file.read().decode('utf-8').splitlines())]
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
                if student:
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
                if CertificateWhitelist.get_certificate_white_list(course_key, user):
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
                    success.append(_(u'user "{username}" in row# {row}').format(username=user.username, row=row_num))

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
        return JsonResponse({'message': text_type(error)}, status=400)

    # Invalidate certificate of the given student for the course course
    if request.method == 'POST':
        try:
            certificate_invalidation = invalidate_certificate(request, certificate, certificate_invalidation_data)
        except ValueError as error:
            return JsonResponse({'message': text_type(error)}, status=400)
        return JsonResponse(certificate_invalidation)

    # Re-Validate student certificate for the course course
    elif request.method == 'DELETE':
        try:
            re_validate_certificate(request, course_key, certificate)
        except ValueError as error:
            return JsonResponse({'message': text_type(error)}, status=400)

        return JsonResponse({}, status=204)


def invalidate_certificate(request, generated_certificate, certificate_invalidation_data):
    """
    Invalidate given GeneratedCertificate and add CertificateInvalidation record for future reference or re-validation.

    :param request: HttpRequest object
    :param generated_certificate: GeneratedCertificate object, the certificate we want to invalidate
    :param certificate_invalidation_data: dict object containing data for CertificateInvalidation.
    :return: dict object containing updated certificate invalidation data.
    """
    if CertificateInvalidation.get_certificate_invalidations(
            generated_certificate.course_id,
            generated_certificate.user,
    ):
        raise ValueError(
            _(u"Certificate of {user} has already been invalidated. Please check your spelling and retry.").format(
                user=generated_certificate.user.username,
            )
        )

    # Verify that certificate user wants to invalidate is a valid one.
    if not generated_certificate.is_valid():
        raise ValueError(
            _(u"Certificate for student {user} is already invalid, kindly verify that certificate was generated "
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
        'created': certificate_invalidation.created.strftime(u"%B %d, %Y"),
        'notes': certificate_invalidation.notes,
    }


@common_exceptions_400
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

    task_api.generate_certificates_for_students(
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
            u"The student {student} does not have certificate for the course {course}. Kindly verify student "
            "username/email and the selected course are correct and try again."
        ).format(student=student.username, course=course_key.course))
    return certificate


def _get_boolean_param(request, param_name):
    """
    Returns the value of the boolean parameter with the given
    name in the POST request. Handles translation from string
    values to boolean values.
    """
    return request.POST.get(param_name, False) in ['true', 'True', True]


def _create_error_response(request, msg):
    """
    Creates the appropriate error response for the current request,
    in JSON form.
    """
    return JsonResponse({"error": msg}, 400)
