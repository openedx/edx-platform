"""
helpers functions for Admin Panel API
"""
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.db.models import Count, Q
from django.urls import reverse
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.pakx.lms.overrides.models import CourseProgressStats
from student.models import Registration

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER
from .message_types import RegistrationNotification


def get_user_org_filter(user):
    return {'profile__organization_id': user.profile.organization_id}


def get_user_org(user):
    """get org for given user object"""

    user_org = getattr(user.profile.organization, "short_name", "").lower()
    if user_org == 'arbisoft':  # TODO: REMOVE THIS IF WHEN WORK PLACE ESSENTIALS COURSES ARE REMOVED
        return r'({}|{})'.format(user_org, 'pakx')
    return r'({})'.format(user_org)


def get_course_overview_same_org_filter(user):
    """get same org filter with respect course's org"""

    return Q(org__iregex=get_user_org(user))


def get_user_same_org_filter(user):
    """get same org filter with respect to user's profile-> org"""

    return Q(profile__organization__short_name__iregex=get_user_org(user))


def get_learners_filter():
    """get learners filter, excludes dummy emails & add org condition """
    return Q(
        Q(is_superuser=False) & Q(is_staff=False) & ~(Q(email__icontains='fake') | Q(email__icontains='example'))
    )


def get_user_enrollment_same_org_filter(user):
    """get filter against enrollment record and user's course enrollment, enrollment->course->org"""

    return Q(courseenrollment__user__profile__organization__short_name__iregex=get_user_org(user))


def get_roles_q_filters(roles):
    """
    return Q filter to be used for filter user queryset
    :param roles: request params to filter roles
    :param user: (User) user object

    :return: Q filters
    """
    qs = Q()

    for role in roles:
        if int(role) == ORG_ADMIN:
            qs |= Q(groups__name=GROUP_ORGANIZATION_ADMIN)
        elif int(role) == LEARNER:
            qs |= get_learners_filter()
        elif int(role) == TRAINING_MANAGER:
            qs |= Q(groups__name=GROUP_TRAINING_MANAGERS)

    return qs


def specify_user_role(user, role):
    g_admin, g_tm = Group.objects.filter(
        name__in=[GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS]
    ).order_by('name')

    if role == ORG_ADMIN:
        user.groups.add(g_admin)
        user.groups.remove(g_tm)
    elif role == TRAINING_MANAGER:
        user.groups.remove(g_admin)
        user.groups.add(g_tm)
    elif role == LEARNER:
        user.groups.remove(g_admin, g_tm)


def get_registration_email_message_context(user, password, protocol, is_public_registration):
    """
    return context for registration notification email body
    """
    site = Site.objects.get_current()
    activation_key = Registration.objects.get(user=user).activation_key
    message_context = {
        'site_name': site.domain
    }
    message_context.update(get_base_template_context(site, user=user))
    message_context.update({
        'is_public_registration': is_public_registration,
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'password': password,
        'email': user.email,
        'employee_id': user.profile.employee_id,
        'language': user.profile.language,
        'account_activation_link': '{protocol}://{site}{link}'.format(
            protocol=protocol,
            site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            link=reverse('activate', kwargs={'key': activation_key}),
        )
    })
    return message_context


def get_completed_course_count_filters(exclude_staff_superuser=False, user=None):
    completed = Q(
        Q(courseenrollment__enrollment_stats__email_reminder_status=CourseProgressStats.COURSE_COMPLETED) &
        Q(courseenrollment__is_active=True)
    )
    in_progress = Q(
        Q(courseenrollment__enrollment_stats__email_reminder_status__lt=CourseProgressStats.COURSE_COMPLETED) &
        Q(courseenrollment__is_active=True)
    )

    if exclude_staff_superuser:
        learners = Q(courseenrollment__user__is_staff=False) & Q(courseenrollment__user__is_superuser=False)
        if not user.is_superuser:
            learners = Q(learners & get_user_enrollment_same_org_filter(user))
        completed = Q(learners & completed)
        in_progress = Q(learners & in_progress)

    completed_count = Count("courseenrollment", filter=completed)
    in_progress_count = Count("courseenrollment", filter=in_progress)
    return completed_count, in_progress_count


def get_org_users_qs(user):
    """
    return users from the same organization as of the request.user
    """
    queryset = User.objects.filter(get_learners_filter())
    if not user.is_superuser:
        queryset = queryset.filter(get_user_same_org_filter(user))

    return queryset.select_related(
        'profile'
    )


def get_enroll_able_course_qs():
    """
    :return: Q filter for enroll-able courses based on course enrollment & course_end dates
    """
    now = datetime.now(pytz.UTC)
    # A Course is "enroll-able" if its enrollment start date has passed,
    # is now, or is None, and its enrollment end date is in the future or is None.
    return (
        (Q(enrollment_start__lte=now) | Q(enrollment_start__isnull=True)) &
        (Q(enrollment_end__gt=now) | Q(enrollment_end__isnull=True)) &
        (Q(end_date__gt=now) | Q(end_date__isnull=True))
    )


def get_user_available_course_qs(user):
    """
    :return: Q filter for enroll-able courses for a user based on its org and course enrollment & course_end dates
    """
    return get_enroll_able_course_qs() & get_course_overview_same_org_filter(user)


def send_registration_email(user, password, protocol, is_public_registration=False):
    """
    send a registration notification via email
    """
    message = RegistrationNotification().personalize(
        recipient=Recipient(user.username, user.email),
        language=user.profile.language,
        user_context=get_registration_email_message_context(user, password, protocol, is_public_registration),
    )
    ace.send(message)
