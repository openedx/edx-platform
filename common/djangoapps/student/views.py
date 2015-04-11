"""
Student Views
"""
import datetime
import logging
import uuid
import time
import json
import warnings
from collections import defaultdict
from pytz import UTC
from ipware.ip import get_ip

from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_reset_confirm
from django.contrib import messages
from django.core.context_processors import csrf
from django.core import mail
from django.core.urlresolvers import reverse
from django.core.validators import validate_email, ValidationError
from django.db import IntegrityError, transaction
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseForbidden,
                         HttpResponseServerError, Http404)
from django.shortcuts import redirect
from django.utils.translation import ungettext
from django_future.csrf import ensure_csrf_cookie
from django.utils.http import cookie_date, base36_to_int
from django.utils.translation import ugettext as _, get_language
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.template.response import TemplateResponse

from ratelimitbackend.exceptions import RateLimitException

from requests import HTTPError

from social.apps.django_app import utils as social_utils
from social.backends import oauth as social_oauth
from social.exceptions import AuthException, AuthAlreadyAssociated

from edxmako.shortcuts import render_to_response, render_to_string

from course_modes.models import CourseMode
from shoppingcart.api import order_history
from student.models import (
    Registration, UserProfile, PendingNameChange,
    PendingEmailChange, CourseEnrollment, unique_id_for_user,
    CourseEnrollmentAllowed, UserStanding, LoginFailures,
    create_comments_service_user, PasswordHistory, UserSignupSource,
    DashboardConfiguration, LinkedInAddToProfileConfiguration)
from student.forms import AccountCreationForm, PasswordResetFormNoActive

from verify_student.models import SoftwareSecurePhotoVerification, MidcourseReverificationWindow
from certificates.models import CertificateStatuses, certificate_status_for_student
from dark_lang.models import DarkLangConfig

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore import ModuleStoreEnum

from collections import namedtuple

from courseware.courses import get_courses, sort_by_announcement, sort_by_start_date  # pylint: disable=import-error
from courseware.access import has_access

from django_comment_common.models import Role

from external_auth.models import ExternalAuthMap
import external_auth.views
from external_auth.login_and_register import (
    login as external_auth_login,
    register as external_auth_register
)

from bulk_email.models import Optout, CourseAuthorization
import shoppingcart
from lang_pref import LANGUAGE_KEY

import track.views

import dogstats_wrapper as dog_stats_api

from util.db import commit_on_success_with_read_committed
from util.json_request import JsonResponse
from util.bad_request_rate_limiter import BadRequestRateLimiter
from util.milestones_helpers import (
    get_pre_requisite_courses_not_completed,
)
from microsite_configuration import microsite

from util.password_policy_validators import (
    validate_password_length, validate_password_complexity,
    validate_password_dictionary
)

import third_party_auth
from third_party_auth import pipeline, provider
from student.helpers import (
    auth_pipeline_urls, set_logged_in_cookie,
    check_verify_status_by_course
)
from xmodule.error_module import ErrorDescriptor
from shoppingcart.models import DonationConfiguration, CourseRegistrationCode

from embargo import api as embargo_api

import analytics
from eventtracking import tracker

# Note that this lives in LMS, so this dependency should be refactored.
from notification_prefs.views import enable_notifications

# Note that this lives in openedx, so this dependency should be refactored.
from openedx.core.djangoapps.user_api.preferences import api as preferences_api


log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")

ReverifyInfo = namedtuple('ReverifyInfo', 'course_id course_name course_number date status display')  # pylint: disable=invalid-name


def csrf_token(context):
    """A csrf token that can be included in a form."""
    token = context.get('csrf_token', '')
    if token == 'NOTPROVIDED':
        return ''
    return (u'<div style="display:none"><input type="hidden"'
            ' name="csrfmiddlewaretoken" value="%s" /></div>' % (token))


# NOTE: This view is not linked to directly--it is called from
# branding/views.py:index(), which is cached for anonymous users.
# This means that it should always return the same thing for anon
# users. (in particular, no switching based on query params allowed)
def index(request, extra_context=None, user=AnonymousUser()):
    """
    Render the edX main page.

    extra_context is used to allow immediate display of certain modal windows, eg signup,
    as used by external_auth.
    """
    if extra_context is None:
        extra_context = {}
    # The course selection work is done in courseware.courses.
    domain = settings.FEATURES.get('FORCE_UNIVERSITY_DOMAIN')  # normally False
    # do explicit check, because domain=None is valid
    if domain is False:
        domain = request.META.get('HTTP_HOST')

    courses = get_courses(user, domain=domain)
    if microsite.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                           settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
        courses = sort_by_start_date(courses)
    else:
        courses = sort_by_announcement(courses)

    context = {'courses': courses}

    context.update(extra_context)
    return render_to_response('index.html', context)


def process_survey_link(survey_link, user):
    """
    If {UNIQUE_ID} appears in the link, replace it with a unique id for the user.
    Currently, this is sha1(user.username).  Otherwise, return survey_link.
    """
    return survey_link.format(UNIQUE_ID=unique_id_for_user(user))


def cert_info(user, course, course_mode):
    """
    Get the certificate info needed to render the dashboard section for the given
    student and course.  Returns a dictionary with keys:

    'status': one of 'generating', 'ready', 'notpassing', 'processing', 'restricted'
    'show_download_url': bool
    'download_url': url, only present if show_download_url is True
    'show_disabled_download_button': bool -- true if state is 'generating'
    'show_survey_button': bool
    'survey_url': url, only if show_survey_button is True
    'grade': if status is not 'processing'
    """
    if not course.may_certify():
        return {}

    return _cert_info(user, course, certificate_status_for_student(user, course.id), course_mode)


def reverification_info(course_enrollment_pairs, user, statuses):
    """
    Returns reverification-related information for *all* of user's enrollments whose
    reverification status is in status_list

    Args:
        course_enrollment_pairs (list): list of (course, enrollment) tuples
        user (User): the user whose information we want
        statuses (list): a list of reverification statuses we want information for
            example: ["must_reverify", "denied"]

    Returns:
        dictionary of lists: dictionary with one key per status, e.g.
            dict["must_reverify"] = []
            dict["must_reverify"] = [some information]
    """
    reverifications = defaultdict(list)
    for (course, enrollment) in course_enrollment_pairs:
        info = single_course_reverification_info(user, course, enrollment)
        if info:
            reverifications[info.status].append(info)

    # Sort the data by the reverification_end_date
    for status in statuses:
        if reverifications[status]:
            reverifications[status].sort(key=lambda x: x.date)
    return reverifications


def single_course_reverification_info(user, course, enrollment):  # pylint: disable=invalid-name
    """Returns midcourse reverification-related information for user with enrollment in course.

    If a course has an open re-verification window, and that user has a verified enrollment in
    the course, we return a tuple with relevant information. Returns None if there is no info..

    Args:
        user (User): the user we want to get information for
        course (Course): the course in which the student is enrolled
        enrollment (CourseEnrollment): the object representing the type of enrollment user has in course

    Returns:
        ReverifyInfo: (course_id, course_name, course_number, date, status)
        OR, None: None if there is no re-verification info for this enrollment
    """
    window = MidcourseReverificationWindow.get_window(course.id, datetime.datetime.now(UTC))

    # If there's no window OR the user is not verified, we don't get reverification info
    if (not window) or (enrollment.mode != "verified"):
        return None
    return ReverifyInfo(
        course.id, course.display_name, course.number,
        window.end_date.strftime('%B %d, %Y %X %p'),
        SoftwareSecurePhotoVerification.user_status(user, window)[0],
        SoftwareSecurePhotoVerification.display_status(user, window),
    )


def get_course_enrollment_pairs(user, course_org_filter, org_filter_out_set):
    """
    Get the relevant set of (Course, CourseEnrollment) pairs to be displayed on
    a student's dashboard.
    """
    for enrollment in CourseEnrollment.enrollments_for_user(user):
        store = modulestore()
        with store.bulk_operations(enrollment.course_id):
            course = store.get_course(enrollment.course_id)
            if course and not isinstance(course, ErrorDescriptor):

                # if we are in a Microsite, then filter out anything that is not
                # attributed (by ORG) to that Microsite
                if course_org_filter and course_org_filter != course.location.org:
                    continue
                # Conversely, if we are not in a Microsite, then let's filter out any enrollments
                # with courses attributed (by ORG) to Microsites
                elif course.location.org in org_filter_out_set:
                    continue

                yield (course, enrollment)
            else:
                log.error(
                    u"User %s enrolled in %s course %s",
                    user.username,
                    "broken" if course else "non-existent",
                    enrollment.course_id
                )


