from djangomako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
import json
from django.conf import settings
from django.core.context_processors import csrf
from django.http import Http404
import courseware.capa.calc
from django.core.mail import send_mail
from django.conf import settings
import datetime
import sys
import track.views

def calculate(request):
#    if not request.user.is_authenticated():
#        raise Http404
    equation = request.GET['equation']
    try: 
        result = courseware.capa.calc.evaluator({}, {}, equation)
    except:
        event = {'error':map(str,sys.exc_info()),
                 'equation':equation}
        track.views.server_track(request, 'error:calc', event, page='calc')
        return HttpResponse(json.dumps({'result':'Invalid syntax'}))
    return HttpResponse(json.dumps({'result':result}))

def send_feedback(request):
#    if not request.user.is_authenticated():
#        raise Http404
    try: 
        username = request.user.username
    except: 
        username = "anonymous"
    
    feedback = render_to_string("feedback_email.txt", 
                                {"subject":request.POST['subject'], 
                                 "url": request.POST['url'], 
                                 "time": datetime.datetime.now().isoformat(),
                                 "feedback": request.POST['message'], 
                                 "user":username})

    send_mail("MITx Feedback / " +request.POST['subject'], 
              feedback, 
              settings.DEFAULT_FROM_EMAIL,
              [ settings.DEFAULT_FEEDBACK_EMAIL ],
              fail_silently = False
              )
    return HttpResponse(json.dumps({'success':True}))

def info(request):
    return render_to_response("info.html", {})
