from mitxmako.shortcuts import render_to_response
from keystore.django import keystore
from django.contrib.auth.decorators import login_required


@login_required
def calendar(request, org, course):
    weeks = keystore.get_children_for_item(['i4x', org, course, 'Course', None])
    return render_to_response('calendar.html', {'weeks': weeks})


def index(request):
    return render_to_response('index.html', {})
