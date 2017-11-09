"""
Fragments for rendering programs.
"""
from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import get_language_bidi
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramProgressMeter,
    get_program_marketing_url
)


class ProgramsFragmentView(EdxFragmentView):
    """
    A fragment to program listing.
    """
    def render_to_fragment(self, request, **kwargs):
        """
        Render the program listing fragment.
        """
        user = request.user
        programs_config = kwargs.get('programs_config') or ProgramsApiConfig.current()
        if not programs_config.enabled or not user.is_authenticated():
            raise Http404

        meter = ProgramProgressMeter(request.site, user)

        context = {
            'marketing_url': get_program_marketing_url(programs_config),
            'programs': meter.engaged_programs,
            'progress': meter.progress()
        }
        html = render_to_string('learner_dashboard/programs_fragment.html', context)
        programs_fragment = Fragment(html)
        self.add_fragment_resource_urls(programs_fragment)

        return programs_fragment

    def css_dependencies(self):
        """
        Returns list of CSS files that this view depends on.

        The helper function that it uses to obtain the list of CSS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        if get_language_bidi():
            return self.get_css_dependencies('style-learner-dashboard-rtl')
        else:
            return self.get_css_dependencies('style-learner-dashboard')
