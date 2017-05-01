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

class AccountSettingsView(View):
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request, **kwargs):
        context = {
            'foo': 'bar'
        }
        context = {
            'csrf': csrf(request)['csrf_token'],
            'supports_preview_menu': True,
            'disable_courseware_js': True,
            'foo': 'bar'
        }
        return render_to_response('account_settings/account-settings.html', context)
