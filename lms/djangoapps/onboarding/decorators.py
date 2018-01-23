from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect


def can_save_org_data(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile
        if user_extended_profile.organization and \
                (user_extended_profile.is_organization_admin or
                     user_extended_profile.organization.is_first_signup_in_org()):
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
            return redirect(reverse('update_account_settings'))

        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
