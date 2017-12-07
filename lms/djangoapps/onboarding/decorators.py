from django.core.exceptions import PermissionDenied


def can_save_org_data(function):
    def wrap(request, *args, **kwargs):
        user_extended_profile = request.user.extended_profile
        if user_extended_profile.is_organization_admin or user_extended_profile.organization.is_first_signup_in_org():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap