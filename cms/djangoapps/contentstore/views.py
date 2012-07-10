from util.json_request import expect_json
import json

from django.http import HttpResponse
from django_future.csrf import ensure_csrf_cookie
from fs.osfs import OSFS
from django.core.urlresolvers import reverse
from xmodule.modulestore import Location
from github_sync import repo_path_from_location, export_to_github

from mitxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore


@ensure_csrf_cookie
def index(request):
    courses = modulestore().get_items(['i4x', None, None, 'course', None])
    return render_to_response('index.html', {
        'courses': [(course.metadata['display_name'],
                    reverse('course_index', args=[
                        course.location.org,
                        course.location.course,
                        course.location.name]))
                    for course in courses]
    })


@ensure_csrf_cookie
def course_index(request, org, course, name):
    # TODO (cpennington): These need to be read in from the active user
    course = modulestore().get_item(['i4x', org, course, 'course', name])
    weeks = course.get_children()
    return render_to_response('course_index.html', {'weeks': weeks})


def edit_item(request):
    item_id = request.GET['id']
    item = modulestore().get_item(item_id)
    return render_to_response('unit.html', {
        'contents': item.get_html(),
        'js_module': item.js_module_name(),
        'category': item.category,
        'name': item.name,
    })


@expect_json
def save_item(request):
    item_id = request.POST['id']
    data = json.loads(request.POST['data'])
    modulestore().update_item(item_id, data)

    # Export the course back to github
    course_location = Location(item_id)._replace(category='course', name=None)
    courses = modulestore().get_items(course_location)
    for course in courses:
        repo_path = repo_path_from_location(course.location)
        export_to_github(course, repo_path, "CMS Edit")

    return HttpResponse(json.dumps({}))


def temp_force_export(request):
    org = 'mit.edu'
    course = '6002xs12'
    name = '6.002_Spring_2012'
    course = modulestore().get_item(['i4x', org, course, 'course', name])
    fs = OSFS('../data-export-test')
    xml = course.export_to_xml(fs)
    with fs.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

    return HttpResponse('Done')
