"""Learner dashboard views"""
from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response
from lms.djangoapps.learner_dashboard.utils import strip_course_id, FAKE_COURSE_KEY
from openedx.core.djangoapps.credentials.utils import get_programs_credentials
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs import utils


@login_required
@require_GET
def program_listing(request):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.show_program_listing:
        raise Http404

    meter = utils.ProgramProgressMeter(request.user)
    programs = meter.engaged_programs

    marketing_url = urljoin(settings.MKTG_URLS.get('ROOT'), programs_config.marketing_path).rstrip('/')

    for program in programs:
        program['detail_url'] = utils.get_program_detail_url(program, marketing_url)

    context = {
        'credentials': get_programs_credentials(request.user),
        'disable_courseware_js': True,
        'marketing_url': marketing_url,
        'nav_hidden': True,
        'programs': programs,
        'progress': meter.progress,
        'show_program_listing': programs_config.show_program_listing,
        'uses_pattern_library': False,
    }

    return render_to_response('learner_dashboard/programs.html', context)


@login_required
@require_GET
def program_details(request, program_id):
    """View details about a specific program."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.show_program_details:
        raise Http404

    program_data = utils.get_programs(request.user, program_id=program_id)

    if not program_data:
        raise Http404

    program_data = utils.ProgramDataExtender(program_data, request.user).extend()

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
        'show_program_listing': programs_config.show_program_listing,
        'nav_hidden': True,
        'disable_courseware_js': True,
        'uses_pattern_library': False
    }

    return render_to_response('learner_dashboard/program_details.html', context)