def _cert_info(user, course, cert_status, course_mode):
    """
    Implements the logic for cert_info -- split out for testing.
    """
    # simplify the status for the template using this lookup table
    template_state = {
        CertificateStatuses.generating: 'generating',
        CertificateStatuses.regenerating: 'generating',
        CertificateStatuses.downloadable: 'ready',
        CertificateStatuses.notpassing: 'notpassing',
        CertificateStatuses.restricted: 'restricted',
    }

    default_status = 'processing'

    default_info = {'status': default_status,
                    'show_disabled_download_button': False,
                    'show_download_url': False,
                    'show_survey_button': False,
                    }

    if cert_status is None:
        return default_info

    is_hidden_status = cert_status['status'] in ('unavailable', 'processing', 'generating', 'notpassing')

    if course.certificates_display_behavior == 'early_no_info' and is_hidden_status:
        return None

    status = template_state.get(cert_status['status'], default_status)

    status_dict = {
        'status': status,
        'show_download_url': status == 'ready',
        'show_disabled_download_button': status == 'generating',
        'mode': cert_status.get('mode', None),
        'linked_in_url': None
    }

    if (status in ('generating', 'ready', 'notpassing', 'restricted') and
            course.end_of_course_survey_url is not None):
        status_dict.update({
            'show_survey_button': True,
            'survey_url': process_survey_link(course.end_of_course_survey_url, user)})
    else:
        status_dict['show_survey_button'] = False

    if status == 'ready':
        if 'download_url' not in cert_status:
            log.warning(
                u"User %s has a downloadable cert for %s, but no download url",
                user.username,
                course.id
            )
            return default_info
        else:
            status_dict['download_url'] = cert_status['download_url']

            # If enabled, show the LinkedIn "add to profile" button
            # Clicking this button sends the user to LinkedIn where they
            # can add the certificate information to their profile.
            linkedin_config = LinkedInAddToProfileConfiguration.current()
            if linkedin_config.enabled:
                status_dict['linked_in_url'] = linkedin_config.add_to_profile_url(
                    course.id,
                    course.display_name,
                    cert_status.get('mode'),
                    cert_status['download_url']
                )

    if status in ('generating', 'ready', 'notpassing', 'restricted'):
        if 'grade' not in cert_status:
            # Note: as of 11/20/2012, we know there are students in this state-- cs169.1x,
            # who need to be regraded (we weren't tracking 'notpassing' at first).
            # We can add a log.warning here once we think it shouldn't happen.
            return default_info
        else:
            status_dict['grade'] = cert_status['grade']

    return status_dict


@ensure_csrf_cookie
def signin_user(request):
    """Deprecated. To be replaced by :class:`student_account.views.login_and_registration_form`."""
    external_auth_response = external_auth_login(request)
    if external_auth_response is not None:
        return external_auth_response
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    course_id = request.GET.get('course_id')
    email_opt_in = request.GET.get('email_opt_in')
    context = {
        'course_id': course_id,
        'email_opt_in': email_opt_in,
        'enrollment_action': request.GET.get('enrollment_action'),
        # Bool injected into JS to submit form if we're inside a running third-
        # party auth pipeline; distinct from the actual instance of the running
        # pipeline, if any.
        'pipeline_running': 'true' if pipeline.running(request) else 'false',
        'pipeline_url': auth_pipeline_urls(pipeline.AUTH_ENTRY_LOGIN, course_id=course_id, email_opt_in=email_opt_in),
        'platform_name': microsite.get_value(
            'platform_name',
            settings.PLATFORM_NAME
        ),
    }

    return render_to_response('login.html', context)


@ensure_csrf_cookie
def register_user(request, extra_context=None):
    """Deprecated. To be replaced by :class:`student_account.views.login_and_registration_form`."""
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    external_auth_response = external_auth_register(request)
    if external_auth_response is not None:
        return external_auth_response

    course_id = request.GET.get('course_id')
    email_opt_in = request.GET.get('email_opt_in')

    context = {
        'course_id': course_id,
        'email_opt_in': email_opt_in,
        'email': '',
        'enrollment_action': request.GET.get('enrollment_action'),
        'name': '',
        'running_pipeline': None,
        'pipeline_urls': auth_pipeline_urls(pipeline.AUTH_ENTRY_REGISTER, course_id=course_id, email_opt_in=email_opt_in),
        'platform_name': microsite.get_value(
            'platform_name',
            settings.PLATFORM_NAME
        ),
        'selected_provider': '',
        'username': '',
    }

    if extra_context is not None:
        context.update(extra_context)

    if context.get("extauth_domain", '').startswith(external_auth.views.SHIBBOLETH_DOMAIN_PREFIX):
        return render_to_response('register-shib.html', context)

    # If third-party auth is enabled, prepopulate the form with data from the
    # selected provider.
    if third_party_auth.is_enabled() and pipeline.running(request):
        running_pipeline = pipeline.get(request)
        current_provider = provider.Registry.get_by_backend_name(running_pipeline.get('backend'))
        overrides = current_provider.get_register_form_data(running_pipeline.get('kwargs'))
        overrides['running_pipeline'] = running_pipeline
        overrides['selected_provider'] = current_provider.NAME
        context.update(overrides)

    return render_to_response('register.html', context)


def complete_course_mode_info(course_id, enrollment, modes=None):
    """
    We would like to compute some more information from the given course modes
    and the user's current enrollment

    Returns the given information:
        - whether to show the course upsell information
        - numbers of days until they can't upsell anymore
    """
    if modes is None:
        modes = CourseMode.modes_for_course_dict(course_id)

    mode_info = {'show_upsell': False, 'days_for_upsell': None}
    # we want to know if the user is already verified and if verified is an
    # option
    if 'verified' in modes and enrollment.mode != 'verified':
        mode_info['show_upsell'] = True
        # if there is an expiration date, find out how long from now it is
        if modes['verified'].expiration_datetime:
            today = datetime.datetime.now(UTC).date()
            mode_info['days_for_upsell'] = (modes['verified'].expiration_datetime.date() - today).days

    return mode_info


def is_course_blocked(request, redeemed_registration_codes, course_key):
    """Checking either registration is blocked or not ."""
    blocked = False
    for redeemed_registration in redeemed_registration_codes:
        # registration codes may be generated via Bulk Purchase Scenario
        # we have to check only for the invoice generated registration codes
        # that their invoice is valid or not
        if redeemed_registration.invoice_item:
            if not getattr(redeemed_registration.invoice_item.invoice, 'is_valid'):
                blocked = True
                # disabling email notifications for unpaid registration courses
                Optout.objects.get_or_create(user=request.user, course_id=course_key)
                log.info(
                    u"User %s (%s) opted out of receiving emails from course %s",
                    request.user.username,
                    request.user.email,
                    course_key
                )
                track.views.server_track(request, "change-email1-settings", {"receive_emails": "no", "course": course_key.to_deprecated_string()}, page='dashboard')
                break

    return blocked


