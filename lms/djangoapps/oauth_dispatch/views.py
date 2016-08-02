"""
Views that dispatch processing of OAuth requests to django-oauth2-provider or
django-oauth-toolkit as appropriate.
"""

from __future__ import unicode_literals

import json
from time import time

import jwt
from auth_exchange import views as auth_exchange_views
from django.conf import settings
from django.utils.functional import cached_property
from django.views.generic import View
from edx_oauth2_provider import views as dop_views  # django-oauth2-provider views
from oauth2_provider import models as dot_models, views as dot_views  # django-oauth-toolkit

from openedx.core.lib.token_utils import JwtBuilder

from . import adapters


class _DispatchingView(View):
    """
    Base class that route views to the appropriate provider view.  The default
    behavior routes based on client_id, but this can be overridden by redefining
    `select_backend()` if particular views need different behavior.
    """
    # pylint: disable=no-member

    dot_adapter = adapters.DOTAdapter()
    dop_adapter = adapters.DOPAdapter()

    def get_adapter(self, request):
        """
        Returns the appropriate adapter based on the OAuth client linked to the request.
        """
        if dot_models.Application.objects.filter(client_id=self._get_client_id(request)).exists():
            return self.dot_adapter
        else:
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


class AccessTokenView(_DispatchingView):
    """
    Handle access token requests.
    """
    dot_view = dot_views.TokenView
    dop_view = dop_views.AccessTokenView

    def dispatch(self, request, *args, **kwargs):
        response = super(AccessTokenView, self).dispatch(request, *args, **kwargs)

        if response.status_code == 200 and request.POST.get('token_type', '').lower() == 'jwt':
            expires_in, scopes, user = self._decompose_access_token_response(request, response)

            content = {
                'access_token': JwtBuilder(user).build_token(scopes, expires_in),
                'expires_in': expires_in,
                'token_type': 'JWT',
                'scope': ' '.join(scopes),
            }
            response.content = json.dumps(content)

        return response

    def _decompose_access_token_response(self, request, response):
        """ Decomposes the access token in the request to an expiration date, scopes, and User. """
        content = json.loads(response.content)
        access_token = content['access_token']
        scope = content['scope']
        access_token_obj = self.get_adapter(request).get_access_token(access_token)
        user = access_token_obj.user
        scopes = scope.split(' ')
        expires_in = content['expires_in']
        return expires_in, scopes, user


class AuthorizationView(_DispatchingView):
    """
    Part of the authorization flow.
    """
    dop_view = dop_views.Capture
    dot_view = dot_views.AuthorizationView


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
