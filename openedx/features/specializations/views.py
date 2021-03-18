"""
Helper views for specializations app
"""
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from common.lib.discovery_client.client import DiscoveryClient
from edxmako.shortcuts import render_to_response
from openedx.features.philu_courseware.models import CourseEnrollmentMeta
from student.models import CourseEnrollment
from student.views import change_enrollment

from .helpers import get_program_courses

log = logging.getLogger(__name__)


def list_specializations(request):  # pylint: disable=unused-argument
    """
    List all active specializations

    Args:
        request: HTTP request object

    Returns:
        HttpResponse
    """
    try:
        context = DiscoveryClient().active_programs()
    except ValidationError as exc:
        return HttpResponseBadRequest(exc.message)
    return render_to_response('features/specializations/list.html', context)


def specialization_about(request, specialization_uuid):
    """
    Show specialization about page

    Args:
        request: HTTP request object
        specialization_uuid: uuid of specialization

    Returns:
        HttpResponse
    """
    user = request.user
    context, courses = get_program_courses(user, specialization_uuid, detail=True)
    is_enrolled_in_all = bool(courses)
    is_all_linked = bool(courses)

    for course in courses:
        is_enrolled_in_all = is_enrolled_in_all and course.get('enrolled')

        if not is_enrolled_in_all or course.get('completed'):
            continue

        is_all_linked = is_all_linked and CourseEnrollmentMeta.objects.filter(
            course_enrollment__course_id=course['course_id'], program_uuid=specialization_uuid
        ).exists()

    context.update({'show_course_status': is_enrolled_in_all and is_all_linked})

    return render_to_response('features/specializations/about.html', context)


@transaction.non_atomic_requests
@login_required
@require_POST
def enroll_in_all_specialisation_courses(request, specialization_uuid):
    """
    Enroll user in all courses of a program. For each enrollment, establish linkages except
    for courses which are already complete

    Args:
        request: HTTP request object
        specialization_uuid: uuid of specialization

    Returns:
        Http response object with status code 200, if all course are enrolled and links are
        established otherwise exception is raised by core edx function

    """
    user = request.user
    _, courses = get_program_courses(user, specialization_uuid, detail=True)

    for course in courses:

        if not course['enrolled']:
            # Modifying request object as a last resort, to avoid network call
            modified_request = request.POST.copy()
            modified_request['course_id'] = course['key']
            modified_request['enrollment_action'] = 'enroll'
            request.POST = modified_request
            response = change_enrollment(request)
            log.info("Course {} enrollment request ended with status {}".format(course['key'], response.status_code))

        if not course['completed']:
            course_id = course['course_id']
            enrollment = CourseEnrollment.get_enrollment(user, course_key=course_id)

            if enrollment.is_enrolled(user, course_id):
                CourseEnrollmentMeta.objects.get_or_create(
                    course_enrollment=enrollment, program_uuid=specialization_uuid
                )

    return HttpResponse(status=200)
