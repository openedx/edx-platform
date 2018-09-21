""" Views related to logout. """
from urlparse import parse_qs, urlsplit, urlunsplit

import edx_oauth2_provider
from django.conf import settings
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.views.generic import TemplateView
from provider.oauth2.models import Client
from openedx.core.djangoapps.user_authn.cookies import delete_logged_in_cookies
from student.helpers import is_safe_redirect


class LogoutView(TemplateView):
    """
    Logs out user and redirects.

    The template should load iframes to log the user out of OpenID Connect services.
    See http://openid.net/specs/openid-connect-logout-1_0.html.
    """
    oauth_client_ids = []
    template_name = 'logout.html'

    # Keep track of the page to which the user should ultimately be redirected.
    default_target = reverse_lazy('cas-logout') if settings.FEATURES.get('AUTH_USE_CAS') else '/'

    @property
    def target(self):
        """
        If a redirect_url is specified in the querystring for this request, and the value is a url
        with the same host, the view will redirect to this page after rendering the template.
        If it is not specified, we will use the default target url.
        """
        target_url = self.request.GET.get('redirect_url')

        if target_url and is_safe_redirect(self.request, target_url):
            return target_url
        else:
            return self.default_target

    def dispatch(self, request, *args, **kwargs):
        # We do not log here, because we have a handler registered to perform logging on successful logouts.
        request.is_from_logout = True

        # Get the list of authorized clients before we clear the session.
        self.oauth_client_ids = request.session.get(edx_oauth2_provider.constants.AUTHORIZED_CLIENTS_SESSION_KEY, [])

        logout(request)

        # If we don't need to deal with OIDC logouts, just redirect the user.
        if self.oauth_client_ids:
            response = super(LogoutView, self).dispatch(request, *args, **kwargs)
        else:
            response = redirect(self.target)

        # Clear the cookie used by the edx.org marketing site
        delete_logged_in_cookies(response)

        return response

    def _build_logout_url(self, url):
        """
        Builds a logout URL with the `no_redirect` query string parameter.

        Args:
            url (str): IDA logout URL

        Returns:
            str
        """
        scheme, netloc, path, query_string, fragment = urlsplit(url)
        query_params = parse_qs(query_string)
        query_params['no_redirect'] = 1
        new_query_string = urlencode(query_params, doseq=True)
        return urlunsplit((scheme, netloc, path, new_query_string, fragment))

    def get_context_data(self, **kwargs):
        context = super(LogoutView, self).get_context_data(**kwargs)

        # Create a list of URIs that must be called to log the user out of all of the IDAs.
        uris = Client.objects.filter(client_id__in=self.oauth_client_ids,
                                     logout_uri__isnull=False).values_list('logout_uri', flat=True)

        referrer = self.request.META.get('HTTP_REFERER', '').strip('/')
        logout_uris = []

        for uri in uris:
            if not referrer or (referrer and not uri.startswith(referrer)):
                logout_uris.append(self._build_logout_url(uri))

        context.update({
            'target': self.target,
            'logout_uris': logout_uris,
        })

        return context
