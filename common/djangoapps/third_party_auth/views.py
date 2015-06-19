"""
Extra views required for SSO
"""
from django.shortcuts import redirect


def inactive_user_view(request):
    """
    A newly registered user has completed the social auth pipeline.
    Their account is not yet activated, but we let them login this once.
    """
    # 'next' may be set to '/account/finish_auth/.../' if this user needs to be auto-enrolled
    # in a course. Otherwise, just redirect them to the dashboard, which displays a message
    # about activating their account.
    return redirect(request.GET.get('next', 'dashboard'))
