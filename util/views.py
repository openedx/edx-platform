from djangomako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
import json
from django.conf import settings
from django.core.context_processors import csrf
from django.http import Http404
import courseware.calc
from django.core.mail import send_mail
from django.conf import settings
import datetime

def calculate(request):
    if not request.user.is_authenticated():
        raise Http404
    equation = request.GET['equation']
    try: 
        result = courseware.calc.evaluator({}, {}, equation)
    except:
        return HttpResponse(json.dumps({'result':'Invalid syntax'}))
    return HttpResponse(json.dumps({'result':result}))

def send_feedback(request):
    if not request.user.is_authenticated():
        raise Http404
    
    feedback = render_to_string("feedback_email.txt", 
                                {"subject":request.POST['subject'], 
                                 "url": request.POST['url'], 
                                 "time": datetime.datetime.now().isoformat(),
                                 "feedback": request.POST['message'], 
                                 "user":request.user.username})

    send_mail("MITx Feedback / " +request.POST['subject'], 
              feedback, 
              settings.DEFAULT_FROM_EMAIL,
              [ settings.DEFAULT_FEEDBACK_EMAIL ],
              fail_silently = False
              )
    return HttpResponse(json.dumps({'success':True}))
