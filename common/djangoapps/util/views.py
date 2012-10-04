import datetime
import json
import pprint
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string

import capa.calc
import track.views


def calculate(request):
    ''' Calculator in footer of every page. '''
    equation = request.GET['equation']
    try:
        result = capa.calc.evaluator({}, {}, equation)
    except:
        event = {'error': map(str, sys.exc_info()),
                 'equation': equation}
        track.views.server_track(request, 'error:calc', event, page='calc')
        return HttpResponse(json.dumps({'result': 'Invalid syntax'}))
    return HttpResponse(json.dumps({'result': str(result)}))


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
                                {"subject": request.POST['subject'],
                                 "url": request.POST['url'],
                                 "time": datetime.datetime.now().isoformat(),
                                 "feedback": request.POST['message'],
                                 "email": email,
                                 "browser": browser,
                                 "user": username})

    send_mail("MITx Feedback / " + request.POST['subject'],
              feedback,
              settings.DEFAULT_FROM_EMAIL,
              [settings.DEFAULT_FEEDBACK_EMAIL],
              fail_silently=False
              )
    return HttpResponse(json.dumps({'success': True}))


def info(request):
    ''' Info page (link from main header) '''
    return render_to_response("info.html", {})


# From http://djangosnippets.org/snippets/1042/
def parse_accept_header(accept):
    """Parse the Accept header *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(lambda x, y: -cmp(x[2], y[2]))
    return result


def accepts(request, media_type):
    """Return whether this request has an Accept header that matches type"""
    accept = parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
    return media_type in [t for (t, p, q) in accept]

def debug_request(request):
    """Return a pretty printed version of the request"""

    return HttpResponse("""<html>
<h1>request:</h1>
<pre>{0}</pre>

<h1>request.GET</h1>:

<pre>{1}</pre>

<h1>request.POST</h1>:
<pre>{2}</pre>

<h1>request.REQUEST</h1>:
<pre>{3}</pre>



</html>
""".format(
    pprint.pformat(request),
    pprint.pformat(dict(request.GET)),
    pprint.pformat(dict(request.POST)),
    pprint.pformat(dict(request.REQUEST)),
    ))
