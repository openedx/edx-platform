import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from mitxmako.shortcuts import render_to_response
import courseware.grades as grades
from certificates.models import GeneratedCertificate

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

log = logging.getLogger("mitx.certificates")

@login_required
def certificate_request(request):
    ''' Attempt to send a certificate. '''
    if request.method != "POST" or not settings.END_COURSE_ENABLED:
        raise Http404
    
    verification_checked = request.POST.get('cert_request_verify', 'false')
    destination_email = request.POST.get('cert_request_email', '')
    error = ''
    
    if verification_checked != 'true':
        error += 'You must verify that you have followed the honor code to receive a certificate. '
    try:
        validate_email(destination_email)
    except ValidationError:
        error += 'Please provide a valid email address to send the certificate. '
    grade = None
    if len(error) == 0:
        student_gradesheet = grades.grade_sheet(request.user)
        
        grade = student_gradesheet['grade']
        
        if not grade:
            error += 'You have not earned a grade in this course. '
            
    if len(error) == 0:
        generate_certificate(request.user, grade, destination_email)
        
        # TODO: Send the certificate email
        return HttpResponse(json.dumps({'success':True,
                                        'value': 'A certificate is being generated and will be sent. ' }))
    else:
        return HttpResponse(json.dumps({'success':False,
                                        'error': error }))


# This method should only be called if the user has a grade and has requested a certificate
def generate_certificate(user, grade, destination_email):
    # Make sure to see the comments in models.GeneratedCertificate to read about the valid
    # states for a GeneratedCertificate object
    generated_certificate = None
    
    try:
        generated_certificate = GeneratedCertificate.objects.get(user = user)
    except GeneratedCertificate.DoesNotExist:
        generated_certificate = GeneratedCertificate(user = user, certificate_id = uuid.uuid4().hex)

    generated_certificate.enabled = True
    generated_certificate.save()
    
    certificate_id = generated_certificate.certificate_id
    
    log.debug("Generating certificate for " + str(user.username) + " with ID: " + certificate_id)
    
