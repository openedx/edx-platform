"""Program marketing views"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_GET
from edxmako.shortcuts import render_to_response

from openedx.core.djangoapps.credentials.utils import get_programs_credentials
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs import utils


@require_GET
def explore_programs(request):
    """Explore programs by MKTG_URLS."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.show_program_listing:
        raise Http404

    if not request.user.is_authenticated():
        user, _ = User.objects.get_or_create(
            username='programs_dummy_user_for_api'
        )
    else:
        user = request.user

    meter = utils.ProgramProgressMeter(user)
    programs = meter.programs

    programs_dummy_user_for_api_meter_progress = []

    for program in programs:
        program['detail_url'] = reverse(
            'program_details_view',
            kwargs={'program_id': program['id']}
        )
        if user.username == 'programs_dummy_user_for_api':
            programs_dummy_user_for_api_meter_progress.append(
                {
                    'completed': [],
                    'in_progress': [],
                    'id': program['id'],
                    'not_started': []
                }
            )
    if user.username == 'programs_dummy_user_for_api':
        current_xseries_page_meter = programs_dummy_user_for_api_meter_progress
    else:
        current_xseries_page_meter = meter.progress
    context = {
        'programs': programs,
        'progress': current_xseries_page_meter,
        'xseries_url': utils.get_program_marketing_url(programs_config),
        'nav_hidden': True,
        'show_program_listing': programs_config.show_program_listing,
        'credentials': get_programs_credentials(request.user),
        'disable_courseware_js': True,
        'uses_pattern_library': True
    }

    return render_to_response('program_marketing/explore_programs.html', context)
