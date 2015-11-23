"""Programs views for use with Studio."""
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramAuthoringView(View):
    """View rendering a template which hosts the Programs authoring app.

    The Programs authoring app is a Backbone SPA maintained in a separate repository.
    The app handles its own routing and provides a UI which can be used to create and
    publish new Programs (e.g, XSeries).
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Relays requests to matching methods.

        Decorated to require login before accessing the authoring app.
        """
        return super(ProgramAuthoringView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Populate the template context with values required for the authoring app to run."""
        programs_config = ProgramsApiConfig.current()

        if programs_config.is_studio_tab_enabled and request.user.is_staff:
            return render_to_response('program_authoring.html', {
                'show_programs_header': programs_config.is_studio_tab_enabled,
                'authoring_app_config': programs_config.authoring_app_config,
                'programs_api_url': programs_config.public_api_url,
                'studio_home_url': reverse('home'),
            })
        else:
            raise Http404
