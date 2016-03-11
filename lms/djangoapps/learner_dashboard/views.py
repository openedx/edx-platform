"""
Handles requests for views, returning page frame
"""

import logging
from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import Http404

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.utils import get_user_enrolled_programs
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from student.views import get_course_enrollments


log = logging.getLogger(__name__)


def _get_xseries_url():
    '''Create the xseries advertising link url'''
    xseries_url = None
    if ProgramsApiConfig.current().show_xseries_ad:
        xseries_url = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries')
    return xseries_url


@login_required
@require_GET
def view_programs(request):
    '''
    This is the view to see all the programs the learner has been enrolled in
    '''
    if not ProgramsApiConfig.current().is_student_dashboard_enabled:
        raise Http404("learner dashboard not enabled")

    course_enrollments = list(get_course_enrollments(request.user, None, []))

    programs = get_user_enrolled_programs(
        request.user,
        [enrollment.course_id for enrollment in course_enrollments]
    )

    return render_to_response('learner_dashboard/programs.html', {
        'programs': programs,
        'xseries_url': _get_xseries_url()
    })
