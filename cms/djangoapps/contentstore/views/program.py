"""Programs views for use with Studio."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.lib.token_utils import get_id_token


class ProgramAuthoringView(View):
    """View rendering a template which hosts the Programs authoring app.

    The Programs authoring app is a Backbone SPA maintained in a separate repository.
    The app handles its own routing and provides a UI which can be used to create and
    publish new Programs (e.g, XSeries).
    """

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Populate the template context with values required for the authoring app to run."""
        programs_config = ProgramsApiConfig.current()

        if programs_config.is_studio_tab_enabled and request.user.is_staff:
            return render_to_response('program_authoring.html', {
                'show_programs_header': programs_config.is_studio_tab_enabled,
                'authoring_app_config': programs_config.authoring_app_config,
                'lms_base_url': '//{}/'.format(settings.LMS_BASE),
                'programs_api_url': programs_config.public_api_url,
                'programs_token_url': reverse('programs_id_token'),
                'studio_home_url': reverse('home'),
            })
        else:
            raise Http404


class ProgramsIdTokenView(View):
    """Provides id tokens to JavaScript clients for use with the Programs API."""

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Generate and return a token, if the integration is enabled."""
        if ProgramsApiConfig.current().is_studio_tab_enabled:
            id_token = get_id_token(request.user, 'programs')
            return JsonResponse({'id_token': id_token})
        else:
            raise Http404
