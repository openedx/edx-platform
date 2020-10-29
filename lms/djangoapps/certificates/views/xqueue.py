"""
Views used by XQueue certificate generation.
"""


import json
import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import CourseKey

from capa.xqueue_interface import XQUEUE_METRIC_NAME
from lms.djangoapps.certificates.api import generate_user_certificates
from lms.djangoapps.certificates.models import (
    CertificateStatuses,
    ExampleCertificate,
    GeneratedCertificate,
    certificate_status_for_student
)
from common.djangoapps.util.json_request import JsonResponse, JsonResponseBadRequest
from common.djangoapps.util.request_rate_limiter import BadRequestRateLimiter
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


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
            if status in [CertificateStatuses.unavailable, CertificateStatuses.notpassing, CertificateStatuses.error]:
                log_msg = u'Grading and certification requested for user %s in course %s via /request_certificate call'
                log.info(log_msg, username, course_key)
                status = generate_user_certificates(student, course_key, course=course)
            return HttpResponse(json.dumps({'add_status': status}), content_type='application/json')
        return HttpResponse(json.dumps({'add_status': 'ERRORANONYMOUSUSER'}), content_type='application/json')


@csrf_exempt
def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.

    See models.py for a state diagram of certificate states

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
                u'xqueue_body: %s\n'
                u'xqueue_header: %s',
                xqueue_body,
                xqueue_header
            )

            return HttpResponse(json.dumps({
                'return_code': 1,
                'content': 'unable to lookup key'
            }), content_type='application/json')

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
                    u'Invalid state for cert update: %s', cert.status
                )
                return HttpResponse(
                    json.dumps({
                        'return_code': 1,
                        'content': 'invalid cert status'
                    }),
                    content_type='application/json'
                )

        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),
                            content_type='application/json')


@csrf_exempt
@require_POST
def update_example_certificate(request):
    """Callback from the XQueue that updates example certificates.

    Example certificates are used to verify that certificate
    generation is configured correctly for a course.

    Unlike other certificates, example certificates
    are not associated with a particular user or displayed
    to students.

    For this reason, we need a different end-point to update
    the status of generated example certificates.

    Arguments:
        request (HttpRequest)

    Returns:
        HttpResponse (200): Status was updated successfully.
        HttpResponse (400): Invalid parameters.
        HttpResponse (403): Rate limit exceeded for bad requests.
        HttpResponse (404): Invalid certificate identifier or access key.

    """
    log.info(u"Received response for example certificate from XQueue.")

    rate_limiter = BadRequestRateLimiter()

    # Check the parameters and rate limits
    # If these are invalid, return an error response.
    if rate_limiter.is_rate_limit_exceeded(request):
        log.info(u"Bad request rate limit exceeded for update example certificate end-point.")
        return HttpResponseForbidden("Rate limit exceeded")

    if 'xqueue_body' not in request.POST:
        log.info(u"Missing parameter 'xqueue_body' for update example certificate end-point")
        rate_limiter.tick_request_counter(request)
        return JsonResponseBadRequest("Parameter 'xqueue_body' is required.")

    if 'xqueue_header' not in request.POST:
        log.info(u"Missing parameter 'xqueue_header' for update example certificate end-point")
        rate_limiter.tick_request_counter(request)
        return JsonResponseBadRequest("Parameter 'xqueue_header' is required.")

    try:
        xqueue_body = json.loads(request.POST['xqueue_body'])
        xqueue_header = json.loads(request.POST['xqueue_header'])
    except (ValueError, TypeError):
        log.info(u"Could not decode params to example certificate end-point as JSON.")
        rate_limiter.tick_request_counter(request)
        return JsonResponseBadRequest("Parameters must be JSON-serialized.")

    # Attempt to retrieve the example certificate record
    # so we can update the status.
    try:
        uuid = xqueue_body.get('username')
        access_key = xqueue_header.get('lms_key')
        cert = ExampleCertificate.objects.get(uuid=uuid, access_key=access_key)
    except ExampleCertificate.DoesNotExist:
        # If we are unable to retrieve the record, it means the uuid or access key
        # were not valid.  This most likely means that the request is NOT coming
        # from the XQueue.  Return a 404 and increase the bad request counter
        # to protect against a DDOS attack.
        log.info(u"Could not find example certificate with uuid '%s' and access key '%s'", uuid, access_key)
        rate_limiter.tick_request_counter(request)
        raise Http404

    if 'error' in xqueue_body:
        # If an error occurs, save the error message so we can fix the issue.
        error_reason = xqueue_body.get('error_reason')
        cert.update_status(ExampleCertificate.STATUS_ERROR, error_reason=error_reason)
        log.warning(
            (
                u"Error occurred during example certificate generation for uuid '%s'.  "
                u"The error response was '%s'."
            ), uuid, error_reason
        )
    else:
        # If the certificate generated successfully, save the download URL
        # so we can display the example certificate.
        download_url = xqueue_body.get('url')
        if download_url is None:
            rate_limiter.tick_request_counter(request)
            log.warning(u"No download URL provided for example certificate with uuid '%s'.", uuid)
            return JsonResponseBadRequest(
                "Parameter 'download_url' is required for successfully generated certificates."
            )
        else:
            cert.update_status(ExampleCertificate.STATUS_SUCCESS, download_url=download_url)
            log.info(u"Successfully updated example certificate with uuid '%s'.", uuid)

    # Let the XQueue know that we handled the response
    return JsonResponse({'return_code': 0})
