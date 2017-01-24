"""Programs views for use with Studio."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from provider.oauth2.models import Client

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.lib.token_utils import JwtBuilder


class ProgramAuthoringView(View):
    """View rendering a template which hosts the Programs authoring app.

    The Programs authoring app is a Backbone SPA. The app handles its own routing
    and provides a UI which can be used to create and publish new Programs.
    """

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Populate the template context with values required for the authoring app to run."""
        programs_config = ProgramsApiConfig.current()

        if programs_config.is_studio_tab_enabled and request.user.is_staff:
            return render_to_response('program_authoring.html', {
                'lms_base_url': '//{}/'.format(settings.LMS_BASE),
                'programs_api_url': programs_config.public_api_url,
                'programs_token_url': reverse('programs_id_token'),
                'studio_home_url': reverse('home'),
                'uses_pattern_library': True
            })
        else:
            raise Http404


class ProgramsIdTokenView(View):
    """Provides id tokens to JavaScript clients for use with the Programs API."""

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Generate and return a token, if the integration is enabled."""
        if ProgramsApiConfig.current().is_studio_tab_enabled:
            # TODO: Use the system's JWT_AUDIENCE and JWT_SECRET_KEY instead of client ID and name.
            client_name = 'programs'

            try:
                client = Client.objects.get(name=client_name)
            except Client.DoesNotExist:
                raise ImproperlyConfigured(
                    'OAuth2 Client with name [{}] does not exist.'.format(client_name)
                )

            scopes = ['email', 'profile']
            expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
            jwt = JwtBuilder(request.user, secret=client.client_secret).build_token(
                scopes,
                expires_in,
                aud=client.client_id
            )

            return JsonResponse({'id_token': jwt})
        else:
            raise Http404
