import datetime
import json
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string

import courseware.capa.calc
import track.views

def calculate(request):
    ''' Calculator in footer of every page. '''
    equation = request.GET['equation']
    try: 
        result = courseware.capa.calc.evaluator({}, {}, equation)
    except:
        event = {'error':map(str,sys.exc_info()),
                 'equation':equation}
        track.views.server_track(request, 'error:calc', event, page='calc')
        return HttpResponse(json.dumps({'result':'Invalid syntax'}))
    return HttpResponse(json.dumps({'result':str(result)}))

def send_feedback(request):
    ''' Feeback mechanism in footer of every page. '''
    try: 
        username = request.user.username
        email = request.user.email
    except: 
        username = "anonymous"
        email = "anonymous"
    
    try: 
        browser = request.META['HTTP_USER_AGENT']
    except: 
        browser = "Unknown"
    
    feedback = render_to_string("feedback_email.txt", 
                                {"subject":request.POST['subject'], 
                                 "url": request.POST['url'], 
                                 "time": datetime.datetime.now().isoformat(),
                                 "feedback": request.POST['message'], 
                                 "email":email,
                                 "browser":browser,
                                 "user":username})

    send_mail("MITx Feedback / " +request.POST['subject'], 
              feedback, 
              settings.DEFAULT_FROM_EMAIL,
              [ settings.DEFAULT_FEEDBACK_EMAIL ],
              fail_silently = False
              )
    return HttpResponse(json.dumps({'success':True}))

def info(request):
    ''' Info page (link from main header) '''
    return render_to_response("info.html", {})

def mitxhome(request):
    ''' Home page (link from main header). List of courses.  '''
    if settings.ENABLE_MULTICOURSE:
        return render_to_response("mitxhome.html", {})
    return info(request)
