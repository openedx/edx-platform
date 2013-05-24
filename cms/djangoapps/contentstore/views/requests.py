import json

from django.http import HttpResponse
from mitxmako.shortcuts import render_to_string, render_to_response

__all__ = ['edge', 'event', 'landing']


# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})


# points to the temporary edge page
def edge(request):
    return render_to_response('university_profiles/edge.html', {})


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def get_request_method(request):
    """
    Using HTTP_X_HTTP_METHOD_OVERRIDE, in the request metadata, determine
    what type of request came from the client, and return it.
    """
    # NB: we're setting Backbone.emulateHTTP to true on the client so everything comes as a post!!!
    if request.method == 'POST' and 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
        real_method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']
    else:
        real_method = request.method

    return real_method


def create_json_response(errmsg=None):
    if errmsg is not None:
        resp = HttpResponse(json.dumps({'Status': 'Failed', 'ErrMsg': errmsg}))
    else:
        resp = HttpResponse(json.dumps({'Status': 'OK'}))
    return resp


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)
