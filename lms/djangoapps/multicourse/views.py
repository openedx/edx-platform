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
from multicourse import multicourse_settings

def mitxhome(request):
    ''' Home page (link from main header). List of courses.  '''
    if settings.DEBUG:
        print "[djangoapps.multicourse.mitxhome] MITX_ROOT_URL = " + settings.MITX_ROOT_URL
    if settings.ENABLE_MULTICOURSE:
        context = {'courseinfo' : multicourse_settings.COURSE_SETTINGS}
        return render_to_response("mitxhome.html", context)
    return info(request)

