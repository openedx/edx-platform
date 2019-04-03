"""
Views that dispatch processing of OAuth requests to django-oauth2-provider or
django-oauth-toolkit as appropriate.
"""

from __future__ import unicode_literals

import json
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.views.generic import View
from django.contrib.auth.models import User
from edx_django_utils import monitoring as monitoring_utils
from edx_oauth2_provider import views as dop_views  # django-oauth2-provider views
from edx_oauth2_provider.forms import PasswordGrantForm
from django.core.exceptions import ObjectDoesNotExist

from provider.oauth2.views import OAuthError
from provider.oauth2.forms import PublicPasswordGrantForm
from provider.forms import OAuthValidationError
from provider.oauth2.models import Client
import provider.constants

from oauth2_provider import models as dot_models  # django-oauth-toolkit
from oauth2_provider import views as dot_views

from ratelimit import ALL
from ratelimit.mixins import RatelimitMixin

from openedx.core.djangoapps.auth_exchange import views as auth_exchange_views
from openedx.core.djangoapps.oauth_dispatch import adapters
from openedx.core.djangoapps.oauth_dispatch.dot_overrides import views as dot_overrides_views
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_from_token

from student.models import UserProfile

log = logging.getLogger(__name__)


class PasswordGrantFormByPhone(PasswordGrantForm, PublicPasswordGrantForm):
    def clean(self):
        data = self.cleaned_data  # pylint: disable=no-member
        username = data.get('username')
        password = data.get('password')

        try:
            user_obj = User.objects.get(username=username)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            try:
                user_obj = UserProfile.objects.get(phone=username).user
                user = authenticate(username=user_obj.username, password=password)
            except ObjectDoesNotExist:
                user = None

        if user is None:
            error_description = "Username does not exist or invalid credentials given for phone number '{}'.".format(
                username
            )
            log.error("OAuth2: {}".format(error_description))
            raise OAuthValidationError({
                'error': 'invalid_grant',
                'error_description': error_description
            })

        data['user'] = user
        try:
            client = Client.objects.get(client_id=data.get('client_id'))
        except Client.DoesNotExist:
            error_description = "Client ID '{}' does not exist.".format(data.get('client_id'))
            log.exception("OAuth2: {}".format(error_description))
            raise OAuthValidationError({
                'error': 'invalid_client',
                'error_description': error_description
            })

        if client.client_type != provider.constants.PUBLIC:
            error_description = "'{}' is not a public client.".format(client.client_type)
            log.error("OAuth2: {}".format(error_description))
            raise OAuthValidationError({
                'error': 'invalid_client',
                'error_description': error_description
            })
        data['client'] = client
        return data


class LoginByPhoneNumPasswordBackend(object):

    def authenticate(self, request=None):
        if request is None:
            return None

        form = PasswordGrantFormByPhone(request.POST)

        # pylint: disable=no-member

        if form.is_valid():
            return form.cleaned_data.get('client')

        return None


class AccessTokenView2(dop_views.AccessTokenView):
    authentication = dop_views.AccessTokenView.authentication + (LoginByPhoneNumPasswordBackend,)

    def get_password_grant(self, _request, data, client):
        form = PasswordGrantFormByPhone(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)

        return form.cleaned_data


class _DispatchingView(View):
    """
    Base class that route views to the appropriate provider view.  The default
    behavior routes based on client_id, but this can be overridden by redefining
    `select_backend()` if particular views need different behavior.
    """

    dot_adapter = adapters.DOTAdapter()
    dop_adapter = adapters.DOPAdapter()

    def get_adapter(self, request):
        """
        Returns the appropriate adapter based on the OAuth client linked to the request.
        """
        client_id = self._get_client_id(request)
        monitoring_utils.set_custom_metric('oauth_client_id', client_id)

        if dot_models.Application.objects.filter(client_id=client_id).exists():
            monitoring_utils.set_custom_metric('oauth_adapter', 'dot')
            return self.dot_adapter
        else:
            monitoring_utils.set_custom_metric('oauth_adapter', 'dop')
            return self.dop_adapter

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch the request to the selected backend's view.
        """
        backend = self.select_backend(request)
        view = self.get_view_for_backend(backend)
        return view(request, *args, **kwargs)

    def select_backend(self, request):
        """
        Given a request that specifies an oauth `client_id`, return the adapter
        for the appropriate OAuth handling library.  If the client_id is found
        in a django-oauth-toolkit (DOT) Application, use the DOT adapter,
        otherwise use the django-oauth2-provider (DOP) adapter, and allow the
        calls to fail normally if the client does not exist.
        """
        return self.get_adapter(request).backend

    def get_view_for_backend(self, backend):
        """
        Return the appropriate view from the requested backend.
        """
        if backend == self.dot_adapter.backend:
            return self.dot_view.as_view()
        elif backend == self.dop_adapter.backend:
            return self.dop_view.as_view()
        else:
            raise KeyError('Failed to dispatch view. Invalid backend {}'.format(backend))

    def _get_client_id(self, request):
        """
        Return the client_id from the provided request
        """
        if request.method == u'GET':
            return request.GET.get('client_id')
        else:
            return request.POST.get('client_id')


class NewTokenView(dot_views.TokenView):

    @classmethod
    def get_server(cls):
        """
        Return an instance of `server_class` initialized with a `validator_class`
        object
        """
        server_class = cls.get_server_class()
        validator_class = cls.get_validator_class()
        return server_class(request_validator=validator_class(),
                            token_expires_in=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'])


class AccessTokenView(RatelimitMixin, _DispatchingView):
    """
    Handle access token requests.
    """
    dot_view = NewTokenView
    dop_view = AccessTokenView2
    ratelimit_key = 'openedx.core.djangoapps.util.ratelimit.real_ip'
    ratelimit_rate = settings.RATELIMIT_RATE
    ratelimit_block = True
    ratelimit_method = ALL

    def dispatch(self, request, *args, **kwargs):
        response = super(AccessTokenView, self).dispatch(request, *args, **kwargs)

        token_type = request.POST.get('token_type', 'no_token_type_supplied').lower()
        monitoring_utils.set_custom_metric('oauth_token_type', token_type)
        monitoring_utils.set_custom_metric('oauth_grant_type', request.POST.get('grant_type', ''))

        if response.status_code == 200 and token_type == 'jwt':
            response.content = self._build_jwt_response_from_access_token_response(request, response)

        return response

    def _build_jwt_response_from_access_token_response(self, request, response):
        """ Builds the content of the response, including the JWT token. """
        token_dict = json.loads(response.content)
        jwt = create_jwt_from_token(token_dict, self.get_adapter(request))
        token_dict.update({
            'access_token': jwt,
            'token_type': 'JWT',
        })
        return json.dumps(token_dict)


class AuthorizationView(_DispatchingView):
    """
    Part of the authorization flow.
    """
    dop_view = dop_views.Capture
    dot_view = dot_overrides_views.EdxOAuth2AuthorizationView


class AccessTokenExchangeView(_DispatchingView):
    """
    Exchange a third party auth token.
    """
    dop_view = auth_exchange_views.DOPAccessTokenExchangeView
    dot_view = auth_exchange_views.DOTAccessTokenExchangeView


class RevokeTokenView(_DispatchingView):
    """
    Dispatch to the RevokeTokenView of django-oauth-toolkit
    """
    dot_view = dot_views.RevokeTokenView
