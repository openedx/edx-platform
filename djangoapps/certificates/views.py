import json
import logging
import settings
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.shortcuts import redirect

import courseware.grades as grades
from certificates.models import GeneratedCertificate, certificate_state_for_student
from mitxmako.shortcuts import render_to_response, render_to_string
from student.models import UserProfile
from student.survey_questions import exit_survey_list_for_student
from student.views import student_took_survey, record_exit_survey

log = logging.getLogger("mitx.certificates")

@login_required
def certificate_request(request):
    ''' Attempt to send a certificate. '''
    if not settings.END_COURSE_ENABLED:
        raise Http404
        
    if request.method == "POST":
        honor_code_verify = request.POST.get('cert_request_honor_code_verify', 'false')
        name_verify = request.POST.get('cert_request_name_verify', 'false')
        id_verify = request.POST.get('cert_request_id_verify', 'false')
        error = ''
        
        def return_error(error):
            return HttpResponse(json.dumps({'success':False,
                                            'error': error }))
        
        if honor_code_verify != 'true':
            error += 'Please verify that you have followed the honor code to receive a certificate. '
    
        if name_verify != 'true':
            error += 'Please verify that your name is correct to receive a certificate. '
    
        if id_verify != 'true':
            error += 'Please certify that you understand the unique ID on the certificate. '
        
        if len(error) > 0:
            return return_error(error)
        
        survey_response = record_exit_survey(request, internal_request=True)
        if not survey_response['success']:
            return return_error( survey_response['error'] )
        
        grade = None
        student_gradesheet = grades.grade_sheet(request.user)
        grade = student_gradesheet['grade']
            
        if not grade:
            return return_error('You have not earned a grade in this course. ')
        
        generate_certificate(request.user, grade)
        
        return HttpResponse(json.dumps({'success':True}))
    
    else:
        #This is not a POST, we should render the page with the form
        
        grade_sheet = grades.grade_sheet(request.user)
        certificate_state = certificate_state_for_student(request.user, grade_sheet['grade'])
        
        if certificate_state['state'] != "requestable":
            return redirect("/profile")
        
        user_info = UserProfile.objects.get(user=request.user)
        
        took_survey = student_took_survey(user_info)
        if settings.DEBUG_SURVEY:
            took_survey = False
        survey_list = []
        if not took_survey:
            survey_list = exit_survey_list_for_student(request.user)
        
        
        context = {'certificate_state' : certificate_state,
                 'took_survey' : took_survey,
                 'survey_list' : survey_list,
                 'name' : user_info.name }
        
        
        return render_to_response('cert_request.html', context)



# This method should only be called if the user has a grade and has requested a certificate
def generate_certificate(user, grade):
    # Make sure to see the comments in models.GeneratedCertificate to read about the valid
    # states for a GeneratedCertificate object
    if grade and user.is_active:
        generated_certificate = None
    
        try:
            generated_certificate = GeneratedCertificate.objects.get(user = user)
        except GeneratedCertificate.DoesNotExist:
            generated_certificate = GeneratedCertificate(user = user, certificate_id = uuid.uuid4().hex)

        generated_certificate.enabled = True
        if generated_certificate.graded_download_url and (generated_certificate.grade != grade):
            log.critical("A graded certificate has been pre-generated with the grade of " + str(generated_certificate.grade) + " but requested with grade " + str(grade) + \
                "! The download URL is " + str(generated_certificate.graded_download_url))
                
        user_name = UserProfile.objects.get(user = user).name
        if generated_certificate.download_url and (generated_certificate.name != user_name):
            log.critical("A Certificate has been pre-generated with the name of " + str(generated_certificate.name) + " but current name is " + str(user_name) + \
                "! The download URL is " + str(generated_certificate.download_url))
        
        
        generated_certificate.grade = grade
        generated_certificate.name = user_name
        generated_certificate.save()
        
        certificate_id = generated_certificate.certificate_id
        
        log.debug("Generating certificate for " + str(user.username) + " with ID: " + certificate_id)
        
        # TODO: If the certificate was pre-generated, send the email that it is ready to download
        if certificate_state_for_student(user, grade)['state'] == "downloadable":
            subject = render_to_string('emails/certificate_ready_subject.txt',{})
            subject = ''.join(subject.splitlines())
            message = render_to_string('emails/certificate_ready.txt',{})
            
            res=send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email,])
        
    else:
        log.warning("Asked to generate a certificate for student " + str(user.username) + " but with a grade of " + str(grade) + " and active status " + str(user.is_active))
