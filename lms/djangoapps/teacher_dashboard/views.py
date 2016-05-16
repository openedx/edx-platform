"""
Views.
"""
import logging

import json
from django.http import HttpResponse, HttpResponseBadRequest
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.defaultfilters import slugify
from django.shortcuts import redirect

from openedx.core.djangoapps.labster.course.utils import LtiPassport

from lms.djangoapps.ccx.utils import get_ccx_from_ccx_locator
from lms.djangoapps.ccx.views import coach_dashboard, get_ccx_for_coach
from lms.djangoapps.ccx.overrides import get_override_for_ccx

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore

from teacher_dashboard.utils import _send_request, has_teacher_access
from ccx_keys.locator import CCXLocator


log = logging.getLogger(__name__)


@login_required
@coach_dashboard
def dashboard_view(request, course, ccx=None):
    """
    Teacher dashboard page.
    """
    # right now, we can only have one ccx per user and course
    # so, if no ccx is passed in, we can safely redirect to that
    if ccx is None:
        ccx = get_ccx_for_coach(course, request.user)
        if ccx:
            url = reverse(
                'dashboard_view_handler',
                kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)}
            )
            # We need this redirect to get a course with CCX fields overrides applied.
            return redirect(url)

    return render_to_response('teacher_dashboard/dashboard.html', {
        'course': course,
        'course_id': CCXLocator.from_course_locator(course.id, ccx.id)
    })


@login_required
@coach_dashboard
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def teacher_dahsboard_handler(request, course, ccx=None):
    """
    Returns data for the appropriate request type.
    """
    if request.method == "POST":
        params = request.POST.copy()
    else:
        params = request.GET.copy()

    req_type = params.get('type')
    license_pk = params.get('license')
    simulation_pk = params.get('simulation')

    if req_type == 'licenses':
        return license_api_call(course, ccx)
    elif req_type == 'simulations':
        return simulations_api_call(license_pk)
    elif req_type == 'students':
        return students_api_call(license_pk, simulation_pk)
    elif req_type == 'attempts':
        return attempts_api_call(unicode(course.id), license_pk, simulation_pk)

    return HttpResponseBadRequest()


def license_api_call(course, ccx=None):
    """
    Retrieves licenses from API.
    """
    # CCX overrides doesn't work outside of Courseware, so we have to get them via
    # get_override_for_ccx.
    passports = get_override_for_ccx(ccx, course, 'lti_passports', course.lti_passports)[:]
    consumer_keys = [LtiPassport(passport_str).consumer_key for passport_str in passports]

    url = settings.LABSTER_ENDPOINTS.get("licenses")
    response = _send_request(
        url,
        method="POST",
        data=json.dumps({"consumer_keys": consumer_keys}),
    )

    return HttpResponse(response, content_type="application/json")


def simulations_api_call(license_pk):
    """
    Retrieves simulations from API.
    """
    url = settings.LABSTER_ENDPOINTS.get('simulations').format(license_pk)
    response = _send_request(url)
    return HttpResponse(response, content_type="application/json")


def students_api_call(license_pk, simulation_pk):
    """
    Retrieves students from API.
    """
    url = settings.LABSTER_ENDPOINTS.get('students').format(license_pk, simulation_pk)
    content = _send_request(url)
    return HttpResponse(content, content_type="application/json")


def attempts_api_call(course_id, license_pk, simulation_pk):
    """
    Retrieves CSV export from API.
    """
    url = settings.LABSTER_ENDPOINTS.get('attempts').format(license_pk, simulation_pk)
    content = _send_request(url, headers={"accept": "text/csv"})
    response = HttpResponse(content, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{0}-summary.csv"'.format(
        slugify(course_id)
    )
    return response
