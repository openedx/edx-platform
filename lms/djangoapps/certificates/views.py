import logging
from certificates.models import GeneratedCertificate
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

log = logging.getLogger("mitx.certificates")

@csrf_exempt
def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.
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
            log.critical('Unable to lookup certificate\n' 
                         'xqueue_body: {0}\n'
                         'xqueue_header: {1}'.format(
                                      xqueue_body, xqueue_header))

            return HttpResponse(json.dumps({
                            'return_code': 1,
                            'content': 'unable to lookup key'}),
                             mimetype='application/json')

        cert.download_uuid = xqueue_body['download_uuid']
        cert.verify_uuid = xqueue_body['download_uuid']
        cert.download_url = xqueue_body['url']
        cert.status = 'downloadable'
        cert.save()
        return HttpResponse(json.dumps({'return_code': 0}),
                             mimetype='application/json')


