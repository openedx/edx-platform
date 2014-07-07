import copy

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from util.json_request import JsonResponse

from contentstore.utils import reverse_course_url
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

from .access import has_course_access

__all__ = ['utility_handler']


# pylint: disable=unused-argument
@require_http_methods(("GET"))
@login_required
@ensure_csrf_cookie
def utility_handler(request, course_key_string):
    """
    The restful handler for utilities.

    GET
        html: return html page for all utilities
        json: return json representing all utilities.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()
    course_module = modulestore().get_course(course_key)
    json_request = 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json')
    if request.method == 'GET':
        expanded_utilities = expand_all_action_urls(course_module)
        if json_request:
            return JsonResponse(expanded_utilities)
        else:
            handler_url = reverse_course_url('utility_handler', course_module.id)
            return render_to_response('utilities.html',
                                      {
                                          'handler_url': handler_url,
                                          'context_course': course_module,
                                          'utilities': expanded_utilities
                                      })
    else:
        # return HttpResponseNotFound()
        raise NotImplementedError()


def expand_all_action_urls(course_module):
    """
    Gets the utilities out of the course module and expands their action urls.

    Returns a copy of the utilities with modified urls, without modifying the persisted version
    of the utilities.
    """
    expanded_utilities = []
    for utility in settings.COURSE_UTILITIES:
        expanded_utilities.append(expand_utility_action_url(course_module, utility))
    return expanded_utilities


def expand_utility_action_url(course_module, utility):
    """
    Expands the action URLs for a given utility and returns the modified version.

    The method does a copy of the input utility and does not modify the input argument.
    """
    expanded_utility = copy.deepcopy(utility)

    for item in expanded_utility.get('items'):
        url_prefix = item.get('action_url')
        item['action_url'] = reverse_course_url(url_prefix, course_module.id)

    return expanded_utility
