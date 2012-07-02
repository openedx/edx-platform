from mitxmako.shortcuts import render_to_response
from keystore.django import keystore
from django_future.csrf import ensure_csrf_cookie
from django.http import HttpResponse
import json


@ensure_csrf_cookie
def index(request):
    # TODO (cpennington): These need to be read in from the active user
    org = 'mit.edu'
    course = '6002xs12'
    name = '6.002_Spring_2012'
    course = keystore().get_item(['i4x', org, course, 'course', name])
    weeks = course.get_children()
    return render_to_response('index.html', {'weeks': weeks})


def edit_item(request):
    item_id = request.GET['id']
    item = keystore().get_item(item_id)
    return render_to_response('unit.html', {
        'contents': item.get_html(),
        'js_module': item.js_module_name(),
        'category': item.category,
        'name': item.name,
    })


def save_item(request):
    item_id = request.POST['id']
    data = json.loads(request.POST['data'])
    keystore().update_item(item_id, data)
    return HttpResponse(json.dumps({}))
