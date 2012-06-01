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
    
    honor_code_verify = request.POST.get('cert_request_honor_code_verify', 'false')
    name_verify = request.POST.get('cert_request_name_verify', 'false')
    id_verify = request.POST.get('cert_request_id_verify', 'false')
    error = ''
    
    
    if honor_code_verify != 'true':
        error += 'Please verify that you have followed the honor code to receive a certificate. '
    
    if name_verify != 'true':
        error += 'Please verify that your name is correct to receive a certificate. '
    
    if id_verify != 'true':
        error += 'Please certify that you understand the unique ID on the certificate. '
        
        
    grade = None
    if len(error) == 0:
        student_gradesheet = grades.grade_sheet(request.user)
        
        grade = student_gradesheet['grade']
        
        if not grade:
            error += 'You have not earned a grade in this course. '
            
    if len(error) == 0:
        generate_certificate(request.user, grade)
        
        # TODO: Send the certificate email
        return HttpResponse(json.dumps({'success':True}))
    else:
        return HttpResponse(json.dumps({'success':False,
                                        'error': error }))


# This method should only be called if the user has a grade and has requested a certificate
def generate_certificate(user, grade):
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
    