@login_required
@ensure_csrf_cookie
def dashboard(request):
    user = request.user

    platform_name = microsite.get_value("platform_name", settings.PLATFORM_NAME)

    # for microsites, we want to filter and only show enrollments for courses within
    # the microsites 'ORG'
    course_org_filter = microsite.get_value('course_org_filter')

    # Let's filter out any courses in an "org" that has been declared to be
    # in a Microsite
    org_filter_out_set = microsite.get_all_orgs()

    # remove our current Microsite from the "filter out" list, if applicable
    if course_org_filter:
        org_filter_out_set.remove(course_org_filter)

    # Build our (course, enrollment) list for the user, but ignore any courses that no
    # longer exist (because the course IDs have changed). Still, we don't delete those
    # enrollments, because it could have been a data push snafu.
    course_enrollment_pairs = list(get_course_enrollment_pairs(user, course_org_filter, org_filter_out_set))

    # sort the enrollment pairs by the enrollment date
    course_enrollment_pairs.sort(key=lambda x: x[1].created, reverse=True)

    # Retrieve the course modes for each course
    enrolled_course_ids = [course.id for course, __ in course_enrollment_pairs]
    all_course_modes, unexpired_course_modes = CourseMode.all_and_unexpired_modes_for_courses(enrolled_course_ids)
    course_modes_by_course = {
        course_id: {
            mode.slug: mode
            for mode in modes
        }
        for course_id, modes in unexpired_course_modes.iteritems()
    }

    # Check to see if the student has recently enrolled in a course.
    # If so, display a notification message confirming the enrollment.
    enrollment_message = _create_recent_enrollment_message(
        course_enrollment_pairs, course_modes_by_course
    )

    course_optouts = Optout.objects.filter(user=user).values_list('course_id', flat=True)

    message = ""
    if not user.is_active:
        message = render_to_string(
            'registration/activate_account_notice.html',
            {'email': user.email, 'platform_name': platform_name}
        )

    # Global staff can see what courses errored on their dashboard
    staff_access = False
    errored_courses = {}
    if has_access(user, 'staff', 'global'):
        # Show any courses that errored on load
        staff_access = True
        errored_courses = modulestore().get_errored_courses()

    show_courseware_links_for = frozenset(
        course.id for course, _enrollment in course_enrollment_pairs
        if has_access(request.user, 'load', course)
        and has_access(request.user, 'view_courseware_with_prerequisites', course)
    )

    # Construct a dictionary of course mode information
    # used to render the course list.  We re-use the course modes dict
    # we loaded earlier to avoid hitting the database.
    course_mode_info = {
        course.id: complete_course_mode_info(
            course.id, enrollment,
            modes=course_modes_by_course[course.id]
        )
        for course, enrollment in course_enrollment_pairs
    }

    # Determine the per-course verification status
    # This is a dictionary in which the keys are course locators
    # and the values are one of:
    #
    # VERIFY_STATUS_NEED_TO_VERIFY
    # VERIFY_STATUS_SUBMITTED
    # VERIFY_STATUS_APPROVED
    # VERIFY_STATUS_MISSED_DEADLINE
    #
    # Each of which correspond to a particular message to display
    # next to the course on the dashboard.
    #
    # If a course is not included in this dictionary,
    # there is no verification messaging to display.
    verify_status_by_course = check_verify_status_by_course(
        user,
        course_enrollment_pairs,
        all_course_modes
    )
    cert_statuses = {
        course.id: cert_info(request.user, course, _enrollment.mode)
        for course, _enrollment in course_enrollment_pairs
    }

    # only show email settings for Mongo course and when bulk email is turned on
    show_email_settings_for = frozenset(
        course.id for course, _enrollment in course_enrollment_pairs if (
            settings.FEATURES['ENABLE_INSTRUCTOR_EMAIL'] and
            modulestore().get_modulestore_type(course.id) != ModuleStoreEnum.Type.xml and
            CourseAuthorization.instructor_email_enabled(course.id)
        )
    )

    # Verification Attempts
    # Used to generate the "you must reverify for course x" banner
    verification_status, verification_msg = SoftwareSecurePhotoVerification.user_status(user)

    # Gets data for midcourse reverifications, if any are necessary or have failed
    statuses = ["approved", "denied", "pending", "must_reverify"]
    reverifications = reverification_info(course_enrollment_pairs, user, statuses)

    show_refund_option_for = frozenset(course.id for course, _enrollment in course_enrollment_pairs
                                       if _enrollment.refundable())

    block_courses = frozenset(course.id for course, enrollment in course_enrollment_pairs
                              if is_course_blocked(request, CourseRegistrationCode.objects.filter(course_id=course.id, registrationcoderedemption__redeemed_by=request.user), course.id))

    enrolled_courses_either_paid = frozenset(course.id for course, _enrollment in course_enrollment_pairs
                                             if _enrollment.is_paid_course())
    # get info w.r.t ExternalAuthMap
    external_auth_map = None
    try:
        external_auth_map = ExternalAuthMap.objects.get(user=user)
    except ExternalAuthMap.DoesNotExist:
        pass

    # If there are *any* denied reverifications that have not been toggled off,
    # we'll display the banner
    denied_banner = any(item.display for item in reverifications["denied"])

    language_options = DarkLangConfig.current().released_languages_list

    # add in the default language if it's not in the list of released languages
    if settings.LANGUAGE_CODE not in language_options:
        language_options.append(settings.LANGUAGE_CODE)
        # Re-alphabetize language options
        language_options.sort()

    # try to get the preferred language for the user
    preferred_language_code = preferences_api.get_user_preference(request.user, LANGUAGE_KEY)
    # try and get the current language of the user
    current_language_code = get_language()
    if preferred_language_code and preferred_language_code in settings.LANGUAGE_DICT:
        # if the user has a preference, get the name from the code
        current_language = settings.LANGUAGE_DICT[preferred_language_code]
    elif current_language_code in settings.LANGUAGE_DICT:
        # if the user's browser is showing a particular language,
        # use that as the current language
        current_language = settings.LANGUAGE_DICT[current_language_code]
    else:
        # otherwise, use the default language
        current_language = settings.LANGUAGE_DICT[settings.LANGUAGE_CODE]

    # Populate the Order History for the side-bar.
    order_history_list = order_history(user, course_org_filter=course_org_filter, org_filter_out_set=org_filter_out_set)

    # get list of courses having pre-requisites yet to be completed
    courses_having_prerequisites = frozenset(course.id for course, _enrollment in course_enrollment_pairs
                                             if course.pre_requisite_courses)
    courses_requirements_not_met = get_pre_requisite_courses_not_completed(user, courses_having_prerequisites)

    ccx_membership_triplets = []
    if settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
        from ccx import ACTIVE_CCX_KEY
        from ccx.utils import get_ccx_membership_triplets
        ccx_membership_triplets = get_ccx_membership_triplets(
            user, course_org_filter, org_filter_out_set
        )
        # should we deselect any active CCX at this time so that we don't have
        # to change the URL for viewing a course?  I think so.
        request.session[ACTIVE_CCX_KEY] = None

    context = {
        'enrollment_message': enrollment_message,
        'course_enrollment_pairs': course_enrollment_pairs,
        'course_optouts': course_optouts,
        'message': message,
        'external_auth_map': external_auth_map,
        'staff_access': staff_access,
        'errored_courses': errored_courses,
        'show_courseware_links_for': show_courseware_links_for,
        'all_course_modes': course_mode_info,
        'cert_statuses': cert_statuses,
        'show_email_settings_for': show_email_settings_for,
        'reverifications': reverifications,
        'verification_status': verification_status,
        'verification_status_by_course': verify_status_by_course,
        'verification_msg': verification_msg,
        'show_refund_option_for': show_refund_option_for,
        'block_courses': block_courses,
        'denied_banner': denied_banner,
        'billing_email': settings.PAYMENT_SUPPORT_EMAIL,
        'language_options': language_options,
        'current_language': current_language,
        'current_language_code': current_language_code,
        'user': user,
        'duplicate_provider': None,
        'logout_url': reverse(logout_user),
        'platform_name': platform_name,
        'enrolled_courses_either_paid': enrolled_courses_either_paid,
        'provider_states': [],
        'order_history_list': order_history_list,
        'courses_requirements_not_met': courses_requirements_not_met,
        'ccx_membership_triplets': ccx_membership_triplets,
    }

    if third_party_auth.is_enabled():
        context['duplicate_provider'] = pipeline.get_duplicate_provider(messages.get_messages(request))
        context['provider_user_states'] = pipeline.get_provider_user_states(user)

    return render_to_response('dashboard.html', context)


def _create_recent_enrollment_message(course_enrollment_pairs, course_modes):
    """Builds a recent course enrollment message

    Constructs a new message template based on any recent course enrollments for the student.

    Args:
        course_enrollment_pairs (list): A list of tuples containing courses, and the associated enrollment information.
        course_modes (dict): Mapping of course ID's to course mode dictionaries.

    Returns:
        A string representing the HTML message output from the message template.
        None if there are no recently enrolled courses.

    """
    recently_enrolled_courses = _get_recently_enrolled_courses(course_enrollment_pairs)

    if recently_enrolled_courses:
        messages = [
            {
                "course_id": course.id,
                "course_name": course.display_name,
                "allow_donation": _allow_donation(course_modes, course.id, enrollment)
            }
            for course, enrollment in recently_enrolled_courses
        ]

        platform_name = microsite.get_value('platform_name', settings.PLATFORM_NAME)

        return render_to_string(
            'enrollment/course_enrollment_message.html',
            {'course_enrollment_messages': messages, 'platform_name': platform_name}
        )


def _get_recently_enrolled_courses(course_enrollment_pairs):
    """Checks to see if the student has recently enrolled in courses.

    Checks to see if any of the enrollments in the course_enrollment_pairs have been recently created and activated.

    Args:
        course_enrollment_pairs (list): A list of tuples containing courses, and the associated enrollment information.

    Returns:
        A list of courses

    """
    seconds = DashboardConfiguration.current().recent_enrollment_time_delta
    time_delta = (datetime.datetime.now(UTC) - datetime.timedelta(seconds=seconds))
    return [
        (course, enrollment) for course, enrollment in course_enrollment_pairs
        # If the enrollment has no created date, we are explicitly excluding the course
        # from the list of recent enrollments.
        if enrollment.is_active and enrollment.created > time_delta
    ]


def _allow_donation(course_modes, course_id, enrollment):
    """Determines if the dashboard will request donations for the given course.

    Check if donations are configured for the platform, and if the current course is accepting donations.

    Args:
        course_modes (dict): Mapping of course ID's to course mode dictionaries.
        course_id (str): The unique identifier for the course.
        enrollment(CourseEnrollment): The enrollment object in which the user is enrolled

    Returns:
        True if the course is allowing donations.

    """
    donations_enabled = DonationConfiguration.current().enabled
    return donations_enabled and enrollment.mode in course_modes[course_id] and course_modes[course_id][enrollment.mode].min_price == 0


def try_change_enrollment(request):
    """
    This method calls change_enrollment if the necessary POST
    parameters are present, but does not return anything in most cases. It
    simply logs the result or exception. This is usually
    called after a registration or login, as secondary action.
    It should not interrupt a successful registration or login.
    """
    if 'enrollment_action' in request.POST:
        try:
            enrollment_response = change_enrollment(request)
            # There isn't really a way to display the results to the user, so we just log it
            # We expect the enrollment to be a success, and will show up on the dashboard anyway
            log.info(
                u"Attempted to automatically enroll after login. Response code: %s; response body: %s",
                enrollment_response.status_code,
                enrollment_response.content
            )
            # Hack: since change_enrollment delivers its redirect_url in the content
            # of its response, we check here that only the 200 codes with content
            # will return redirect_urls.
            if enrollment_response.status_code == 200 and enrollment_response.content != '':
                return enrollment_response.content
        except Exception as exc:  # pylint: disable=broad-except
            log.exception(u"Exception automatically enrolling after login: %s", exc)


