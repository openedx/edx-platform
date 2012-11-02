import logging
from certificates.models import GeneratedCertificate
from certificates.models import CertificateStatuses as status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

logger = logging.getLogger(__name__)


@csrf_exempt
def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.

    See models.py for a state diagram of certificate states

    This view should only ever be accessed by the xqueue server
    """

    if request.method == "POST":

        xqueue_body = json.loads(request.POST.get('xqueue_body'))
        xqueue_header = json.loads(request.POST.get('xqueue_header'))

        try:
            cert = GeneratedCertificate.objects.get(
                   user__username=xqueue_body['username'],
                   course_id=xqueue_body['course_id'],
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
        else:
            if cert.state in [status.generating, status.regenerating]:
                cert.download_uuid = xqueue_body['download_uuid']
                cert.verify_uuid = xqueue_body['verify_uuid']
                cert.download_url = xqueue_body['url']
                cert.status = status.downloadable
            elif cert.state in [status.deleting]:
                cert.status = status.deleted
            else:
                logger.critical('Invalid state for cert update: {0}'.format(
                    cert.state))
                return HttpResponse(json.dumps({
                            'return_code': 1,
                            'content': 'invalid cert state'}),
                             mimetype='application/json')
        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),
                             mimetype='application/json')
