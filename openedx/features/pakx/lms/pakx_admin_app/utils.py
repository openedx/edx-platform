"""
helpers functions for Admin Panel API
"""
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.db.models.query_utils import Q
from django.urls import reverse
from django.utils.http import int_to_base36
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER
from .message_types import RegistrationNotification


def get_user_org_filter(user):
    return {'profile__organization_id': user.profile.organization_id}


def get_learners_filter():
    return Q(
        Q(is_superuser=False) & Q(is_staff=False) &
        ~Q(groups__name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN])
    )


def get_roles_q_filters(roles):
    """
    return Q filter to be used for filter user queryset
    :param roles: request params to filter roles
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
    if role == ORG_ADMIN:
        user.groups.add(Group.objects.get(name=GROUP_ORGANIZATION_ADMIN))
    elif role == TRAINING_MANAGER:
        user.groups.add(Group.objects.get(name=GROUP_TRAINING_MANAGERS))


def get_email_message_context(user, user_profile, protocol):
    """
    return context for registration notification email body
    """
    site = Site.objects.get_current()
    message_context = {
        'site_name': site.domain
    }
    message_context.update(get_base_template_context(site))
    message_context.update({
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'firstname': user.first_name,
        'username': user.username,
        'email': user.email,
        'employee_id': user_profile.employee_id,
        'language': user_profile.language,
        'reset_password_link': '{protocol}://{site}{link}'.format(
            protocol=protocol,
            site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            link=reverse('password_reset_confirm', kwargs={
                'uidb36': int_to_base36(user.id),
                'token': default_token_generator.make_token(user),
            }),
        )
    })
    return message_context


def send_registration_email(user, user_profile, protocol):
    """
    send a registration notification via email
    """
    message = RegistrationNotification().personalize(
        recipient=Recipient(user.username, user.email),
        language=user_profile.language,
        user_context=get_email_message_context(user, user_profile, protocol),
    )
    ace.send(message)
