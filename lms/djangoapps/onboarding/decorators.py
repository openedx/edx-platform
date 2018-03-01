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
    are_forms_complete = not (bool(user_extended_profile.unattended_surveys(_type='list')))

    # user have completed profile & is admin of organization => can access org page
    if are_forms_complete and user_extended_profile.organization and user_extended_profile.is_organization_admin:
        can_access = True

    # user is at registration pages & signup as admin/first_learner => can access org page
    elif not are_forms_complete and user_extended_profile.organization and \
        (user_extended_profile.is_organization_admin or user_extended_profile.is_first_signup_in_org):
        can_access = True
    else:
        can_access = False

    return can_access


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

        if can_access_org_page(user_extended_profile) and \
                        user_extended_profile.organization.org_type == PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def can_not_update_onboarding_steps(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile
        are_forms_complete = not (bool(user_extended_profile.unattended_surveys(_type='list')))
        if are_forms_complete and request.path in [reverse('user_info'), reverse('interests'), reverse('organization'),
                                                   reverse('org_detail_survey')]:

            if request.path == reverse('org_detail_survey'):
                redirect_url = reverse('recommendations')
            else:
                redirect_url = reverse('update_account_settings')
            return redirect(redirect_url)

        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
