"""
Helper methods for `philu_overrides` app
"""
import json
from datetime import datetime

import pytz
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from common.lib.mandrill_client.client import MandrillClient
from common.djangoapps.mailchimp_pipeline.signals.handlers import task_send_account_activation_email
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.onboarding.constants import ORG_PARTNERSHIP_END_DATE_PLACEHOLDER
from lms.djangoapps.onboarding.models import GranteeOptIn
from lms.djangoapps.philu_overrides.constants import ACTIVATION_ALERT_TYPE, ACTIVATION_ERROR_MSG_FORMAT
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.request_utils import safe_get_host
from student.models import Registration
from util.json_request import JsonResponse

utc = pytz.UTC


def get_course_details(course_id):
    course_descriptor = get_course_by_id(course_id)
    course = CourseDetails.populate(course_descriptor)
    return course


def send_account_activation_email(request, registration, user):
    """
    Send account activation email to user

    Arguments:
        request (HttpRequest): HttpRequest object
        registration (Registration): Registration object
        user (User): User object

    Returns:
        None
    """
    activation_link = '{protocol}://{site}/activate/{key}'.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        key=registration.activation_key
    )

    data = {
        'first_name': user.first_name,
        'activation_link': activation_link,
        'user_email': user.email
    }
    task_send_account_activation_email.delay(data)


