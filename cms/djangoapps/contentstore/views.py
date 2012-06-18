from mitxmako.shortcuts import render_to_response
from keystore.django import keystore
from django.contrib.auth.decorators import login_required


def index(request):
    # FIXME (cpennington): These need to be read in from the active user
    org = 'mit.edu'
    course = '6002xs12'
    course = keystore.get_item(['i4x', org, course, 'Course', None])
    weeks = course.get_children()
    return render_to_response('index.html', {'weeks': weeks})
