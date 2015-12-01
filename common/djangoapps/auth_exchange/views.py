# pylint: disable=abstract-method
"""
Views to support exchange of authentication credentials.
The following are currently implemented:
    1. AccessTokenExchangeView:
       3rd party (social-auth) OAuth 2.0 access token -> 1st party (open-edx) OAuth 2.0 access token
    2. LoginWithAccessTokenView:
       1st party (open-edx) OAuth 2.0 access token -> session cookie
"""
from django.conf import settings
from django.contrib.auth import login
import django.contrib.auth as auth
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from provider import constants
from provider.oauth2.views import AccessTokenView as AccessTokenView
from rest_framework import permissions
from rest_framework.views import APIView
import social.apps.django_app.utils as social_utils

from auth_exchange.forms import AccessTokenExchangeForm
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser


class AccessTokenExchangeView(AccessTokenView):
    """
    View for token exchange from 3rd party OAuth access token to 1st party OAuth access token
    """
    @method_decorator(csrf_exempt)
    @method_decorator(social_utils.strategy("social:complete"))
    def dispatch(self, *args, **kwargs):
        return super(AccessTokenExchangeView, self).dispatch(*args, **kwargs)

    def get(self, request, _backend):  # pylint: disable=arguments-differ
        return super(AccessTokenExchangeView, self).get(request)

    def post(self, request, _backend):  # pylint: disable=arguments-differ
        form = AccessTokenExchangeForm(request=request, data=request.POST)
        if not form.is_valid():
            return self.error_response(form.errors)

        user = form.cleaned_data["user"]
        scope = form.cleaned_data["scope"]
        client = form.cleaned_data["client"]

        if constants.SINGLE_ACCESS_TOKEN:
            edx_access_token = self.get_access_token(request, user, scope, client)
        else:
            edx_access_token = self.create_access_token(request, user, scope, client)

        return self.access_token_response(edx_access_token)


class LoginWithAccessTokenView(APIView):
    """
    View for exchanging an access token for session cookies
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def _get_path_of_arbitrary_backend_for_user(user):
        """
        Return the path to the first found authentication backend that recognizes the given user.
        """
        for backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = auth.load_backend(backend_path)
            if backend.get_user(user.id):
                return backend_path

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Handler for the POST method to this view.
        """
        # The django login method stores the user's id in request.session[SESSION_KEY] and the
        # path to the user's authentication backend in request.session[BACKEND_SESSION_KEY].
        # The login method assumes the backend path had been previously stored in request.user.backend
        # in the 'authenticate' call.  However, not all authentication providers do so.
        # So we explicitly populate the request.user.backend field here.
        if not hasattr(request.user, 'backend'):
            request.user.backend = self._get_path_of_arbitrary_backend_for_user(request.user)
        login(request, request.user)  # login generates and stores the user's cookies in the session
        return HttpResponse(status=204)  # cookies stored in the session are returned with the response
