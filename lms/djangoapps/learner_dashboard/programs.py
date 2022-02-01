"""
Fragments for rendering programs.
"""

import json
from abc import ABC, abstractmethod
from urllib.parse import quote

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _  # lint-amnesty, pylint: disable=unused-import
from django.utils.translation import to_locale
from lti_consumer.lti_1p1.contrib.django import lti_embed
from web_fragments.fragment import Fragment

from common.djangoapps.student.models import anonymous_id_for_user
from common.djangoapps.student.roles import GlobalStaff
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.learner_dashboard.utils import FAKE_COURSE_KEY, program_tab_view_is_enabled, strip_course_id
from openedx.core.djangoapps.catalog.constants import PathwayType
from openedx.core.djangoapps.catalog.utils import get_pathways, get_programs
from openedx.core.djangoapps.credentials.utils import get_credentials_records_url
from openedx.core.djangoapps.discussions.models import ProgramDiscussionsConfiguration, ProgramLiveConfiguration
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

    @staticmethod
    def _get_resource_link_id(program_uuid, request) -> str:
        site = get_current_site(request)
        return f'{site.domain}-{program_uuid}'

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
        program_discussion_lti = ProgramDiscussionLTI(program_uuid, request)
        program_live_lti = ProgramLiveLTI(program_uuid, request)
        context = {
            'urls': urls,
            'user_preferences': get_user_preferences(user),
            'program_data': program_data,
            'course_data': course_data,
            'certificate_data': certificate_data,
            'industry_pathways': industry_pathways,
            'credit_pathways': credit_pathways,
            'program_tab_view_enabled': program_tab_view_is_enabled(),
            'discussion_fragment': {
                'configured': program_discussion_lti.is_configured,
                'iframe': program_discussion_lti.render_iframe()
            },
            'live_fragment': {
                'configured': program_live_lti.is_configured,
                'iframe': program_live_lti.render_iframe()
            }
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


class ProgramLTI(ABC):
    """
      Encapsulates methods for program LTI iframe rendering.
    """
    DEFAULT_ROLE = 'Student'
    ADMIN_ROLE = 'Administrator'

    def __init__(self, program_uuid, request):
        self.program_uuid = program_uuid
        self.program = get_programs(uuid=self.program_uuid)
        self.request = request
        self.configuration = self.get_configuration()

    @abstractmethod
    def get_configuration(self):
        return

    @property
    def is_configured(self):
        """
        Returns a boolean indicating if the program configuration is enabled or not.
        """
        return bool(self.configuration and self.configuration.enabled)

    def _get_resource_link_id(self) -> str:
        site = get_current_site(self.request)
        return f'{site.domain}-{self.program_uuid}'

    def _get_result_sourcedid(self, resource_link_id) -> str:
        return f'{self.program_uuid}:{resource_link_id}:{self.request.user.id}'

    def get_user_roles(self) -> str:
        """
        Returns comma-separated roles for the given user
        """
        basic_role = self.DEFAULT_ROLE

        if GlobalStaff().has_user(self.request.user):
            basic_role = self.ADMIN_ROLE

        all_roles = [basic_role]
        return ','.join(all_roles)

    def _get_additional_lti_parameters(self):
        lti_config = self.configuration.lti_configuration
        return lti_config.lti_config.get('additional_parameters', {})

    def _get_context_title(self) -> str:
        return "{} - {}".format(
            self.program.get('title', ''),
            self.program.get('subtitle', ''),
        )

    def _get_pii_lti_parameters(self, configuration, request):
        """
        Get LTI parameters that contain PII.

        Args:
            configuration (LtiConfiguration): LtiConfiguration object.
            request (HttpRequest): Request object for view in which LTI will be embedded.

        Returns:
            Dictionary with LTI parameters containing PII.
        """
        if configuration.version != configuration.LTI_1P1:
            return {}
        pii_config = {}
        if configuration.pii_share_username:
            pii_config['person_sourcedid'] = request.user.username
        if configuration.pii_share_email:
            pii_config['person_contact_email_primary'] = request.user.email
        return pii_config

    def _get_lti_embed_code(self) -> str:
        """
        Returns the LTI embed code for embedding in the program discussions tab
        Returns:
            HTML code to embed LTI in program page.
        """
        resource_link_id = self._get_resource_link_id()
        result_sourcedid = self._get_result_sourcedid(resource_link_id)
        pii_params = self._get_pii_lti_parameters(self.configuration.lti_configuration, self.request)
        additional_params = self._get_additional_lti_parameters()

        return lti_embed(
            html_element_id='lti-tab-launcher',
            lti_consumer=self.configuration.lti_configuration.get_lti_consumer(),
            resource_link_id=quote(resource_link_id),
            user_id=quote(anonymous_id_for_user(self.request.user, None)),
            roles=self.get_user_roles(),
            context_id=quote(self.program_uuid),
            context_title=self._get_context_title(),
            context_label=self.program_uuid,
            result_sourcedid=quote(result_sourcedid),
            locale=to_locale(get_language()),
            **pii_params,
            **additional_params
        )

    def render_iframe(self) -> str:
        """
        Returns the program LTI iframe if program Lti configuration exists for a program uuid
        """
        if not self.is_configured:
            return ''

        lti_embed_html = self._get_lti_embed_code()
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
        return fragment.content


class ProgramDiscussionLTI(ProgramLTI):
    def get_configuration(self):
        return ProgramDiscussionsConfiguration.get(self.program_uuid)


class ProgramLiveLTI(ProgramLTI):
    def get_configuration(self):
        return ProgramLiveConfiguration.get(self.program_uuid)
