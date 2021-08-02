"""
Views used by XQueue certificate generation.
"""


import json
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.api import generate_certificate_task
from lms.djangoapps.certificates.utils import certificate_status_for_student

log = logging.getLogger(__name__)
User = get_user_model()


# Grades can potentially be written - if so, let grading manage the transaction.
@transaction.non_atomic_requests
@csrf_exempt
def request_certificate(request):
    """Request the on-demand creation of a certificate for some user, course.

    A request doesn't imply a guarantee that such a creation will take place.
    We intentionally use the same machinery as is used for doing certification
    at the end of a course run, so that we can be sure users get graded and
    then if and only if they pass, do they get a certificate issued.
    """
    if request.method == "POST":
        if request.user.is_authenticated:
            username = request.user.username
            student = User.objects.get(username=username)
            course_key = CourseKey.from_string(request.POST.get('course_id'))
            status = certificate_status_for_student(student, course_key)['status']

            log.info(f'{course_key} is using V2 course certificates. Attempt will be made to generate a V2 certificate '
                     f'for user {student.id}.')
            generate_certificate_task(student, course_key)
            return HttpResponse(json.dumps({'add_status': status}), content_type='application/json')  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
        return HttpResponse(json.dumps({'add_status': 'ERRORANONYMOUSUSER'}), content_type='application/json')  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
