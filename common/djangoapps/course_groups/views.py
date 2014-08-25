from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponse
import json
import logging
import re

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from edxmako.shortcuts import render_to_response

from . import cohorts


log = logging.getLogger(__name__)


def json_http_response(data):
    """
    Return an HttpResponse with the data json-serialized and the right content
    type header.
    """
    return HttpResponse(json.dumps(data), content_type="application/json")


def split_by_comma_and_whitespace(s):
    """
    Split a string both by commas and whitespice.  Returns a list.
    """
    return re.split(r'[\s,]+', s)


@ensure_csrf_cookie
def list_cohorts(request, course_key_string):
    """
    Return json dump of dict:

    {'success': True,
     'cohorts': [{'name': name, 'id': id}, ...]}
    """

    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)

    get_course_with_access(request.user, 'staff', course_key)

    all_cohorts = [{'name': c.name, 'id': c.id}
                   for c in cohorts.get_course_cohorts(course_key)]

    return json_http_response({'success': True,
                               'cohorts': all_cohorts})


@ensure_csrf_cookie
@require_POST
def add_cohort(request, course_key_string):
    """
    Return json of dict:
    {'success': True,
     'cohort': {'id': id,
                'name': name}}

                or

    {'success': False,
     'msg': error_msg} if there's an error
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)

    get_course_with_access(request.user, 'staff', course_key)

    name = request.POST.get("name")
    if not name:
        return json_http_response({'success': False,
                                'msg': "No name specified"})

    try:
        cohort = cohorts.add_cohort(course_key, name)
    except ValueError as err:
        return json_http_response({'success': False,
                                'msg': str(err)})

    return json_http_response({'success': 'True',
                            'cohort': {
                                'id': cohort.id,
                                'name': cohort.name
                                }})


@ensure_csrf_cookie
def users_in_cohort(request, course_key_string, cohort_id):
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
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)

    get_course_with_access(request.user, 'staff', course_key)

    # this will error if called with a non-int cohort_id.  That's ok--it
    # shoudn't happen for valid clients.
    cohort = cohorts.get_cohort_by_id(course_key, int(cohort_id))

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

    return json_http_response({'success': True,
                               'page': page,
                               'num_pages': paginator.num_pages,
                               'users': user_info})


@ensure_csrf_cookie
@require_POST
def add_users_to_cohort(request, course_key_string, cohort_id):
    """
    Return json dict of:

    {'success': True,
     'added': [{'username': ...,
                'name': ...,
                'email': ...}, ...],
     'changed': [{'username': ...,
                  'name': ...,
                  'email': ...,
                  'previous_cohort': ...}, ...],
     'present': [str1, str2, ...],    # already there
     'unknown': [str1, str2, ...]}
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    get_course_with_access(request.user, 'staff', course_key)

    cohort = cohorts.get_cohort_by_id(course_key, cohort_id)

    users = request.POST.get('users', '')
    added = []
    changed = []
    present = []
    unknown = []
    for username_or_email in split_by_comma_and_whitespace(users):
        if not username_or_email:
            continue

        try:
            (user, previous_cohort) = cohorts.add_user_to_cohort(cohort, username_or_email)
            info = {
                'username': user.username,
                'name': user.profile.name,
                'email': user.email,
            }
            if previous_cohort:
                info['previous_cohort'] = previous_cohort
                changed.append(info)
            else:
                added.append(info)
        except ValueError:
            present.append(username_or_email)
        except User.DoesNotExist:
            unknown.append(username_or_email)

    return json_http_response({'success': True,
                               'added': added,
                               'changed': changed,
                               'present': present,
                               'unknown': unknown})


@ensure_csrf_cookie
@require_POST
def remove_user_from_cohort(request, course_key_string, cohort_id):
    """
    Expects 'username': username in POST data.

    Return json dict of:

    {'success': True} or
    {'success': False,
     'msg': error_msg}
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    get_course_with_access(request.user, 'staff', course_key)

    username = request.POST.get('username')
    if username is None:
        return json_http_response({'success': False,
                                   'msg': 'No username specified'})

    cohort = cohorts.get_cohort_by_id(course_key, cohort_id)
    try:
        user = User.objects.get(username=username)
        cohort.users.remove(user)
        return json_http_response({'success': True})
    except User.DoesNotExist:
        log.debug('no user')
        return json_http_response({'success': False,
                                   'msg': "No user '{0}'".format(username)})


def debug_cohort_mgmt(request, course_key_string):
    """
    Debugging view for dev.
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    # add staff check to make sure it's safe if it's accidentally deployed.
    get_course_with_access(request.user, 'staff', course_key)

    context = {'cohorts_ajax_url': reverse(
        'cohorts',
        kwargs={'course_key': course_key.to_deprecated_string()}
    )}
    return render_to_response('/course_groups/debug.html', context)
