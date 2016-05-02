"""New learner dashboard views."""
from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import Http404

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter, get_display_category
from student.views import get_course_enrollments, _get_xseries_credentials


@login_required
@require_GET
def view_programs(request):
    """View programs in which the user is engaged."""
    show_program_listing = ProgramsApiConfig.current().show_program_listing
    if not show_program_listing:
        raise Http404

    enrollments = list(get_course_enrollments(request.user, None, []))
    meter = ProgramProgressMeter(request.user, enrollments)
    programs = meter.engaged_programs

    # TODO: Pull 'xseries' string from configuration model.
    marketing_root = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries').strip('/')
    for program in programs:
        program['display_category'] = get_display_category(program)
        program['marketing_url'] = '{root}/{slug}'.format(
            root=marketing_root,
            slug=program['marketing_slug']
        )

    return render_to_response('learner_dashboard/programs.html', {
        'programs': programs,
        'progress': meter.progress,
        'xseries_url': marketing_root if ProgramsApiConfig.current().show_xseries_ad else None,
        'nav_hidden': True,
        'show_program_listing': show_program_listing,
        'credentials': _get_xseries_credentials(request.user)
    })
