import logging

import json
from django.http import HttpResponse
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.conf import settings
from django.contrib.auth.decorators import login_required

from openedx.core.djangoapps.labster.course.utils import LtiPassport

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore

from teacher_dashboard.utils import _send_request

log = logging.getLogger(__name__)


MIME_TYPES = {
    "csv": "text/csv",
    "json": "application/json"
}


@login_required
def dashboard_view(request, course_id):
    """
    Teacher dashboard renders data using backbone from /static/teacher_dashboard/js
    """
    # Course is needed for display others tabs
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key, depth=2)

    return render_to_response('teacher_dashboard/dashboard.html', {'course': course, 'course_id': course_id})


@login_required
def licenses_api_call(request):
    """
    Redirect Api call to Labster API
    """
    course_id = request.GET.get('course_id')
    if not course_id:
        response = []
    else:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        with modulestore().bulk_operations(course_key):
            course = get_course_by_id(course_key, depth=2)
        passports = course.lti_passports
        consumer_keys = [LtiPassport(passport_str).consumer_key for passport_str in passports]
        url = settings.LABSTER_ENDPOINTS.get("licenses")
        response = _send_request(
            url,
            method="POST",
            data=json.dumps({"consumer_keys": consumer_keys}),
        )
    return HttpResponse(response, content_type="application/json")


@login_required
def simulations_api_call(request, license_pk):
    url = settings.LABSTER_ENDPOINTS.get('simulations').format(license_pk)
    response = _send_request(url)
    return HttpResponse(response, content_type="application/json")


@login_required
def students_api_call(request, license_pk, simulation_pk):
    CONTENT_DESPOSITION_FORMATS = ('csv', )

    if request.GET.get("format") in MIME_TYPES:
        accept_format = request.GET.get("format")
    else:
        accept_format = "json"

    url = settings.LABSTER_ENDPOINTS.get('students').format(license_pk, simulation_pk)
    content = _send_request(url, headers={"accept": MIME_TYPES.get(accept_format)})
    response = HttpResponse(content, content_type=MIME_TYPES.get(accept_format))

    if request.GET.get("format") in CONTENT_DESPOSITION_FORMATS:
        response['Content-Disposition'] = 'attachment; filename="export_student_results.{}"'.format(
            request.GET.get("format")
        )

    return response
