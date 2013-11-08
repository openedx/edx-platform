from django.http import HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_string, render_to_response

__all__ = ['edge', 'event', 'landing']


# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})


# points to the temporary edge page
def edge(request):
    return redirect('/')


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)
