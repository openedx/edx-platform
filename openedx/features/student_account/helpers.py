import logging
import operator

from datetime import datetime
from pytz import utc

import third_party_auth

from mailchimp_pipeline.signals.handlers import task_send_account_activation_email

from constants import NON_ACTIVE_COURSE_NOTIFICATION, TOP_REGISTRATION_COUNTRIES
from student.models import CourseEnrollment
from courseware.models import StudentModule

from openedx.features.course_card.helpers import get_course_open_date
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from openedx.core.lib.request_utils import safe_get_host

from lms.djangoapps.onboarding.helpers import COUNTRIES
from lms.djangoapps.onboarding.models import EmailPreference, Organization, UserExtendedProfile
from lms.djangoapps.philu_overrides.constants import ACTIVATION_ALERT_TYPE


log = logging.getLogger("edx.student")


def get_non_active_course(user):
    DAYS_TO_DISPLAY_NOTIFICATION = 7

    all_user_courses = CourseEnrollment.objects.filter(user=user, is_active=True)

    non_active_courses = []
    non_active_course_info = []

    for user_course in all_user_courses:

        today = datetime.now(utc).date()

        try:
            course = CourseOverview.objects.get(id=user_course.course_id, end__gte=today)
        except CourseOverview.DoesNotExist:
            continue

        course_start_date = get_course_open_date(course).date()
        delta_date = today - course_start_date

        if delta_date.days >= DAYS_TO_DISPLAY_NOTIFICATION:

            modules = StudentModule.objects.filter(course_id=course.id, student_id=user.id,
                                                   created__gt=course_start_date)

            # Make this check equals to zero to make it more generic.
            if len(modules) <= 0:
                non_active_courses.append(course)

    if len(non_active_courses) > 0:
        error = NON_ACTIVE_COURSE_NOTIFICATION % (non_active_courses[0].display_name,
                                                  get_course_first_chapter_link(course=non_active_courses[0]))
        non_active_course_info.append({"type": ACTIVATION_ALERT_TYPE,
                                       "alert": error})
    return non_active_course_info


def save_user_utm_info(req, user):
    """
    :param req:
        request to get all utm related params
    :param user:
        user for which utm params are being saved
    :return:
    """
    def extract_param_value(request, param_name):
        utm_value = request.POST.get(param_name, None)

        if not utm_value and param_name in request.session:
            utm_value = request.session[param_name]
            del request.session[param_name]

        return utm_value

    try:
        utm_source = extract_param_value(req, "utm_source")
        utm_medium = extract_param_value(req, "utm_medium")
        utm_campaign = extract_param_value(req, "utm_campaign")
        utm_content = extract_param_value(req, "utm_content")
        utm_term = extract_param_value(req, "utm_term")

        from openedx.features.user_leads.models import UserLeads
        UserLeads.objects.create(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_content=utm_content,
            utm_term=utm_term,
            user=user
        )
    except Exception as ex:
        log.error("There is some error saving UTM {}".format(str(ex)))
        pass


def set_opt_in_and_affiliate_user_organization(user, form):
    org_name = form.cleaned_data.get('organization_name')
    org_type = form.cleaned_data.get('organization_type')
    user_extended_profile_data = {}

    if org_name:
        user_organization, org_created = Organization.objects.get_or_create(label=org_name)
        org_size = form.cleaned_data.get('organization_size')

        if org_created:
            user_organization.total_employees = org_size
            user_organization.org_type = org_type
            user_organization.save()
            is_first_learner = True
        else:
            if org_size:
                user_organization.total_employees = org_size

            if org_type:
                user_organization.org_type = org_type

            user_organization.save()
            is_first_learner = user_organization.can_join_as_first_learner(exclude_user=user)

        user_extended_profile_data = {
            'is_first_learner': is_first_learner,
            'organization_id': user_organization.id
        }

    # create User Extended Profile
    user_extended_profile = UserExtendedProfile.objects.create(user=user, **user_extended_profile_data)

    # create user email preferences object
    EmailPreference.objects.create(user=user, opt_in=form.cleaned_data.get('opt_in'))


def compose_and_send_activation_email_custom(request, registration, user):
    activation_link = '{protocol}://{site}/activate/{key}'.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        key=registration.activation_key
    )
    data = {
        "activation_link": activation_link,
        "user_email": user.email,
        'first_name': user.first_name,
    }

    task_send_account_activation_email.delay(data)


def check_and_add_third_party_params(request, params):
    """
    Adds backend and access token from current running third_party_auth
    provider to the params.
    :param request: request object
    :param params: params dictionary
    """
    if third_party_auth.is_enabled() and third_party_auth.pipeline.running(request):
        running_pipeline = third_party_auth.pipeline.get(request)

        if running_pipeline.get('backend'):
            params['provider'] = running_pipeline.get('backend')

        params['access_token'] = running_pipeline['kwargs']['response']['access_token']


def get_registration_countries():
    return {
        'all_countries': sorted(COUNTRIES.items(), key=operator.itemgetter(1)),
        'top_countries': TOP_REGISTRATION_COUNTRIES or []
    }
