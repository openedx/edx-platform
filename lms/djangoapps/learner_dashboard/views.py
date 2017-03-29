"""Learner dashboard views"""
import waffle
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response
from lms.djangoapps.learner_dashboard.utils import strip_course_id, FAKE_COURSE_KEY
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.credentials.utils import get_programs_credentials
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    get_program_marketing_url,
    ProgramProgressMeter,
    ProgramDataExtender,
    get_certificates,
)
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences


@login_required
@require_GET
def program_listing(request):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.enabled:
        raise Http404

    meter = ProgramProgressMeter(request.user)

    context = {
        'credentials': get_programs_credentials(request.user),
        'disable_courseware_js': True,
        'marketing_url': get_program_marketing_url(programs_config),
        'nav_hidden': True,
        'programs': meter.engaged_programs,
        'progress': meter.progress(),
        'show_program_listing': programs_config.enabled,
        'uses_pattern_library': True,
    }

    return render_to_response('learner_dashboard/programs.html', context)


@login_required
@require_GET
def program_details(request, program_uuid):
    """View details about a specific program."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.enabled:
        raise Http404

    meter = ProgramProgressMeter(request.user, uuid=program_uuid)
    program_data = meter.programs[0]

    if not program_data:
        raise Http404

    program_data = ProgramDataExtender(program_data, request.user).extend()

    urls = {
        'program_listing_url': reverse('program_listing_view'),
        'track_selection_url': strip_course_id(
            reverse('course_modes_choose', kwargs={'course_id': FAKE_COURSE_KEY})
        ),
        'commerce_api_url': reverse('commerce_api:v0:baskets:create'),
    }

    context = {
        'urls': urls,
        'show_program_listing': programs_config.enabled,
        'nav_hidden': True,
        'disable_courseware_js': True,
        'uses_pattern_library': True,
        'user_preferences': get_user_preferences(request.user)
    }

    if waffle.switch_is_active('new_program_progress'):
        course_data = meter.progress(programs=[program_data], count_only=False)[0]
        certificate_data = get_certificates(request.user, program_data)

        program_data.pop('courses')

        context.update({
            'program_data': program_data,
            'course_data': course_data,
            'certificate_data': certificate_data,
        })

        return render_to_response('learner_dashboard/program_details_2017.html', context)
    else:
        context.update({'program_data': program_data})

        return render_to_response('learner_dashboard/program_details.html', context)
