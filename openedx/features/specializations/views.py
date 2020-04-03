from datetime import datetime

from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from opaque_keys.edx.keys import CourseKey

from common.lib.discovery_client.client import DiscoveryClient
from edxmako.shortcuts import render_to_response
from student.models import CourseEnrollment

from .helpers import date_from_str


def list_specializations(request):
    try:
        context = DiscoveryClient().active_programs()
    except ValidationError as exc:
        return HttpResponseBadRequest(exc.message)
    return render_to_response('features/specializations/list.html', context)


def specialization_about(request, specialization_uuid):
    try:
        context = DiscoveryClient().get_program(specialization_uuid)
    except ValidationError as exc:
        return HttpResponseBadRequest(exc.message)

    courses = []
    for course in [course for course in context['courses'] if course['course_runs']]:
        course_open_rerun_list = [
            rerun for rerun in course['course_runs']
            if rerun['enrollment_start'] and rerun['enrollment_end'] and
            date_from_str(rerun['enrollment_start']) <= datetime.now() <= date_from_str(rerun['enrollment_end'])
        ]

        opened = bool(course_open_rerun_list)
        course_rerun = (sorted(course_open_rerun_list,
                        key=lambda open_rerun: date_from_str(open_rerun['enrollment_start']))[0]
                        if opened else course['course_runs'][0])
        course_rerun['opened'] = opened
        course_rerun['enrolled'] = CourseEnrollment.is_enrolled(request.user,
                                                                CourseKey.from_string(course_rerun['key']))

        courses.append(course_rerun)

    context.update({'courses': courses})

    return render_to_response('features/specializations/about.html', context)
