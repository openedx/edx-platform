import json
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect
import logging

from courseware.courses import get_course_with_access
from mitxmako.shortcuts import render_to_response, render_to_string
from .models import CourseUserGroup
from . import models

import track.views


log = logging.getLogger(__name__)

def JsonHttpReponse(data):
    """
    Return an HttpResponse with the data json-serialized and the right content type
    header.  Named to look like a class.
    """
    return HttpResponse(json.dumps(data), content_type="application/json")

@ensure_csrf_cookie
def list_cohorts(request, course_id):
    """
    Return json dump of dict:

    {'success': True,
     'cohorts': [{'name': name, 'id': id}, ...]}
    """
    get_course_with_access(request.user, course_id, 'staff')

    cohorts = [{'name': c.name, 'id': c.id}
               for c in models.get_course_cohorts(course_id)]

    return JsonHttpReponse({'success': True,
                            'cohorts': cohorts})


@ensure_csrf_cookie
def add_cohort(request, course_id):
    """
    Return json of dict:
    {'success': True,
     'cohort': {'id': id,
                'name': name}}

                or

    {'success': False,
     'msg': error_msg} if there's an error
    """
    get_course_with_access(request.user, course_id, 'staff')


    if request.method != "POST":
        raise Http404("Must POST to add cohorts")

    name = request.POST.get("name")
    if not name:
        return JsonHttpReponse({'success': False,
                                'msg': "No name specified"})

    try:
        cohort = models.add_cohort(course_id, name)
    except ValueError as err:
        return JsonHttpReponse({'success': False,
                                'msg': str(err)})

    return JsonHttpReponse({'success': 'True',
                            'cohort': {
                                'id': cohort.id,
                                'name': cohort.name
                                }})


@ensure_csrf_cookie
def users_in_cohort(request, course_id, cohort_id):
    """
    """
    get_course_with_access(request.user, course_id, 'staff')

    return JsonHttpReponse({'error': 'Not implemented'})


@ensure_csrf_cookie
def add_users_to_cohort(request, course_id):
    """
    """
    get_course_with_access(request.user, course_id, 'staff')

    return JsonHttpReponse({'error': 'Not implemented'})


def debug_cohort_mgmt(request, course_id):
    """
    Debugging view for dev.
    """
    # add staff check to make sure it's safe if it's accidentally deployed.
    get_course_with_access(request.user, course_id, 'staff')
    
    context = {'cohorts_ajax_url': reverse('cohorts',
                                           kwargs={'course_id': course_id})}
    return render_to_response('/course_groups/debug.html', context)
