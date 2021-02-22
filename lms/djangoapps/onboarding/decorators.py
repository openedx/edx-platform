from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from lms.djangoapps.onboarding.models import PartnerNetwork


def can_access_org_page(user_extended_profile):
    """
    Only org admin or first learner in org is allowed add organization details. Once registration completed,
     first learner is restricted to access org data update pages until he become admin
    :param user_extended_profile:
    :return: boolean
    """
    return bool(user_extended_profile.organization and
                (user_extended_profile.is_organization_admin or
                 user_extended_profile.is_first_signup_in_org))


def can_save_org_data(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile

        if can_access_org_page(user_extended_profile):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def can_save_org_details(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile

        if (can_access_org_page(user_extended_profile) and
                user_extended_profile.organization.org_type == PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
