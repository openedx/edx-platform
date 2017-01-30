"""
Decorators that can be used to interact with branding.
"""
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test, login_required
from django.conf import settings

def courses_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    This decorator relies on the feature flag ENABLE_COURSES_LOGIN_REQUIRED
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        if settings.APPSEMBLER_FEATURES.get(
                'ENABLE_COURSES_LOGIN_REQUIRED', False
        ):
            return actual_decorator(function)
        else:
            return function
    return actual_decorator