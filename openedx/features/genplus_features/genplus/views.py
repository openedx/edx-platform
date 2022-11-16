import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from common.djangoapps import third_party_auth
from common.djangoapps.third_party_auth import pipeline


@ensure_csrf_cookie
def authenticate_user(request):
    frontend_url = settings.GENPLUS_FRONTEND_URL
    if request.user.is_authenticated:
        # redirect to custom dashboard of genplus if authenticated
        dashboard_url = frontend_url if frontend_url else 'dashboard'
        return redirect(dashboard_url)
    else:
        provider_id = request.GET.get('provider_id', '-')
        provider = third_party_auth.provider.Registry.get(provider_id=provider_id)
        if not provider:
            raise Http404

        login_url = pipeline.get_login_url(
            provider.provider_id,
            pipeline.AUTH_ENTRY_LOGIN,
            redirect_url=frontend_url,
        )

        return redirect(login_url)
