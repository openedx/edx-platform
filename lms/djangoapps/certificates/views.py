import logging
from certificates.models import GeneratedCertificate
from pprint import pprint

log = logging.getLogger("mitx.certificates")


def update_certificate(request):
    """
    Will update GeneratedCertificate for a new certificate or
    modify an existing certificate entry.
    """

    if request.method == "POST":
        pprint(request)
#        user = request.POST.get('user')
#        try:
#            generated_certificate = GeneratedCertificate.objects.get(
#                   key=key)
#        except GeneratedCertificate.DoesNotExist:
#            generated_certificate = GeneratedCertificate(user=user)
#
#        enabled = request.POST.get('enabled')
#        enabled = True if enabled == 'True' else False
#        generated_certificate.grade = request.POST.get('grade')
#        generated_certificate.download_url = request.POST.get('download_url')
#        generated_certificate.graded_download_url = request.POST.get(
#                'graded_download_url')
#        generated_certificate.course_id = request.POST.get('course_id')
#        generated_certificate.enabled = enabled
#        generated_certificate.save()