def _update_email_opt_in(request, org):
    """Helper function used to hit the profile API if email opt-in is enabled."""

    email_opt_in = request.POST.get('email_opt_in')
    if email_opt_in is not None:
        email_opt_in_boolean = email_opt_in == 'true'
        preferences_api.update_email_opt_in(request.user, org, email_opt_in_boolean)


@require_POST
@commit_on_success_with_read_committed
def change_enrollment(request, check_access=True):
    """
    Modify the enrollment status for the logged-in user.

    The request parameter must be a POST request (other methods return 405)
    that specifies course_id and enrollment_action parameters. If course_id or
    enrollment_action is not specified, if course_id is not valid, if
    enrollment_action is something other than "enroll" or "unenroll", if
    enrollment_action is "enroll" and enrollment is closed for the course, or
    if enrollment_action is "unenroll" and the user is not enrolled in the
    course, a 400 error will be returned. If the user is not logged in, 403
    will be returned; it is important that only this case return 403 so the
    front end can redirect the user to a registration or login page when this
    happens. This function should only be called from an AJAX request or
    as a post-login/registration helper, so the error messages in the responses
    should never actually be user-visible.

    Args:
        request (`Request`): The Django request object

    Keyword Args:
        check_access (boolean): If True, we check that an accessible course actually
            exists for the given course_key before we enroll the student.
            The default is set to False to avoid breaking legacy code or
            code with non-standard flows (ex. beta tester invitations), but
            for any standard enrollment flow you probably want this to be True.

    Returns:
        Response

    """
    # Get the user
    user = request.user

    # Ensure the user is authenticated
    if not user.is_authenticated():
        return HttpResponseForbidden()

    # Ensure we received a course_id
    action = request.POST.get("enrollment_action")
    if 'course_id' not in request.POST:
        return HttpResponseBadRequest(_("Course id not specified"))

    try:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(request.POST.get("course_id"))
    except InvalidKeyError:
        log.warning(
            u"User %s tried to %s with invalid course id: %s",
            user.username,
            action,
            request.POST.get("course_id"),
        )
        return HttpResponseBadRequest(_("Invalid course id"))

    if action == "enroll":
        # Make sure the course exists
        # We don't do this check on unenroll, or a bad course id can't be unenrolled from
        if not modulestore().has_course(course_id):
            log.warning(
                u"User %s tried to enroll in non-existent course %s",
                user.username,
                course_id
            )
            return HttpResponseBadRequest(_("Course id is invalid"))

        # Record the user's email opt-in preference
        if settings.FEATURES.get('ENABLE_MKTG_EMAIL_OPT_IN'):
            _update_email_opt_in(request, course_id.org)

        available_modes = CourseMode.modes_for_course_dict(course_id)

        # Check whether the user is blocked from enrolling in this course
        # This can occur if the user's IP is on a global blacklist
        # or if the user is enrolling in a country in which the course
        # is not available.
        redirect_url = embargo_api.redirect_if_blocked(
            course_id, user=user, ip_address=get_ip(request),
            url=request.path
        )
        if redirect_url:
            return HttpResponse(redirect_url)

        # Check that auto enrollment is allowed for this course
        # (= the course is NOT behind a paywall)
        if CourseMode.can_auto_enroll(course_id):
            # Enroll the user using the default mode (honor)
            # We're assuming that users of the course enrollment table
            # will NOT try to look up the course enrollment model
            # by its slug.  If they do, it's possible (based on the state of the database)
            # for no such model to exist, even though we've set the enrollment type
            # to "honor".
            try:
                CourseEnrollment.enroll(user, course_id, check_access=check_access)
            except Exception:
                return HttpResponseBadRequest(_("Could not enroll"))

        # If we have more than one course mode or professional ed is enabled,
        # then send the user to the choose your track page.
        # (In the case of no-id-professional/professional ed, this will redirect to a page that
        # funnels users directly into the verification / payment flow)
        if CourseMode.has_verified_mode(available_modes) or CourseMode.has_professional_mode(available_modes):
            return HttpResponse(
                reverse("course_modes_choose", kwargs={'course_id': unicode(course_id)})
            )

        # Otherwise, there is only one mode available (the default)
        return HttpResponse()

    elif action == "add_to_cart":
        # Pass the request handling to shoppingcart.views
        # The view in shoppingcart.views performs error handling and logs different errors.  But this elif clause
        # is only used in the "auto-add after user reg/login" case, i.e. it's always wrapped in try_change_enrollment.
        # This means there's no good way to display error messages to the user.  So we log the errors and send
        # the user to the shopping cart page always, where they can reasonably discern the status of their cart,
        # whether things got added, etc

        shoppingcart.views.add_course_to_cart(request, course_id.to_deprecated_string())
        return HttpResponse(
            reverse("shoppingcart.views.show_cart")
        )

    elif action == "unenroll":
        if not CourseEnrollment.is_enrolled(user, course_id):
            return HttpResponseBadRequest(_("You are not enrolled in this course"))
        CourseEnrollment.unenroll(user, course_id)
        return HttpResponse()
    else:
        return HttpResponseBadRequest(_("Enrollment action is invalid"))


@never_cache
@ensure_csrf_cookie
def accounts_login(request):
    """Deprecated. To be replaced by :class:`student_account.views.login_and_registration_form`."""
    external_auth_response = external_auth_login(request)
    if external_auth_response is not None:
        return external_auth_response

    redirect_to = request.GET.get('next')
    context = {
        'pipeline_running': 'false',
        'pipeline_url': auth_pipeline_urls(pipeline.AUTH_ENTRY_LOGIN, redirect_url=redirect_to),
        'platform_name': settings.PLATFORM_NAME,
    }
    return render_to_response('login.html', context)


