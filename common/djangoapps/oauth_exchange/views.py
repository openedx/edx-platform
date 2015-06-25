"""
Views to support third-party to first-party OAuth 2.0 access token exchange
"""
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from provider import constants
from provider.oauth2.views import AccessTokenView as AccessTokenView
import social.apps.django_app.utils as social_utils

from oauth_exchange.forms import AccessTokenExchangeForm


class AccessTokenExchangeView(AccessTokenView):
    """View for access token exchange"""
    @method_decorator(csrf_exempt)
    @method_decorator(social_utils.strategy("social:complete"))
    def dispatch(self, *args, **kwargs):
        return super(AccessTokenExchangeView, self).dispatch(*args, **kwargs)

    def get(self, request, _backend):
        return super(AccessTokenExchangeView, self).get(request)

    def post(self, request, _backend):
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
