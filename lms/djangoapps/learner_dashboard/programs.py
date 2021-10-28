"""
Fragments for rendering programs.
"""


import json

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _  # lint-amnesty, pylint: disable=unused-import
from web_fragments.fragment import Fragment

from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.learner_dashboard.utils import FAKE_COURSE_KEY, strip_course_id, program_discussions_is_enabled
from lti_consumer.lti_1p1.contrib.django import lti_embed
from openedx.core.djangoapps.catalog.constants import PathwayType
from openedx.core.djangoapps.catalog.utils import get_pathways
from openedx.core.djangoapps.credentials.utils import get_credentials_records_url
from openedx.core.djangoapps.discussions.models import ProgramDiscussionsConfiguration
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramDataExtender,
    ProgramProgressMeter,
    get_certificates,
    get_program_marketing_url
)
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from openedx.core.djangolib.markup import HTML


class ProgramsFragmentView(EdxFragmentView):
    """
    A fragment to program listing.
    """

    def render_to_fragment(self, request, **kwargs):
        """
        Render the program listing fragment.
        """
        user = request.user
        try:
            mobile_only = json.loads(request.GET.get('mobile_only', 'false'))
        except ValueError:
            mobile_only = False

        programs_config = kwargs.get('programs_config') or ProgramsApiConfig.current()
        if not programs_config.enabled or not user.is_authenticated:
            raise Http404

        meter = ProgramProgressMeter(request.site, user, mobile_only=mobile_only)

        context = {
            'marketing_url': get_program_marketing_url(programs_config, mobile_only),
            'programs': meter.engaged_programs,
            'progress': meter.progress()
        }
        html = render_to_string('learner_dashboard/programs_fragment.html', context)
        programs_fragment = Fragment(html)
        self.add_fragment_resource_urls(programs_fragment)

        return programs_fragment

    def standalone_page_title(self, request, fragment, **kwargs):
        """
        Return page title for the standalone page.
        """
        return _('Programs')


class ProgramDetailsFragmentView(EdxFragmentView):
    """
    Render the program details fragment.
    """
    DEFAULT_ROLE = 'student'

    @staticmethod
    def get_program_discussion_configuration(program_uuid):
        return ProgramDiscussionsConfiguration.objects.filter(
            program_uuid=program_uuid
        ).first()

    @staticmethod
    def _get_resource_link_id(program_uuid, request) -> str:
        site = get_current_site(request)
        return f'{site.domain}-{program_uuid}'

    @staticmethod
    def _get_result_sourcedid(context_id, resource_link_id, user_id) -> str:
        return f'{context_id}:{resource_link_id}:{user_id}'

    def _get_lti_embed_code(self, program_discussions_configuration, request) -> str:
        """
        Returns the LTI embed code for embedding in the program discussions tab
        Args:
            program_discussions_configuration (ProgramDiscussionsConfiguration): ProgramDiscussionsConfiguration object.
            request (HttpRequest): Request object for view in which LTI will be embedded.
        Returns:
            HTML code to embed LTI in program page.
        """
        program_uuid = program_discussions_configuration.program_uuid
        lti_consumer = program_discussions_configuration.lti_configuration.get_lti_consumer()
        user_id = str(request.user.id)
        context_id = program_uuid
        resource_link_id = self._get_resource_link_id(program_uuid, request)
        # TODO: Add support for multiple roles
        roles = self.DEFAULT_ROLE
        context_title = program_uuid
        result_sourcedid = self._get_result_sourcedid(context_id, resource_link_id, user_id)

        return lti_embed(
            html_element_id='lti-tab-launcher',
            lti_consumer=lti_consumer,
            resource_link_id=resource_link_id,
            user_id=user_id,
            roles=roles,
            context_id=context_id,
            context_title=context_title,
            context_label=context_id,
            result_sourcedid=result_sourcedid
        )

    def render_discussions_fragment(self, program_uuid, request) -> dict:
        """
        Returns the program discussion fragment if program discussions configuration exists for a program uuid
        """
        if program_discussions_is_enabled():
            program_discussions_configuration = self.get_program_discussion_configuration(program_uuid)
            if program_discussions_configuration:
                lti_embed_html = self._get_lti_embed_code(program_discussions_configuration, request)
                fragment = Fragment(
                    HTML(
                        """
                        <iframe
                            id='lti-tab-embed'
                            style='width: 100%; min-height: 800px; border: none'
                            srcdoc='{srcdoc}'
                         >
                        </iframe>
                        """
                    ).format(
                        srcdoc=lti_embed_html
                    )
                )
                return {
                    'iframe': fragment.content,
                    'enabled': True
                }
        return {
            'iframe': '',
            'enabled': False
        }

    def render_to_fragment(self, request, program_uuid, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """View details about a specific program."""
        programs_config = kwargs.get('programs_config') or ProgramsApiConfig.current()
        user = request.user
        if not programs_config.enabled or not request.user.is_authenticated:
            raise Http404

        meter = ProgramProgressMeter(request.site, user, uuid=program_uuid)
        program_data = meter.programs[0]

        if not program_data:
            raise Http404

        try:
            mobile_only = json.loads(request.GET.get('mobile_only', 'false'))
        except ValueError:
            mobile_only = False

        program_data = ProgramDataExtender(program_data, user, mobile_only=mobile_only).extend()
        course_data = meter.progress(programs=[program_data], count_only=False)[0]
        certificate_data = get_certificates(user, program_data)

        program_data.pop('courses')
        skus = program_data.get('skus')
        ecommerce_service = EcommerceService()

        # TODO: Don't have business logic of course-certificate==record-available here in LMS.
        # Eventually, the UI should ask Credentials if there is a record available and get a URL from it.
        # But this is here for now so that we can gate this URL behind both this business logic and
        # a waffle flag. This feature is in active developoment.
        program_record_url = get_credentials_records_url(program_uuid=program_uuid)
        if not certificate_data:
            program_record_url = None

        industry_pathways = []
        credit_pathways = []
        try:
            for pathway_id in program_data['pathway_ids']:
                pathway = get_pathways(request.site, pathway_id)
                if pathway and pathway['email']:
                    if pathway['pathway_type'] == PathwayType.CREDIT.value:
                        credit_pathways.append(pathway)
                    elif pathway['pathway_type'] == PathwayType.INDUSTRY.value:
                        industry_pathways.append(pathway)
        # if pathway caching did not complete fully (no pathway_ids)
        except KeyError:
            pass

        urls = {
            'program_listing_url': reverse('program_listing_view'),
            'track_selection_url': strip_course_id(
                reverse('course_modes_choose', kwargs={'course_id': FAKE_COURSE_KEY})
            ),
            'commerce_api_url': reverse('commerce_api:v0:baskets:create'),
            'buy_button_url': ecommerce_service.get_checkout_page_url(*skus),
            'program_record_url': program_record_url,
        }

        context = {
            'urls': urls,
            'user_preferences': get_user_preferences(user),
            'program_data': program_data,
            'course_data': course_data,
            'certificate_data': certificate_data,
            'industry_pathways': industry_pathways,
            'credit_pathways': credit_pathways,
            'program_discussions_enabled': program_discussions_is_enabled(),
            'discussion_fragment': self.render_discussions_fragment(program_uuid, request)
        }

        html = render_to_string('learner_dashboard/program_details_fragment.html', context)
        program_details_fragment = Fragment(html)
        self.add_fragment_resource_urls(program_details_fragment)
        return program_details_fragment

    def standalone_page_title(self, request, fragment, **kwargs):
        """
        Return page title for the standalone page.
        """
        return _('Program Details')