def reactivation_email_for_user_custom(request, user):
    try:
        reg = Registration.objects.get(user=user)
        send_account_activation_email(request, reg, user)
    except Registration.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('No inactive user with this e-mail exists'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme


def has_access_custom(course):
    """ User can enroll if current time is between enrollment start and end date """
    current_time = datetime.utcnow().replace(tzinfo=utc)

    return (course.enrollment_start and course.enrollment_end and
            course.enrollment_start < current_time < course.enrollment_end)


def get_course_next_classes(request, course):
    """
    Method to get all upcoming reruns of a course
    """

    # imports to avoid circular dependencies
    from lms.djangoapps.courseware.access import _can_enroll_courselike
    from lms.djangoapps.courseware.views.views import registered_for_course
    from student.models import CourseEnrollment
    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    courses = get_all_reruns_of_a_course(course)

    course_next_classes = []

    for _course in courses:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(_course.id.__str__())
        course = get_course_by_id(course_key)
        course.course_open_date = _course.course_open_date
        registered = registered_for_course(course, request.user)

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = _can_enroll_courselike(request.user, course)
        invitation_only = course.invitation_only
        is_course_full = CourseEnrollment.objects.is_course_full(course)

        # Register button should be disabled if one of the following is true:
        # - Student is already registered for course
        # - Course is already full
        # - Student cannot enroll in course
        active_reg_button = not (registered or is_course_full or not can_enroll)
        course_first_chapter_link = ""
        if request.user.is_authenticated() and request.user.is_staff:
            # imported get_course_first_chapter_link here because importing above was throwing circular exception
            from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
            course_first_chapter_link = get_course_first_chapter_link(_course)

        course_next_classes.append({
            'user': request.user,
            'registered': registered,
            'is_course_full': is_course_full,
            'can_enroll': can_enroll.has_access,
            'invitation_only': invitation_only,
            'course': course,
            'active_reg_button': active_reg_button,
            'course_first_chapter_link': course_first_chapter_link
        })
    return course_next_classes


def get_all_reruns_of_a_course(course):
    """
    :param course:
    :return reruns:
    """
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from course_action_state.models import CourseRerunState
    from openedx.features.course_card.helpers import get_course_open_date
    courses = []
    current_time = datetime.utcnow().replace(tzinfo=utc)
    course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
    course_rerun_objects = CourseOverview.objects.select_related('image_set').filter(
        id__in=course_rerun_states).order_by('start')
    for course_run in course_rerun_objects:

        course_open_date = get_course_open_date(course_run)
        if course_run.start > current_time:
            course_run.course_open_date = course_open_date
            courses.append(course_run)

    return courses


def get_user_current_enrolled_class(request, course):
    """
    Method to get an ongoing user enrolled course. A course that meets the following criteria
    => start date <= today
    => end date > today
    => user is enrolled
    """
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from lms.djangoapps.philu_overrides.courseware.views.views import get_course_related_keys
    from student.models import CourseEnrollment
    from course_action_state.models import CourseRerunState

    all_course_reruns = [crs.course_key for crs in CourseRerunState.objects.filter(
        source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
    current_time = datetime.utcnow().replace(tzinfo=utc)
    current_class = get_course_current_class(all_course_reruns, current_time)

    current_enrolled_class = False
    if current_class:
        current_enrolled_class = CourseEnrollment.is_enrolled(request.user, current_class.id)

    current_enrolled_class_target = ''
    if current_enrolled_class:
        course_open_date = current_class.course_open_date
        course_key = SlashSeparatedCourseKey.from_deprecated_string(current_class.id.__str__())
        current_class = get_course_by_id(course_key)
        current_class.course_open_date = course_open_date
        first_chapter_url, first_section = get_course_related_keys(request, current_class)
        current_enrolled_class_target = reverse('courseware_section',
                                                args=[current_class.id.to_deprecated_string(),
                                                      first_chapter_url, first_section])

    return current_class, current_enrolled_class, current_enrolled_class_target


def get_course_current_class(all_course_reruns, current_time):
    """
    Method to get ongoing course

    Arguments:
        all_course_reruns (list): List of course reruns key
        current_time (datetime): Current time

    Returns:
        CourseOverview object or None
    """
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from openedx.features.course_card.helpers import get_course_open_date
    course = CourseOverview.objects.select_related('image_set').filter(
        id__in=all_course_reruns, start__lte=current_time, end__gte=current_time).order_by('-start').first()

    if course:
        course_open_date = get_course_open_date(course)

        if course.start <= current_time:
            course.course_open_date = course_open_date
            return course
        else:
            return None


def is_user_enrolled_in_any_class(course_current_class, course_next_classes):
    next_reg_classes = [next_class for next_class in course_next_classes if next_class['registered']]
    return bool(course_current_class or next_reg_classes)


# Query string parameters that can be passed to the "finish_auth" view to manage
# things like auto-enrollment.
POST_AUTH_PARAMS = ('course_id', 'enrollment_action', 'course_mode', 'email_opt_in', 'purchase_workflow')


def get_next_url_for_login_page_override(request):
    """
    NOTE*: We override this method to tackle alquity redirection scenarios
    Determine the URL to redirect to following login/registration/third_party_auth

    The user is currently on a login or registration page.
    If 'course_id' is set, or other POST_AUTH_PARAMS, we will need to send the user to the
    /account/finish_auth/ view following login, which will take care of auto-enrollment in
    the specified course.

    Otherwise, we go to the ?next= query param or to the dashboard if nothing else is
    specified.
    """
    import urllib
    from django.core.urlresolvers import NoReverseMatch
    from django.utils import http
    from lms.djangoapps.onboarding.helpers import get_alquity_community_url
    import logging
    log = logging.getLogger(__name__)

    redirect_to = request.GET.get('next', None)

    # sanity checks for alquity specific users
    if redirect_to == 'alquity' and request.path == '/register':
        if request.user.is_authenticated():
            return get_alquity_community_url()
        return reverse('dashboard')

    if redirect_to == 'alquity' and request.path == '/login':
        return get_alquity_community_url()

    # if we get a redirect parameter, make sure it's safe. If it's not, drop the
    # parameter.
    if redirect_to and not http.is_safe_url(redirect_to):
        log.error(
            u'Unsafe redirect parameter detected: %(redirect_to)r',
            {"redirect_to": redirect_to}
        )
        redirect_to = None

    course_id = request.GET.get('course_id', None)
    if not redirect_to:
        try:
            if course_id:
                redirect_to = reverse('info', args=[course_id])
            else:
                redirect_to = reverse('dashboard')
        except NoReverseMatch:
            redirect_to = reverse('home')
    if any(param in request.GET for param in POST_AUTH_PARAMS):
        # Before we redirect to next/dashboard, we need to handle auto-enrollment:
        params = [(param, request.GET[param]) for param in POST_AUTH_PARAMS if param in request.GET]
        params.append(('next', redirect_to))  # After auto-enrollment, user will be sent to payment page or to this URL
        redirect_to = '{}?{}'.format(reverse('finish_auth'), urllib.urlencode(params))
        # Note: if we are resuming a third party auth pipeline, then the next URL will already
        # be saved in the session as part of the pipeline state. That URL will take priority
        # over this one.
    return redirect_to


def save_user_partner_network_consent(user, _data):
    if _data:
        organization = user.extended_profile.organization
        consents = json.loads(_data)
        for _c in consents:
            organization_partner = organization.organization_partners.filter(
                partner=_c['code'], end_date=ORG_PARTNERSHIP_END_DATE_PLACEHOLDER
            ).first()
            if organization_partner:
                GranteeOptIn.objects.create(
                    agreed=_c['consent'] == 'true',
                    organization_partner=organization_partner,
                    user=user
                )


def get_activation_alert_error_msg_dict(user_id):
    return {
        'type': ACTIVATION_ALERT_TYPE,
        'alert': ACTIVATION_ERROR_MSG_FORMAT.format(
            api_endpoint=reverse('resend_activation_email'),
            user_id=user_id
        )
    }
