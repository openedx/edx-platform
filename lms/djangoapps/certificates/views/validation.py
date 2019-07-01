from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from edxmako.shortcuts import render_to_response
from django.template.context_processors import csrf
from lms.djangoapps.certificates.models import GeneratedCertificate
from django.shortcuts import redirect


@require_http_methods(("GET", "POST"))
def validate_certificate(request):
    context = {"csrftoken": csrf(request)["csrf_token"]}
    if request.method == "POST":
        cert_id = request.POST.get('cert-id')
        certificate_exists = GeneratedCertificate.objects.filter(
            verify_uuid=cert_id
        ).exists()
        if certificate_exists:
            return redirect('/certificates/' + cert_id)
        context['exists'] = certificate_exists
        context['_id'] = cert_id
    return render_to_response('certificates/validate_certificates.html', context)