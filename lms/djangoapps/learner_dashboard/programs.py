"""
Fragments for rendering programs.
"""
from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import get_language_bidi
from django.core.urlresolvers import reverse

from web_fragments.fragment import Fragment

from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.learner_dashboard.utils import FAKE_COURSE_KEY, strip_course_id
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramDataExtender,
    ProgramProgressMeter,
    get_certificates,
    get_program_marketing_url
)
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences


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


class ProgramDetailsFragmentView(EdxFragmentView):
    """
    Render the program details fragment.
    """
    def render_to_fragment(self, request, program_uuid, **kwargs):
        """View details about a specific program."""
        programs_config = kwargs.get('programs_config') or ProgramsApiConfig.current()
        if not programs_config.enabled or not request.user.is_authenticated():
            raise Http404

        meter = ProgramProgressMeter(request.site, request.user, uuid=program_uuid)
        program_data = meter.programs[0]

        if not program_data:
            raise Http404

        program_data = ProgramDataExtender(program_data, request.user).extend()
        course_data = meter.progress(programs=[program_data], count_only=False)[0]
        certificate_data = get_certificates(request.user, program_data)

        program_data.pop('courses')
        skus = program_data.get('skus')
        ecommerce_service = EcommerceService()

        urls = {
            'program_listing_url': reverse('program_listing_view'),
            'track_selection_url': strip_course_id(
                reverse('course_modes_choose', kwargs={'course_id': FAKE_COURSE_KEY})
            ),
            'commerce_api_url': reverse('commerce_api:v0:baskets:create'),
            'buy_button_url': ecommerce_service.get_checkout_page_url(*skus)
        }

        context = {
            'urls': urls,
            'user_preferences': get_user_preferences(request.user),
            'program_data': program_data,
            'course_data': course_data,
            'certificate_data': certificate_data
        }

        html = render_to_string('learner_dashboard/program_details_fragment.html', context)
        program_details_fragment = Fragment(html)
        self.add_fragment_resource_urls(program_details_fragment)
        return program_details_fragment

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
