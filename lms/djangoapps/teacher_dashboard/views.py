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
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.defaultfilters import slugify

from openedx.core.djangoapps.labster.course.utils import LtiPassport

from lms.djangoapps.ccx.utils import get_ccx_from_ccx_locator
from lms.djangoapps.ccx.overrides import get_override_for_ccx

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore

from teacher_dashboard.utils import _send_request, has_teacher_access


log = logging.getLogger(__name__)


@login_required
def dashboard_view(request, course_id):
    """
    Teacher dashboard page.
    """
    # Course is needed for display others tabs
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key)

    return render_to_response('teacher_dashboard/dashboard.html', {'course': course, 'course_id': course_id})


@login_required
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def teacher_dahsboard_handler(request, course_id):
    """
    Returns data for the appropriate request type.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key)

    if not has_teacher_access(request.user, course):
        raise PermissionDenied()

    if request.method == "POST":
        params = request.POST.copy()
    else:
        params = request.GET.copy()

    req_type = params.get('type')
    license_pk = params.get('license')
    simulation_pk = params.get('simulation')

    if req_type == 'licenses':
        return license_api_call(course)
    elif req_type == 'simulations':
        return simulations_api_call(license_pk)
    elif req_type == 'students':
        return students_api_call(license_pk, simulation_pk)
    elif req_type == 'attempts':
        return attempts_api_call(course_id, license_pk, simulation_pk)

    return HttpResponseBadRequest()


def license_api_call(course):
    """
    Retrieves licenses from API.
    """
    # CCX overrides doesn't work outside of Courseware, so we have to get them via
    # get_override_for_ccx.
    # Next 3 lines work well with both: ccx and simple courses.
    ccx = get_ccx_from_ccx_locator(course.id)
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
