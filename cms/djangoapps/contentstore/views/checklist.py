import json
import copy

from util.json_request import JsonResponse
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from django.http import HttpResponseNotFound
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from contentstore.utils import reverse_course_url

from .access import has_course_access
from xmodule.course_module import CourseDescriptor

from django.utils.translation import ugettext

__all__ = ['checklists_handler']


# pylint: disable=unused-argument
@require_http_methods(("GET", "POST", "PUT"))
@login_required
@ensure_csrf_cookie
def checklists_handler(request, course_key_string, checklist_index=None):
    """
    The restful handler for checklists.

    GET
        html: return html page for all checklists
        json: return json representing all checklists. checklist_index is not supported for GET at this time.
    POST or PUT
        json: updates the checked state for items within a particular checklist. checklist_index is required.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)

    json_request = 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json')
    if request.method == 'GET':
        # If course was created before checklists were introduced, copy them over
        # from the template.
        if not course_module.checklists:
            course_module.checklists = CourseDescriptor.checklists.default
            modulestore().update_item(course_module, request.user.id)

        expanded_checklists = expand_all_action_urls(course_module)
        if json_request:
            return JsonResponse(expanded_checklists)
        else:
            handler_url = reverse_course_url('checklists_handler', course_key)
            return render_to_response('checklists.html',
                                      {
                                          'handler_url': handler_url,
                                          # context_course is used by analytics
                                          'context_course': course_module,
                                          'checklists': expanded_checklists
                                      })
    elif json_request:
        # Can now assume POST or PUT because GET handled above.
        if checklist_index is not None and 0 <= int(checklist_index) < len(course_module.checklists):
            index = int(checklist_index)
            persisted_checklist = course_module.checklists[index]
            modified_checklist = json.loads(request.body)
            # Only thing the user can modify is the "checked" state.
            # We don't want to persist what comes back from the client because it will
            # include the expanded action URLs (which are non-portable).
            for item_index, item in enumerate(modified_checklist.get('items')):
                persisted_checklist['items'][item_index]['is_checked'] = item['is_checked']
            # seeming noop which triggers kvs to record that the metadata is
            # not default
            course_module.checklists = course_module.checklists
            course_module.save()
            modulestore().update_item(course_module, request.user.id)
            expanded_checklist = expand_checklist_action_url(course_module, persisted_checklist)
            return JsonResponse(localize_checklist_text(expanded_checklist))
        else:
            return HttpResponseBadRequest(
                ("Could not save checklist state because the checklist index "
                 "was out of range or unspecified."),
                content_type="text/plain"
            )
    else:
        return HttpResponseNotFound()


def expand_all_action_urls(course_module):
    """
    Gets the checklists out of the course module and expands their action urls.

    Returns a copy of the checklists with modified urls, without modifying the persisted version
    of the checklists.
    """
    expanded_checklists = []
    for checklist in course_module.checklists:
        expanded_checklists.append(localize_checklist_text(expand_checklist_action_url(course_module, checklist)))
    return expanded_checklists


def expand_checklist_action_url(course_module, checklist):
    """
    Expands the action URLs for a given checklist and returns the modified version.

    The method does a copy of the input checklist and does not modify the input argument.
    """
    expanded_checklist = copy.deepcopy(checklist)

    urlconf_map = {
        "ManageUsers": "course_team_handler",
        "CourseOutline": "course_handler",
        "SettingsDetails": "settings_handler",
        "SettingsGrading": "grading_handler",
    }

    for item in expanded_checklist.get('items'):
        action_url = item.get('action_url')
        if action_url in urlconf_map:
            item['action_url'] = reverse_course_url(urlconf_map[action_url], course_module.id)

    return expanded_checklist

def localize_checklist_text(checklist):
    """
    Localize texts for a given checklist and returns the modified version.

    The method does an in-place operation so the input checklist is modified directly.
    """
    # Localize checklist name
    checklist['short_description'] = ugettext(checklist['short_description'])

    # Localize checklist items
    for item in checklist.get('items'):
        item['short_description'] = ugettext(item['short_description'])
        item['long_description'] = ugettext(item['long_description']) if item['long_description'] != '' else u''
        item['action_text'] = ugettext(item['action_text']) if item['action_text'] != "" else u""

    return checklist
