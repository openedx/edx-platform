import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from mitxmako.shortcuts import render_to_response

import courseware.grades as grades

@login_required
def certificate_request(request):
    ''' Attempt to send a certificate. '''
    if request.method != "POST":
        raise Http404
    
    verification_checked = request.POST.get('cert_request_verify', 'false')
    destination_email = request.POST.get('cert_request_email', '')
    error = ''
    
    if verification_checked != 'true':
        error += 'You must verify that you have followed the honor code to receive a certificate. '
    
    # TODO: Check e-mail format is correct. 
    if len(destination_email) < 5:
        error += 'Please provide a valid email address to send the certificate. '
        
    grade = None
    if len(error) == 0:
        student_gradesheet = grades.grade_sheet(request.user)
        
        grade = student_gradesheet['grade']
        
        if not grade:
            error += 'You have not earned a grade in this course. '
            
    if len(error) == 0:
        # TODO: Send the certificate email
        return HttpResponse(json.dumps({'success':True,
                                        'value': 'A certificate is being generated and will be sent. ' }))
    else:
        return HttpResponse(json.dumps({'success':False,
                                        'error': error }))
