import json
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect
import logging

from courseware.courses import get_course_with_access
from mitxmako.shortcuts import render_to_response, render_to_string
from string_util import split_by_comma_and_whitespace

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
    Return users in the cohort.  Show up to 100 per page, and page
    using the 'page' GET attribute in the call.  Format:

    Returns:
        Json dump of dictionary in the following format:
        {'success': True,
         'page': page,
         'num_pages': paginator.num_pages,
         'users': [{'username': ..., 'email': ..., 'name': ...}]
    }
    """
    get_course_with_access(request.user, course_id, 'staff')

    cohort = models.get_cohort_by_id(course_id, int(cohort_id))

    paginator = Paginator(cohort.users.all(), 100)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        # return the first page
        page = 1
        users = paginator.page(page)
    except EmptyPage:
        # Page is out of range.  Return last page
        page = paginator.num_pages
        contacts = paginator.page(page)

    user_info = [{'username': u.username,
                  'email': u.email,
                  'name': '{0} {1}'.format(u.first_name, u.last_name)}
                  for u in users]

    return JsonHttpReponse({'success': True,
                            'page': page,
                            'num_pages': paginator.num_pages,
                            'users': user_info})


@ensure_csrf_cookie
def add_users_to_cohort(request, course_id, cohort_id):
    """
    Return json dict of:

    {'success': True,
     'added': [{'username': username,
                'name': name,
                'email': email}, ...],
     'present': [str1, str2, ...],    # already there
     'unknown': [str1, str2, ...]}
    """
    get_course_with_access(request.user, course_id, 'staff')

    if request.method != "POST":
        raise Http404("Must POST to add users to cohorts")

    cohort = models.get_cohort_by_id(course_id, cohort_id)

    users = request.POST.get('users', '')
    added = []
    present = []
    unknown = []
    for username_or_email in split_by_comma_and_whitespace(users):
        try:
            user = models.add_user_to_cohort(cohort, username_or_email)
            added.append({'username': user.username,
                          'name': "{0} {1}".format(user.first_name, user.last_name),
                          'email': user.email,
                          })
        except ValueError:
            present.append(username_or_email)
        except User.DoesNotExist:
            unknown.append(username_or_email)

    return JsonHttpReponse({'success': True,
                            'added': added,
                            'present': present,
                            'unknown': unknown})


def debug_cohort_mgmt(request, course_id):
    """
    Debugging view for dev.
    """
    # add staff check to make sure it's safe if it's accidentally deployed.
    get_course_with_access(request.user, course_id, 'staff')

    context = {'cohorts_ajax_url': reverse('cohorts',
                                           kwargs={'course_id': course_id})}
    return render_to_response('/course_groups/debug.html', context)
