from mitxmako.shortcuts import render_to_response
from keystore.django import keystore
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


def index(request):
    # TODO (cpennington): These need to be read in from the active user
    org = 'mit.edu'
    course = '6002xs12'
    name = '6.002 Spring 2012'
    course = keystore().get_item(['i4x', org, course, 'Course', name])
    weeks = course.get_children()
    return render_to_response('index.html', {'weeks': weeks})


def edit_item(request):
    item_id = request.GET['id']
    item = keystore().get_item(item_id)
    return render_to_response('unit.html', {
        'contents': item.get_html(),
        'type': item.type,
    })