# Need different levels of logging
@ensure_csrf_cookie
def login_user(request, error=""):  # pylint: disable-msg=too-many-statements,unused-argument
    """AJAX request to log in the user."""

    backend_name = None
    email = None
    password = None
    redirect_url = None
    response = None
    running_pipeline = None
    third_party_auth_requested = third_party_auth.is_enabled() and pipeline.running(request)
    third_party_auth_successful = False
    trumped_by_first_party_auth = bool(request.POST.get('email')) or bool(request.POST.get('password'))
    user = None

    if third_party_auth_requested and not trumped_by_first_party_auth:
        # The user has already authenticated via third-party auth and has not
        # asked to do first party auth by supplying a username or password. We
        # now want to put them through the same logging and cookie calculation
        # logic as with first-party auth.
        running_pipeline = pipeline.get(request)
        username = running_pipeline['kwargs'].get('username')
        backend_name = running_pipeline['backend']
        requested_provider = provider.Registry.get_by_backend_name(backend_name)

        try:
            user = pipeline.get_authenticated_user(username, backend_name)
            third_party_auth_successful = True
        except User.DoesNotExist:
            AUDIT_LOG.warning(
                u'Login failed - user with username {username} has no social auth with backend_name {backend_name}'.format(
                    username=username, backend_name=backend_name))
            return HttpResponse(
                _("You've successfully logged into your {provider_name} account, but this account isn't linked with an {platform_name} account yet.").format(
                    platform_name=settings.PLATFORM_NAME, provider_name=requested_provider.NAME
                )
                + "<br/><br/>" +
                _("Use your {platform_name} username and password to log into {platform_name} below, "
                  "and then link your {platform_name} account with {provider_name} from your dashboard.").format(
                      platform_name=settings.PLATFORM_NAME, provider_name=requested_provider.NAME
                )
                + "<br/><br/>" +
                _("If you don't have an {platform_name} account yet, click <strong>Register Now</strong> at the top of the page.").format(
                    platform_name=settings.PLATFORM_NAME
                ),
                content_type="text/plain",
                status=403
            )

    else:

        if 'email' not in request.POST or 'password' not in request.POST:
            return JsonResponse({
                "success": False,
                "value": _('There was an error receiving your login information. Please email us.'),  # TODO: User error message
            })  # TODO: this should be status code 400  # pylint: disable=fixme

        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.warning(u"Login failed - Unknown user email")
            else:
                AUDIT_LOG.warning(u"Login failed - Unknown user email: {0}".format(email))

    # check if the user has a linked shibboleth account, if so, redirect the user to shib-login
    # This behavior is pretty much like what gmail does for shibboleth.  Try entering some @stanford.edu
    # address into the Gmail login.
    if settings.FEATURES.get('AUTH_USE_SHIB') and user:
        try:
            eamap = ExternalAuthMap.objects.get(user=user)
            if eamap.external_domain.startswith(external_auth.views.SHIBBOLETH_DOMAIN_PREFIX):
                return JsonResponse({
                    "success": False,
                    "redirect": reverse('shib-login'),
                })  # TODO: this should be status code 301  # pylint: disable=fixme
        except ExternalAuthMap.DoesNotExist:
            # This is actually the common case, logging in user without external linked login
            AUDIT_LOG.info(u"User %s w/o external auth attempting login", user)

    # see if account has been locked out due to excessive login failures
    user_found_by_email_lookup = user
    if user_found_by_email_lookup and LoginFailures.is_feature_enabled():
        if LoginFailures.is_user_locked_out(user_found_by_email_lookup):
            return JsonResponse({
                "success": False,
                "value": _('This account has been temporarily locked due to excessive login failures. Try again later.'),
            })  # TODO: this should be status code 429  # pylint: disable=fixme

    # see if the user must reset his/her password due to any policy settings
    if user_found_by_email_lookup and PasswordHistory.should_user_reset_password_now(user_found_by_email_lookup):
        return JsonResponse({
            "success": False,
            "value": _('Your password has expired due to password policy on this account. You must '
                       'reset your password before you can log in again. Please click the '
                       '"Forgot Password" link on this page to reset your password before logging in again.'),
        })  # TODO: this should be status code 403  # pylint: disable=fixme

    # if the user doesn't exist, we want to set the username to an invalid
    # username so that authentication is guaranteed to fail and we can take
    # advantage of the ratelimited backend
    username = user.username if user else ""

    if not third_party_auth_successful:
        try:
            user = authenticate(username=username, password=password, request=request)
        # this occurs when there are too many attempts from the same IP address
        except RateLimitException:
            return JsonResponse({
                "success": False,
                "value": _('Too many failed login attempts. Try again later.'),
            })  # TODO: this should be status code 429  # pylint: disable=fixme

    if user is None:
        # tick the failed login counters if the user exists in the database
        if user_found_by_email_lookup and LoginFailures.is_feature_enabled():
            LoginFailures.increment_lockout_counter(user_found_by_email_lookup)

        # if we didn't find this username earlier, the account for this email
        # doesn't exist, and doesn't have a corresponding password
        if username != "":
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                loggable_id = user_found_by_email_lookup.id if user_found_by_email_lookup else "<unknown>"
                AUDIT_LOG.warning(u"Login failed - password for user.id: {0} is invalid".format(loggable_id))
            else:
                AUDIT_LOG.warning(u"Login failed - password for {0} is invalid".format(email))
        return JsonResponse({
            "success": False,
            "value": _('Email or password is incorrect.'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme

    # successful login, clear failed login attempts counters, if applicable
    if LoginFailures.is_feature_enabled():
        LoginFailures.clear_lockout_counter(user)

    # Track the user's sign in
    if settings.FEATURES.get('SEGMENT_IO_LMS') and hasattr(settings, 'SEGMENT_IO_LMS_KEY'):
        tracking_context = tracker.get_tracker().resolve_context()
        analytics.identify(user.id, {
            'email': email,
            'username': username,
        })

        analytics.track(
            user.id,
            "edx.bi.user.account.authenticated",
            {
                'category': "conversion",
                'label': request.POST.get('course_id'),
                'provider': None
            },
            context={
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )

    if user is not None and user.is_active:
        try:
            # We do not log here, because we have a handler registered
            # to perform logging on successful logins.
            login(request, user)
            if request.POST.get('remember') == 'true':
                request.session.set_expiry(604800)
                log.debug("Setting user session to never expire")
            else:
                request.session.set_expiry(0)
        except Exception as exc:  # pylint: disable=broad-except
            AUDIT_LOG.critical("Login failed - Could not create session. Is memcached running?")
            log.critical("Login failed - Could not create session. Is memcached running?")
            log.exception(exc)
            raise

        redirect_url = try_change_enrollment(request)

        if third_party_auth_successful:
            redirect_url = pipeline.get_complete_url(backend_name)

        response = JsonResponse({
            "success": True,
            "redirect_url": redirect_url,
        })

        # Ensure that the external marketing site can
        # detect that the user is logged in.
        return set_logged_in_cookie(request, response)

    if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
        AUDIT_LOG.warning(u"Login failed - Account not active for user.id: {0}, resending activation".format(user.id))
    else:
        AUDIT_LOG.warning(u"Login failed - Account not active for user {0}, resending activation".format(username))

    reactivation_email_for_user(user)
    not_activated_msg = _("This account has not been activated. We have sent another activation message. Please check your email for the activation instructions.")
    return JsonResponse({
        "success": False,
        "value": not_activated_msg,
    })  # TODO: this should be status code 400  # pylint: disable=fixme


@csrf_exempt
@require_POST
@social_utils.strategy("social:complete")
def login_oauth_token(request, backend):
    """
    Authenticate the client using an OAuth access token by using the token to
    retrieve information from a third party and matching that information to an
    existing user.
    """
    warnings.warn("Please use AccessTokenExchangeView instead.", DeprecationWarning)

    backend = request.social_strategy.backend
    if isinstance(backend, social_oauth.BaseOAuth1) or isinstance(backend, social_oauth.BaseOAuth2):
        if "access_token" in request.POST:
            # Tell third party auth pipeline that this is an API call
            request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_LOGIN_API
            user = None
            try:
                user = backend.do_auth(request.POST["access_token"])
            except HTTPError:
                pass
            # do_auth can return a non-User object if it fails
            if user and isinstance(user, User):
                login(request, user)
                return JsonResponse(status=204)
            else:
                # Ensure user does not re-enter the pipeline
                request.social_strategy.clean_partial_pipeline()
                return JsonResponse({"error": "invalid_token"}, status=401)
        else:
            return JsonResponse({"error": "invalid_request"}, status=400)
    raise Http404


@ensure_csrf_cookie
def logout_user(request):
    """
    HTTP request to log out the user. Redirects to marketing page.
    Deletes both the CSRF and sessionid cookies so the marketing
    site can determine the logged in state of the user
    """
    # We do not log here, because we have a handler registered
    # to perform logging on successful logouts.
    logout(request)
    if settings.FEATURES.get('AUTH_USE_CAS'):
        target = reverse('cas-logout')
    else:
        target = '/'
    response = redirect(target)
    response.delete_cookie(
        settings.EDXMKTG_COOKIE_NAME,
        path='/', domain=settings.SESSION_COOKIE_DOMAIN,
    )
    return response


@require_GET
@login_required
@ensure_csrf_cookie
def manage_user_standing(request):
    """
    Renders the view used to manage user standing. Also displays a table
    of user accounts that have been disabled and who disabled them.
    """
    if not request.user.is_staff:
        raise Http404
    all_disabled_accounts = UserStanding.objects.filter(
        account_status=UserStanding.ACCOUNT_DISABLED
    )

    all_disabled_users = [standing.user for standing in all_disabled_accounts]

    headers = ['username', 'account_changed_by']
    rows = []
    for user in all_disabled_users:
        row = [user.username, user.standing.all()[0].changed_by]
        rows.append(row)

    context = {'headers': headers, 'rows': rows}

    return render_to_response("manage_user_standing.html", context)


@require_POST
@login_required
@ensure_csrf_cookie
def disable_account_ajax(request):
    """
    Ajax call to change user standing. Endpoint of the form
    in manage_user_standing.html
    """
    if not request.user.is_staff:
        raise Http404
    username = request.POST.get('username')
    context = {}
    if username is None or username.strip() == '':
        context['message'] = _('Please enter a username')
        return JsonResponse(context, status=400)

    account_action = request.POST.get('account_action')
    if account_action is None:
        context['message'] = _('Please choose an option')
        return JsonResponse(context, status=400)

    username = username.strip()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        context['message'] = _("User with username {} does not exist").format(username)
        return JsonResponse(context, status=400)
    else:
        user_account, _success = UserStanding.objects.get_or_create(
            user=user, defaults={'changed_by': request.user},
        )
        if account_action == 'disable':
            user_account.account_status = UserStanding.ACCOUNT_DISABLED
            context['message'] = _("Successfully disabled {}'s account").format(username)
            log.info(u"%s disabled %s's account", request.user, username)
        elif account_action == 'reenable':
            user_account.account_status = UserStanding.ACCOUNT_ENABLED
            context['message'] = _("Successfully reenabled {}'s account").format(username)
            log.info(u"%s reenabled %s's account", request.user, username)
        else:
            context['message'] = _("Unexpected account status")
            return JsonResponse(context, status=400)
        user_account.changed_by = request.user
        user_account.standing_last_changed_at = datetime.datetime.now(UTC)
        user_account.save()

    return JsonResponse(context)


@login_required
@ensure_csrf_cookie
def change_setting(request):
    """JSON call to change a profile setting: Right now, location"""
    # TODO (vshnayder): location is no longer used
    u_prof = UserProfile.objects.get(user=request.user)  # request.user.profile_cache
    if 'location' in request.POST:
        u_prof.location = request.POST['location']
    u_prof.save()

    return JsonResponse({
        "success": True,
        "location": u_prof.location,
    })


class AccountValidationError(Exception):
    def __init__(self, message, field):
        super(AccountValidationError, self).__init__(message)
        self.field = field


@receiver(post_save, sender=User)
def user_signup_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    handler that saves the user Signup Source
    when the user is created
    """
    if 'created' in kwargs and kwargs['created']:
        site = microsite.get_value('SITE_NAME')
        if site:
            user_signup_source = UserSignupSource(user=kwargs['instance'], site=site)
            user_signup_source.save()
            log.info(u'user {} originated from a white labeled "Microsite"'.format(kwargs['instance'].id))


def _do_create_account(form):
    """
    Given cleaned post variables, create the User and UserProfile objects, as well as the
    registration for this user.

    Returns a tuple (User, UserProfile, Registration).

    Note: this function is also used for creating test users.
    """
    if not form.is_valid():
        raise ValidationError(form.errors)

    user = User(
        username=form.cleaned_data["username"],
        email=form.cleaned_data["email"],
        is_active=False
    )
    user.set_password(form.cleaned_data["password"])
    registration = Registration()

    # TODO: Rearrange so that if part of the process fails, the whole process fails.
    # Right now, we can have e.g. no registration e-mail sent out and a zombie account
    try:
        user.save()
    except IntegrityError:
        # Figure out the cause of the integrity error
        if len(User.objects.filter(username=user.username)) > 0:
            raise AccountValidationError(
                _("An account with the Public Username '{username}' already exists.").format(username=user.username),
                field="username"
            )
        elif len(User.objects.filter(email=user.email)) > 0:
            raise AccountValidationError(
                _("An account with the Email '{email}' already exists.").format(email=user.email),
                field="email"
            )
        else:
            raise

    # add this account creation to password history
    # NOTE, this will be a NOP unless the feature has been turned on in configuration
    password_history_entry = PasswordHistory()
    password_history_entry.create(user)

    registration.register(user)

    profile_fields = [
        "name", "level_of_education", "gender", "mailing_address", "city", "country", "goals",
        "year_of_birth"
    ]
    profile = UserProfile(
        user=user,
        **{key: form.cleaned_data.get(key) for key in profile_fields}
    )
    extended_profile = form.cleaned_extended_profile
    if extended_profile:
        profile.meta = json.dumps(extended_profile)
    try:
        profile.save()
    except Exception:  # pylint: disable=broad-except
        log.exception("UserProfile creation failed for user {id}.".format(id=user.id))
        raise

    return (user, profile, registration)


def create_account_with_params(request, params):
    """
    Given a request and a dict of parameters (which may or may not have come
    from the request), create an account for the requesting user, including
    creating a comments service user object and sending an activation email.
    This also takes external/third-party auth into account, updates that as
    necessary, and authenticates the user for the request's session.

    Does not return anything.

    Raises AccountValidationError if an account with the username or email
    specified by params already exists, or ValidationError if any of the given
    parameters is invalid for any other reason.

    Issues with this code:
    * It is not transactional. If there is a failure part-way, an incomplete
      account will be created and left in the database.
    * Third-party auth passwords are not verified. There is a comment that
      they are unused, but it would be helpful to have a sanity check that
      they are sane.
    * It is over 300 lines long (!) and includes disprate functionality, from
      registration e-mails to all sorts of other things. It should be broken
      up into semantically meaningful functions.
    * The user-facing text is rather unfriendly (e.g. "Username must be a
      minimum of two characters long" rather than "Please use a username of
      at least two characters").
    """
    # Copy params so we can modify it; we can't just do dict(params) because if
    # params is request.POST, that results in a dict containing lists of values
    params = dict(params.items())

    # allow for microsites to define their own set of required/optional/hidden fields
    extra_fields = microsite.get_value(
        'REGISTRATION_EXTRA_FIELDS',
        getattr(settings, 'REGISTRATION_EXTRA_FIELDS', {})
    )

    # Boolean of whether a 3rd party auth provider and credentials were provided in
    # the API so the newly created account can link with the 3rd party account.
    #
    # Note: this is orthogonal to the 3rd party authentication pipeline that occurs
    # when the account is created via the browser and redirect URLs.
    should_link_with_social_auth = third_party_auth.is_enabled() and 'provider' in params

    if should_link_with_social_auth or (third_party_auth.is_enabled() and pipeline.running(request)):
        params["password"] = pipeline.make_random_password()

    # if doing signup for an external authorization, then get email, password, name from the eamap
    # don't use the ones from the form, since the user could have hacked those
    # unless originally we didn't get a valid email or name from the external auth
    # TODO: We do not check whether these values meet all necessary criteria, such as email length
    do_external_auth = 'ExternalAuthMap' in request.session
    if do_external_auth:
        eamap = request.session['ExternalAuthMap']
        try:
            validate_email(eamap.external_email)
            params["email"] = eamap.external_email
        except ValidationError:
            pass
        if eamap.external_name.strip() != '':
            params["name"] = eamap.external_name
        params["password"] = eamap.internal_password
        log.debug(u'In create_account with external_auth: user = %s, email=%s', params["name"], params["email"])

    extended_profile_fields = microsite.get_value('extended_profile_fields', [])
    enforce_password_policy = (
        settings.FEATURES.get("ENFORCE_PASSWORD_POLICY", False) and
        not do_external_auth
    )
    # Can't have terms of service for certain SHIB users, like at Stanford
    tos_required = (
        not settings.FEATURES.get("AUTH_USE_SHIB") or
        not settings.FEATURES.get("SHIB_DISABLE_TOS") or
        not do_external_auth or
        not eamap.external_domain.startswith(
            external_auth.views.SHIBBOLETH_DOMAIN_PREFIX
        )
    )

    form = AccountCreationForm(
        data=params,
        extra_fields=extra_fields,
        extended_profile_fields=extended_profile_fields,
        enforce_username_neq_password=True,
        enforce_password_policy=enforce_password_policy,
        tos_required=tos_required,
    )

    # Perform operations within a transaction that are critical to account creation
    with transaction.commit_on_success():
        # first, create the account
        (user, profile, registration) = _do_create_account(form)

        # next, link the account with social auth, if provided
        if should_link_with_social_auth:
            request.social_strategy = social_utils.load_strategy(backend=params['provider'], request=request)
            social_access_token = params.get('access_token')
            if not social_access_token:
                raise ValidationError({
                    'access_token': [
                        _("An access_token is required when passing value ({}) for provider.").format(
                            params['provider']
                        )
                    ]
                })
            request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_REGISTER_API
            pipeline_user = None
            error_message = ""
            try:
                pipeline_user = request.social_strategy.backend.do_auth(social_access_token, user=user)
            except AuthAlreadyAssociated:
                error_message = _("The provided access_token is already associated with another user.")
            except (HTTPError, AuthException):
                error_message = _("The provided access_token is not valid.")
            if not pipeline_user or not isinstance(pipeline_user, User):
                # Ensure user does not re-enter the pipeline
                request.social_strategy.clean_partial_pipeline()
                raise ValidationError({'access_token': [error_message]})

    # Perform operations that are non-critical parts of account creation
    preferences_api.set_user_preference(user, LANGUAGE_KEY, get_language())

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:
            log.exception("Enable discussion notifications failed for user {id}.".format(id=user.id))

    dog_stats_api.increment("common.student.account_created")

    # Track the user's registration
    if settings.FEATURES.get('SEGMENT_IO_LMS') and hasattr(settings, 'SEGMENT_IO_LMS_KEY'):
        tracking_context = tracker.get_tracker().resolve_context()
        analytics.identify(user.id, {
            'email': user.email,
            'username': user.username,
        })

        # If the user is registering via 3rd party auth, track which provider they use
        provider_name = None
        if third_party_auth.is_enabled() and pipeline.running(request):
            running_pipeline = pipeline.get(request)
            current_provider = provider.Registry.get_by_backend_name(running_pipeline.get('backend'))
            provider_name = current_provider.NAME

        analytics.track(
            user.id,
            "edx.bi.user.account.registered",
            {
                'category': 'conversion',
                'label': params.get('course_id'),
                'provider': provider_name
            },
            context={
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )

    create_comments_service_user(user)

    context = {
        'name': profile.name,
        'key': registration.activation_key,
    }

    # composes activation email
    subject = render_to_string('emails/activation_email_subject.txt', context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', context)

    # Don't send email if we are:
    #
    # 1. Doing load testing.
    # 2. Random user generation for other forms of testing.
    # 3. External auth bypassing activation.
    # 4. Have the platform configured to not require e-mail activation.
    #
    # Note that this feature is only tested as a flag set one way or
    # the other for *new* systems. we need to be careful about
    # changing settings on a running system to make sure no users are
    # left in an inconsistent state (or doing a migration if they are).
    send_email = (
        not settings.FEATURES.get('SKIP_EMAIL_VALIDATION', None) and
        not settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING') and
        not (do_external_auth and settings.FEATURES.get('BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'))
    )
    if send_email:
        from_address = microsite.get_value(
            'email_from_address',
            settings.DEFAULT_FROM_EMAIL
        )
        try:
            if settings.FEATURES.get('REROUTE_ACTIVATION_EMAIL'):
                dest_addr = settings.FEATURES['REROUTE_ACTIVATION_EMAIL']
                message = ("Activation for %s (%s): %s\n" % (user, user.email, profile.name) +
                           '-' * 80 + '\n\n' + message)
                mail.send_mail(subject, message, from_address, [dest_addr], fail_silently=False)
            else:
                user.email_user(subject, message, from_address)
        except Exception:  # pylint: disable=broad-except
            log.error(u'Unable to send activation email to user from "%s"', from_address, exc_info=True)
    else:
        registration.activate()

    # Immediately after a user creates an account, we log them in. They are only
    # logged in until they close the browser. They can't log in again until they click
    # the activation link from the email.
    new_user = authenticate(username=user.username, password=params['password'])
    login(request, new_user)
    request.session.set_expiry(0)

    # TODO: there is no error checking here to see that the user actually logged in successfully,
    # and is not yet an active user.
    if new_user is not None:
        AUDIT_LOG.info(u"Login success on new account creation - {0}".format(new_user.username))

    if do_external_auth:
        eamap.user = new_user
        eamap.dtsignup = datetime.datetime.now(UTC)
        eamap.save()
        AUDIT_LOG.info(u"User registered with external_auth %s", new_user.username)
        AUDIT_LOG.info(u'Updated ExternalAuthMap for %s to be %s', new_user.username, eamap)

        if settings.FEATURES.get('BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'):
            log.info('bypassing activation email')
            new_user.is_active = True
            new_user.save()
            AUDIT_LOG.info(u"Login activated on extauth account - {0} ({1})".format(new_user.username, new_user.email))


def set_marketing_cookie(request, response):
    """
    Set the login cookie for the edx marketing site on the given response. Its
    expiration will match that of the given request's session.
    """
    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
        expires_time = time.time() + max_age
        expires = cookie_date(expires_time)

    # we want this cookie to be accessed via javascript
    # so httponly is set to None
    response.set_cookie(
        settings.EDXMKTG_COOKIE_NAME,
        'true',
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path='/',
        secure=None,
        httponly=None
    )


@csrf_exempt
def create_account(request, post_override=None):
    """
    JSON call to create new edX account.
    Used by form in signup_modal.html, which is included into navigation.html
    """
    warnings.warn("Please use RegistrationView instead.", DeprecationWarning)

    try:
        create_account_with_params(request, post_override or request.POST)
    except AccountValidationError as exc:
        return JsonResponse({'success': False, 'value': exc.message, 'field': exc.field}, status=400)
    except ValidationError as exc:
        field, error_list = next(exc.message_dict.iteritems())
        return JsonResponse(
            {
                "success": False,
                "field": field,
                "value": error_list[0],
            },
            status=400
        )

    redirect_url = try_change_enrollment(request)

    # Resume the third-party-auth pipeline if necessary.
    if third_party_auth.is_enabled() and pipeline.running(request):
        running_pipeline = pipeline.get(request)
        redirect_url = pipeline.get_complete_url(running_pipeline['backend'])

    response = JsonResponse({
        'success': True,
        'redirect_url': redirect_url,
    })
    set_marketing_cookie(request, response)
    return response


def auto_auth(request):
    """
    Create or configure a user account, then log in as that user.

    Enabled only when
    settings.FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] is true.

    Accepts the following querystring parameters:
    * `username`, `email`, and `password` for the user account
    * `full_name` for the user profile (the user's full name; defaults to the username)
    * `staff`: Set to "true" to make the user global staff.
    * `course_id`: Enroll the student in the course with `course_id`
    * `roles`: Comma-separated list of roles to grant the student in the course with `course_id`
    * `no_login`: Define this to create the user but not login

    If username, email, or password are not provided, use
    randomly generated credentials.
    """

    # Generate a unique name to use if none provided
    unique_name = uuid.uuid4().hex[0:30]

    # Use the params from the request, otherwise use these defaults
    username = request.GET.get('username', unique_name)
    password = request.GET.get('password', unique_name)
    email = request.GET.get('email', unique_name + "@example.com")
    full_name = request.GET.get('full_name', username)
    is_staff = request.GET.get('staff', None)
    course_id = request.GET.get('course_id', None)
    course_key = None
    if course_id:
        course_key = CourseLocator.from_string(course_id)
    role_names = [v.strip() for v in request.GET.get('roles', '').split(',') if v.strip()]
    login_when_done = 'no_login' not in request.GET

    form = AccountCreationForm(
        data={
            'username': username,
            'email': email,
            'password': password,
            'name': full_name,
        },
        tos_required=False
    )

    # Attempt to create the account.
    # If successful, this will return a tuple containing
    # the new user object.
    try:
        user, _profile, reg = _do_create_account(form)
    except AccountValidationError:
        # Attempt to retrieve the existing user.
        user = User.objects.get(username=username)
        user.email = email
        user.set_password(password)
        user.save()
        reg = Registration.objects.get(user=user)

    # Set the user's global staff bit
    if is_staff is not None:
        user.is_staff = (is_staff == "true")
        user.save()

    # Activate the user
    reg.activate()
    reg.save()

    # Enroll the user in a course
    if course_key is not None:
        CourseEnrollment.enroll(user, course_key)

    # Apply the roles
    for role_name in role_names:
        role = Role.objects.get(name=role_name, course_id=course_key)
        user.roles.add(role)

    # Log in as the user
    if login_when_done:
        user = authenticate(username=username, password=password)
        login(request, user)

    create_comments_service_user(user)

    # Provide the user with a valid CSRF token
    # then return a 200 response
    success_msg = u"{} user {} ({}) with password {} and user_id {}".format(
        u"Logged in" if login_when_done else "Created",
        username, email, password, user.id
    )
    response = HttpResponse(success_msg)
    response.set_cookie('csrftoken', csrf(request)['csrf_token'])
    return response


@ensure_csrf_cookie
def activate_account(request, key):
    """When link in activation e-mail is clicked"""
    regs = Registration.objects.filter(activation_key=key)
    if len(regs) == 1:
        user_logged_in = request.user.is_authenticated()
        already_active = True
        if not regs[0].user.is_active:
            regs[0].activate()
            already_active = False

        # Enroll student in any pending courses he/she may have if auto_enroll flag is set
        student = User.objects.filter(id=regs[0].user_id)
        if student:
            ceas = CourseEnrollmentAllowed.objects.filter(email=student[0].email)
            for cea in ceas:
                if cea.auto_enroll:
                    CourseEnrollment.enroll(student[0], cea.course_id)

            # enroll student in any pending CCXs he/she may have if auto_enroll flag is set
            if settings.FEATURES.get('CUSTOM_COURSES_EDX'):
                from ccx.models import CcxMembership, CcxFutureMembership
                ccxfms = CcxFutureMembership.objects.filter(
                    email=student[0].email
                )
                for ccxfm in ccxfms:
                    if ccxfm.auto_enroll:
                        CcxMembership.auto_enroll(student[0], ccxfm)

        resp = render_to_response(
            "registration/activation_complete.html",
            {
                'user_logged_in': user_logged_in,
                'already_active': already_active
            }
        )
        return resp
    if len(regs) == 0:
        return render_to_response(
            "registration/activation_invalid.html",
            {'csrf': csrf(request)['csrf_token']}
        )
    return HttpResponseServerError(_("Unknown error. Please e-mail us to let us know how it happened."))


@csrf_exempt
@require_POST
def password_reset(request):
    """ Attempts to send a password reset e-mail. """
    # Add some rate limiting here by re-using the RateLimitMixin as a helper class
    limiter = BadRequestRateLimiter()
    if limiter.is_rate_limit_exceeded(request):
        AUDIT_LOG.warning("Rate limit exceeded in password_reset")
        return HttpResponseForbidden()

    form = PasswordResetFormNoActive(request.POST)
    if form.is_valid():
        form.save(use_https=request.is_secure(),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  request=request,
                  domain_override=request.get_host())
    else:
        # bad user? tick the rate limiter counter
        AUDIT_LOG.info("Bad password_reset user passed in.")
        limiter.tick_bad_request_counter(request)

    return JsonResponse({
        'success': True,
        'value': render_to_string('registration/password_reset_done.html', {}),
    })


def password_reset_confirm_wrapper(
    request,
    uidb36=None,
    token=None,
):
    """ A wrapper around django.contrib.auth.views.password_reset_confirm.
        Needed because we want to set the user as active at this step.
    """
    # cribbed from django.contrib.auth.views.password_reset_confirm
    try:
        uid_int = base36_to_int(uidb36)
        user = User.objects.get(id=uid_int)
        user.is_active = True
        user.save()
    except (ValueError, User.DoesNotExist):
        pass

    # tie in password strength enforcement as an optional level of
    # security protection
    err_msg = None

    if request.method == 'POST':
        password = request.POST['new_password1']
        if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
            try:
                validate_password_length(password)
                validate_password_complexity(password)
                validate_password_dictionary(password)
            except ValidationError, err:
                err_msg = _('Password: ') + '; '.join(err.messages)

        # also, check the password reuse policy
        if not PasswordHistory.is_allowable_password_reuse(user, password):
            if user.is_staff:
                num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STAFF_PASSWORDS_BEFORE_REUSE']
            else:
                num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE']
            err_msg = ungettext(
                "You are re-using a password that you have used recently. You must have {num} distinct password before reusing a previous password.",
                "You are re-using a password that you have used recently. You must have {num} distinct passwords before reusing a previous password.",
                num_distinct
            ).format(num=num_distinct)

        # also, check to see if passwords are getting reset too frequent
        if PasswordHistory.is_password_reset_too_soon(user):
            num_days = settings.ADVANCED_SECURITY_CONFIG['MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS']
            err_msg = ungettext(
                "You are resetting passwords too frequently. Due to security policies, {num} day must elapse between password resets.",
                "You are resetting passwords too frequently. Due to security policies, {num} days must elapse between password resets.",
                num_days
            ).format(num=num_days)

    if err_msg:
        # We have an password reset attempt which violates some security policy, use the
        # existing Django template to communicate this back to the user
        context = {
            'validlink': True,
            'form': None,
            'title': _('Password reset unsuccessful'),
            'err_msg': err_msg,
            'platform_name': settings.PLATFORM_NAME,
        }
        return TemplateResponse(request, 'registration/password_reset_confirm.html', context)
    else:
        # we also want to pass settings.PLATFORM_NAME in as extra_context
        extra_context = {"platform_name": settings.PLATFORM_NAME}

        if request.method == 'POST':
            # remember what the old password hash is before we call down
            old_password_hash = user.password

            result = password_reset_confirm(
                request, uidb36=uidb36, token=token, extra_context=extra_context
            )

            # get the updated user
            updated_user = User.objects.get(id=uid_int)

            # did the password hash change, if so record it in the PasswordHistory
            if updated_user.password != old_password_hash:
                entry = PasswordHistory()
                entry.create(updated_user)

            return result
        else:
            return password_reset_confirm(
                request, uidb36=uidb36, token=token, extra_context=extra_context
            )


def reactivation_email_for_user(user):
    try:
        reg = Registration.objects.get(user=user)
    except Registration.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('No inactive user with this e-mail exists'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme

    context = {
        'name': user.profile.name,
        'key': reg.activation_key,
    }

    subject = render_to_string('emails/activation_email_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', context)

    try:
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except Exception:  # pylint: disable=broad-except
        log.error(u'Unable to send reactivation email from "%s"', settings.DEFAULT_FROM_EMAIL, exc_info=True)
        return JsonResponse({
            "success": False,
            "error": _('Unable to send reactivation email')
        })  # TODO: this should be status code 500  # pylint: disable=fixme

    return JsonResponse({"success": True})


# TODO: delete this method and redirect unit tests to validate_new_email and do_email_change_request
# after accounts page work is done.
@ensure_csrf_cookie
def change_email_request(request):
    """ AJAX call from the profile page. User wants a new e-mail.
    """
    ## Make sure it checks for existing e-mail conflicts
    if not request.user.is_authenticated():
        raise Http404

    user = request.user

    if not user.check_password(request.POST['password']):
        return JsonResponse({
            "success": False,
            "error": _('Invalid password'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme

    new_email = request.POST['new_email']
    try:
        validate_new_email(request.user, new_email)
        do_email_change_request(request.user, new_email)
    except ValueError as err:
        return JsonResponse({
            "success": False,
            "error": err.message,
        })
    return JsonResponse({"success": True})


def validate_new_email(user, new_email):
    """
    Given a new email for a user, does some basic verification of the new address If any issues are encountered
    with verification a ValueError will be thrown.
    """
    try:
        validate_email(new_email)
    except ValidationError:
        raise ValueError(_('Valid e-mail address required.'))

    if new_email == user.email:
        raise ValueError(_('Old email is the same as the new email.'))

    if User.objects.filter(email=new_email).count() != 0:
        raise ValueError(_('An account with this e-mail already exists.'))


def do_email_change_request(user, new_email, activation_key=uuid.uuid4().hex):
    """
    Given a new email for a user, does some basic verification of the new address and sends an activation message
    to the new address. If any issues are encountered with verification or sending the message, a ValueError will
    be thrown.
    """
    pec_list = PendingEmailChange.objects.filter(user=user)
    if len(pec_list) == 0:
        pec = PendingEmailChange()
        pec.user = user
    else:
        pec = pec_list[0]

    pec.new_email = new_email
    pec.activation_key = activation_key
    pec.save()

    context = {
        'key': pec.activation_key,
        'old_email': user.email,
        'new_email': pec.new_email
    }

    subject = render_to_string('emails/email_change_subject.txt', context)
    subject = ''.join(subject.splitlines())

    message = render_to_string('emails/email_change.txt', context)

    from_address = microsite.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )
    try:
        mail.send_mail(subject, message, from_address, [pec.new_email])
    except Exception:  # pylint: disable=broad-except
        log.error(u'Unable to send email activation link to user from "%s"', from_address, exc_info=True)
        raise ValueError(_('Unable to send email activation link. Please try again later.'))


@ensure_csrf_cookie
@transaction.commit_manually
def confirm_email_change(request, key):  # pylint: disable=unused-argument
    """
    User requested a new e-mail. This is called when the activation
    link is clicked. We confirm with the old e-mail, and update
    """
    try:
        try:
            pec = PendingEmailChange.objects.get(activation_key=key)
        except PendingEmailChange.DoesNotExist:
            response = render_to_response("invalid_email_key.html", {})
            transaction.rollback()
            return response

        user = pec.user
        address_context = {
            'old_email': user.email,
            'new_email': pec.new_email
        }

        if len(User.objects.filter(email=pec.new_email)) != 0:
            response = render_to_response("email_exists.html", {})
            transaction.rollback()
            return response

        subject = render_to_string('emails/email_change_subject.txt', address_context)
        subject = ''.join(subject.splitlines())
        message = render_to_string('emails/confirm_email_change.txt', address_context)
        u_prof = UserProfile.objects.get(user=user)
        meta = u_prof.get_meta()
        if 'old_emails' not in meta:
            meta['old_emails'] = []
        meta['old_emails'].append([user.email, datetime.datetime.now(UTC).isoformat()])
        u_prof.set_meta(meta)
        u_prof.save()
        # Send it to the old email...
        try:
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        except Exception:    # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to old address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': user.email})
            transaction.rollback()
            return response

        user.email = pec.new_email
        user.save()
        pec.delete()
        # And send it to the new email...
        try:
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to new address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': pec.new_email})
            transaction.rollback()
            return response

        response = render_to_response("email_change_successful.html", address_context)
        transaction.commit()
        return response
    except Exception:  # pylint: disable=broad-except
        # If we get an unexpected exception, be sure to rollback the transaction
        transaction.rollback()
        raise


# TODO: DELETE AFTER NEW ACCOUNT PAGE DONE
@ensure_csrf_cookie
@require_POST
def change_name_request(request):
    """ Log a request for a new name. """
    if not request.user.is_authenticated():
        raise Http404

    try:
        pnc = PendingNameChange.objects.get(user=request.user.id)
    except PendingNameChange.DoesNotExist:
        pnc = PendingNameChange()
    pnc.user = request.user
    pnc.new_name = request.POST['new_name'].strip()
    pnc.rationale = request.POST['rationale']
    if len(pnc.new_name) < 2:
        return JsonResponse({
            "success": False,
            "error": _('Name required'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme
    pnc.save()

    # The following automatically accepts name change requests. Remove this to
    # go back to the old system where it gets queued up for admin approval.
    accept_name_change_by_id(pnc.id)

    return JsonResponse({"success": True})


# TODO: DELETE AFTER NEW ACCOUNT PAGE DONE
def accept_name_change_by_id(uid):
    """
    Accepts the pending name change request for the user represented
    by user id `uid`.
    """
    try:
        pnc = PendingNameChange.objects.get(id=uid)
    except PendingNameChange.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('Invalid ID'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme

    user = pnc.user
    u_prof = UserProfile.objects.get(user=user)

    # Save old name
    meta = u_prof.get_meta()
    if 'old_names' not in meta:
        meta['old_names'] = []
    meta['old_names'].append([u_prof.name, pnc.rationale, datetime.datetime.now(UTC).isoformat()])
    u_prof.set_meta(meta)

    u_prof.name = pnc.new_name
    u_prof.save()
    pnc.delete()

    return JsonResponse({"success": True})


@require_POST
@login_required
@ensure_csrf_cookie
def change_email_settings(request):
    """Modify logged-in user's setting for receiving emails from a course."""
    user = request.user

    course_id = request.POST.get("course_id")
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    receive_emails = request.POST.get("receive_emails")
    if receive_emails:
        optout_object = Optout.objects.filter(user=user, course_id=course_key)
        if optout_object:
            optout_object.delete()
        log.info(
            u"User %s (%s) opted in to receive emails from course %s",
            user.username,
            user.email,
            course_id
        )
        track.views.server_track(request, "change-email-settings", {"receive_emails": "yes", "course": course_id}, page='dashboard')
    else:
        Optout.objects.get_or_create(user=user, course_id=course_key)
        log.info(
            u"User %s (%s) opted out of receiving emails from course %s",
            user.username,
            user.email,
            course_id
        )
        track.views.server_track(request, "change-email-settings", {"receive_emails": "no", "course": course_id}, page='dashboard')

    return JsonResponse({"success": True})
