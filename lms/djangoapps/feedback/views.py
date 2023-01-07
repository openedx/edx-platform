from rest_framework.generics import RetrieveAPIView
from common.djangoapps.edxmako.shortcuts import render_to_response

from django.http import HttpResponse
from django.template import loader
from .models import Feedback
from .forms import FeedbackForm
import requests

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
