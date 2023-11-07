from rest_framework.generics import RetrieveAPIView
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import loader
from .models import Feedback
from .forms import FeedbackForm
import requests
from django.views.decorators.csrf import  ensure_csrf_cookie 
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings

def index(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':               
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = Feedback()            
            feedback.email = form.cleaned_data['email']
            feedback.lesson_url = form.cleaned_data['lesson_url']
            feedback.unit_title = form.cleaned_data['unit_title']
            feedback.instance_code = form.cleaned_data['instance_code']
            feedback.category_id = form.cleaned_data['category_id']
            feedback.content = form.cleaned_data['content']
            feedback.attachment = request.FILES.get('attachment', '')
            feedback.save()

            # Save into CRM
            url = "https://crm2.funix.edu.vn/index.php?entryPoint=publicEntrypoint&subaction=LMSFeedback"
            username = 'funix'
            password = '@1231funixFeedback'

            if feedback.attachment == False:
                attachmentURL = ''
            else:
                attachmentURL = "http://courses.funix.edu.vn/media/" + feedback.attachment.name


            data = {
                'email': feedback.email,
                'lesson_url': feedback.lesson_url,
                'unit_title': feedback.unit_title,
                'instance_code': feedback.instance_code,
                'category_id': feedback.category_id,
                'content': feedback.content,
                'attachment': attachmentURL,
            }
            resp = requests.post(url, data=data, auth=(username, password), verify=False)

            return HttpResponse("success")
        else:
            return HttpResponse(form.errors)
            #print(form.errors)

    context = {
        'email': request.user.email
    }
    response = render_to_response('feedback_form.html', context)
    # template = loader.get_template('feedback_form.html')
    return response




@api_view(['POST'])
def create_feedback (request) :
    form = FeedbackForm(request.POST, request.FILES)
    # url_lms = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    if form.is_valid():
        feedback = Feedback() 
       
        feedback.email = form.cleaned_data['email']
        feedback.category_id = form.cleaned_data['category_id']
        feedback.content = form.cleaned_data['content']
        feedback.attachment = request.FILES.get('attachment', '')
        feedback.course_id = form.cleaned_data['course_id']
        feedback.lesson_url = form.cleaned_data['lesson_url']
        feedback.save()
        print('============')
    #     if feedback.attachment == False:
    #         attachmentURL = ''
    #     else:
    #         attachmentURL = url_lms+ '/media/' + feedback.attachment.name
    #     print('==============',attachmentURL )
    #     category = [
    #         {"id" : 'outdated' , "content": 'Content contains outdated information' } ,
    #         {'id' : "bad_explain" , "content" : "Content is not explained well"} ,
    #         {"id" : "insufficient_details" , "content" : "Content needs more detail"},
    #         {"id" : "broken_resource" , "content" : "Resource is missing or broken (link, dataset, etc)"},
    #         {"id" : "error_translation" , "content" : "Translation Error in content"}
    #         ]
    #     category_id = ''
    #     for c in category :
    #         if form.cleaned_data['category_id'] == c['content'] :
    #             category_id = c['id']
    #     data = {
    #             'ticket_title': 'lms_test',
    #             'ticket_category': category_id,
    #             'ticket_description': feedback.content ,
    #             "student_id" : 3
    #         }

    return HttpResponse('success')