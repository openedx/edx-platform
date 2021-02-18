from django.core.exceptions import PermissionDenied

from lms.djangoapps.onboarding.models import PartnerNetwork, Organization
from lms.djangoapps.onboarding.helpers import oef_eligible_first_learner


def can_take_oef(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile

        if eligible_for_oef(user_extended_profile):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def eligible_for_oef(user_extended_profile):
    """
    :return: True if user can take OEF
    """
    return user_extended_profile.organization and Organization.is_non_profit(user_extended_profile) and \
        (user_extended_profile.is_organization_admin or oef_eligible_first_learner(user_extended_profile))
