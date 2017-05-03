"""
Views for the Account Settings page.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render_to_response
from django.views.generic import View

from lms.djangoapps.student_account.views import account_settings_context

class AccountSettingsView(View):
    """
    Contains methods for rendering the account settings view.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request, **kwargs):
        """Render the current user's account settings page.

        Args:
            request (HttpRequest)

        Returns:
            HttpResponse: 200 if the page was sent successfully
            HttpResponse: 302 if not logged in (redirect to login page)
            HttpResponse: 405 if using an unsupported HTTP method

        Example usage:

            GET /account/settings/new

        """
        return render_to_response('account_settings/account-settings.html', account_settings_context(request))
