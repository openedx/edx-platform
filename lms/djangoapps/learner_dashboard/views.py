"""Learner dashboard views"""
import uuid

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response
from lms.djangoapps.learner_dashboard.utils import strip_course_id, FAKE_COURSE_KEY
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.utils import get_programs as get_catalog_programs, munge_catalog_program
from openedx.core.djangoapps.credentials.utils import get_programs_credentials
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs import utils
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences


@login_required
@require_GET
def program_listing(request):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.show_program_listing:
        raise Http404

    meter = utils.ProgramProgressMeter(request.user)

    context = {
        'credentials': get_programs_credentials(request.user),
        'disable_courseware_js': True,
        'marketing_url': utils.get_program_marketing_url(programs_config),
        'nav_hidden': True,
        'programs': meter.engaged_programs(),
        'progress': meter.progress,
        'show_program_listing': programs_config.show_program_listing,
        'uses_pattern_library': True,
    }

    return render_to_response('learner_dashboard/programs.html', context)


@login_required
@require_GET
def program_details(request, program_uuid):
    """View details about a specific program."""

    programs_config = ProgramsApiConfig.current()
    if not programs_config.show_program_details or not CatalogIntegration.is_enabled():
        raise Http404

    program_data = get_catalog_programs(request.user, uuid=program_uuid)
    if program_data:
        # TODO Get rid of this. Always use the Catalog API's format.
        program_data = munge_catalog_program(program_data)

    if not program_data:
        raise Http404

    urls = {
        'program_listing_url': reverse('program_listing_view'),
        'track_selection_url': strip_course_id(
            reverse('course_modes_choose', kwargs={'course_id': FAKE_COURSE_KEY})
        ),
        'commerce_api_url': reverse('commerce_api:v0:baskets:create'),
    }

    context = {
        'program_data': program_data,
        'urls': urls,
        # TODO Can we get rid of these?
        'show_program_listing': programs_config.show_program_listing,
        'nav_hidden': True,
        'disable_courseware_js': True,
        'uses_pattern_library': True,
        'user_preferences': get_user_preferences(request.user)
    }

    return render_to_response('learner_dashboard/program_details.html', context)
