"""URL handlers related to certificate handling by LMS"""

from dogapi import dog_stats_api
import json
import logging

from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from capa.xqueue_interface import XQUEUE_METRIC_NAME
from student.models import UserProfile
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from certificates.models import certificate_status_for_student, CertificateStatuses, GeneratedCertificate
from certificates.queue import XQueueCertInterface

use_cme = settings.FEATURES.get('USE_CME_REGISTRATION', False)
if use_cme:
    from cme_registration.models import CmeUserProfile


logger = logging.getLogger(__name__)


@csrf_exempt
def request_certificate(request):
    """Request the on-demand creation of a certificate for some user, course.

    A request doesn't imply a guarantee that such a creation will take place.
    We intentionally use the same machinery as is used for doing certification
    at the end of a course run, so that we can be sure users get graded and
    then if and only if they pass, do they get a certificate issued.
    """
    # Memoize user information; return error if it's invalid
    user = None
    username = ''
    try:
        user = request.user
        username = user.username
    except AttributeError:
        return HttpResponse(json.dumps({'add_status': 'error', 'error': 'ERRORBADREQUEST'}), mimetype='application/json')

    # It is an error to hit this endpoint with anything but a POST
    if request.method != "POST":
        return HttpResponse(json.dumps({'add_status': 'error', 'error': 'ERRORNOPOST'}), mimetype='application/json')

    # It is an error to hit this endpoint as an anonymous/nonregistered user
    if not (user.is_authenticated() and UserProfile.has_registered(user)):
        return HttpResponse(json.dumps({'add_status': 'error', 'error': 'ERRORANONYMOUSUSER'}), mimetype='application/json')

    xq = XQueueCertInterface()
    student = User.objects.get(username=username)
    course_key = SlashSeparatedCourseKey.from_deprecated_string(request.POST.get('course_id'))
    course = modulestore().get_course(course_key, depth=2)
    title = 'None'
    if use_cme:
        titlelist = CmeUserProfile.objects.filter(user=student).values('professional_designation')
        if len(titlelist):
            title = titlelist[0]['professional_designation']

    status = certificate_status_for_student(student, course_key)['status']
    if status in [CertificateStatuses.unavailable, CertificateStatuses.notpassing, CertificateStatuses.error]:
        logger.info('Grading and certification requested for user {} in course {} via /request_certificate call'.format(username, course_key))
        status = xq.add_cert(student, course_key, course=course, title=title)
    return HttpResponse(json.dumps({'add_status': status, 'error': ''}), mimetype='application/json')


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
            course_key = SlashSeparatedCourseKey.from_deprecated_string(xqueue_body['course_id'])

            cert = GeneratedCertificate.objects.get(
                user__username=xqueue_body['username'],
                course_id=course_key,
                key=xqueue_header['lms_key'])

        except GeneratedCertificate.DoesNotExist:
            logger.critical('Unable to lookup certificate\n'
                            'xqueue_body: {0}\n'
                            'xqueue_header: {1}'.format(
                                xqueue_body, xqueue_header))

            return HttpResponse(json.dumps({
                'return_code': 1,
                'content': 'unable to lookup key'}),
                mimetype='application/json')

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
            if cert.status in [status.generating, status.regenerating]:
                cert.download_uuid = xqueue_body['download_uuid']
                cert.verify_uuid = xqueue_body['verify_uuid']
                cert.download_url = xqueue_body['url']
                cert.status = status.downloadable
            elif cert.status in [status.deleting]:
                cert.status = status.deleted
            else:
                logger.critical('Invalid state for cert update: {0}'.format(
                    cert.status))
                return HttpResponse(json.dumps({
                            'return_code': 1,
                            'content': 'invalid cert status'}),
                             mimetype='application/json')

        dog_stats_api.increment(XQUEUE_METRIC_NAME, tags=[
            u'action:update_certificate',
            u'course_id:{}'.format(cert.course_id)
        ])

        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),
                            mimetype='application/json')
