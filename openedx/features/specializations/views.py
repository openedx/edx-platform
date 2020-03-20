from datetime import datetime

from opaque_keys.edx.keys import CourseKey

from common.lib.discovery_client.client import DiscoveryClient
from edxmako.shortcuts import render_to_response
from student.models import CourseEnrollment

from .helpers import date_from_str


def list_specializations(request):
    context = DiscoveryClient().active_programs()
    return render_to_response('features/specializations/list.html', context)


def specialization_about(request, specialization_uuid):
    context = DiscoveryClient().get_program(specialization_uuid)

    courses = []

    for course in [c for c in context.get('courses') if c['course_runs']]:
        course_open_rerun_list = [
            rerun for rerun in course['course_runs']
            if date_from_str(rerun['enrollment_start']) <= datetime.now() <= date_from_str(rerun['enrollment_end'])
        ]

        opened = bool(course_open_rerun_list)
        course_rerun = (sorted(course_open_rerun_list, key=lambda i: date_from_str(i['enrollment_start']))[0]
                        if opened else course['course_runs'][0])
        course_rerun['opened'] = opened
        course_rerun['enrolled'] = CourseEnrollment.is_enrolled(request.user, CourseKey.from_string(course_rerun['key']))

        courses.append(course_rerun)

    context.update({'courses': courses})

    return render_to_response('features/specializations/about.html', context)
