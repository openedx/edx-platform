"""
Views used by XQueue certificate generation.
"""


import json
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.util.json_request import JsonResponse, JsonResponseBadRequest
from lms.djangoapps.certificates.api import (
    can_generate_certificate_task,
    generate_certificate_task,
    generate_user_certificates
)
from lms.djangoapps.certificates.models import (
    CertificateStatuses,
    ExampleCertificate,
    GeneratedCertificate,
    certificate_status_for_student
)
from xmodule.modulestore.django import modulestore

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
            course = modulestore().get_course(course_key, depth=2)

            status = certificate_status_for_student(student, course_key)['status']
            if can_generate_certificate_task(student, course_key):
                log.info(f'{course_key} is using V2 course certificates. Attempt will be made to generate a V2 '
                         f'certificate for user {student.id}.')
                generate_certificate_task(student, course_key)
            elif status in [CertificateStatuses.unavailable, CertificateStatuses.notpassing, CertificateStatuses.error]:
                log_msg = 'Grading and certification requested for user %s in course %s via /request_certificate call'
                log.info(log_msg, username, course_key)
                status = generate_user_certificates(student, course_key, course=course)
            return HttpResponse(json.dumps({'add_status': status}), content_type='application/json')  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
        return HttpResponse(json.dumps({'add_status': 'ERRORANONYMOUSUSER'}), content_type='application/json')  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps


@csrf_exempt
def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.

    This view should only ever be accessed by the xqueue server
    """

    status = CertificateStatuses
    if request.method == "POST":

        xqueue_body = json.loads(request.POST.get('xqueue_body'))
        xqueue_header = json.loads(request.POST.get('xqueue_header'))

        try:
            course_key = CourseKey.from_string(xqueue_body['course_id'])

            cert = GeneratedCertificate.eligible_certificates.get(
                user__username=xqueue_body['username'],
                course_id=course_key,
                key=xqueue_header['lms_key'])

        except GeneratedCertificate.DoesNotExist:
            log.critical(
                'Unable to lookup certificate\n'
                'xqueue_body: %s\n'
                'xqueue_header: %s',
                xqueue_body,
                xqueue_header
            )

            return HttpResponse(json.dumps({  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
                'return_code': 1,
                'content': 'unable to lookup key'
            }), content_type='application/json')

        user = cert.user
        if can_generate_certificate_task(user, course_key):
            log.warning(f'{course_key} is using V2 certificates. Request to update the certificate for user {user.id} '
                        f'will be ignored.')
            return HttpResponse(  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
                json.dumps({
                    'return_code': 1,
                    'content': 'allowlist certificate'
                }),
                content_type='application/json'
            )

        if 'error' in xqueue_body:
            cert.status = status.error
            if 'error_reason' in xqueue_body:

                # Hopefully we will record a meaningful error
                # here if something bad happened during the
                # certificate generation process
                #
                # example:
                #  (aamorm BerkeleyX/CS169.1x/2012_Fall)
                #  <class 'simples3.bucket.S3Error'>:
                #  HTTP error (reason=error(32, 'Broken pipe'), filename=None) :
                #  certificate_agent.py:175

                cert.error_reason = xqueue_body['error_reason']
        else:
            if cert.status == status.generating:
                cert.download_uuid = xqueue_body['download_uuid']
                cert.verify_uuid = xqueue_body['verify_uuid']
                cert.download_url = xqueue_body['url']
                cert.status = status.downloadable
            elif cert.status in [status.deleting]:
                cert.status = status.deleted
            else:
                log.critical(
                    'Invalid state for cert update: %s', cert.status
                )
                return HttpResponse(  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
                    json.dumps({
                        'return_code': 1,
                        'content': 'invalid cert status'
                    }),
                    content_type='application/json'
                )

        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),  # pylint: disable=http-response-with-content-type-json, http-response-with-json-dumps
                            content_type='application/json')
