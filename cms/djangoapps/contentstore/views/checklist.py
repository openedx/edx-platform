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
from xmodule.modulestore.django import loc_mapper

from xmodule.modulestore.inheritance import own_metadata


from ..utils import get_modulestore
from .access import has_course_access
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.locator import BlockUsageLocator

__all__ = ['checklists_handler']


# pylint: disable=unused-argument
@require_http_methods(("GET", "POST", "PUT"))
@login_required
@ensure_csrf_cookie
def checklists_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None, checklist_index=None):
    """
    The restful handler for checklists.

    GET
        html: return html page for all checklists
        json: return json representing all checklists. checklist_index is not supported for GET at this time.
    POST or PUT
        json: updates the checked state for items within a particular checklist. checklist_index is required.
    """
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, location):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(location)

    modulestore = get_modulestore(old_location)
    course_module = modulestore.get_item(old_location)

    json_request = 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json')
    if request.method == 'GET':
        # If course was created before checklists were introduced, copy them over
        # from the template.
        if not course_module.checklists:
            course_module.checklists = CourseDescriptor.checklists.default
            course_module.save()
            modulestore.update_metadata(old_location, own_metadata(course_module))

        expanded_checklists = expand_all_action_urls(course_module)
        if json_request:
            return JsonResponse(expanded_checklists)
        else:
            handler_url = location.url_reverse('checklists/', '')
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
            modulestore.update_metadata(old_location, own_metadata(course_module))
            expanded_checklist = expand_checklist_action_url(course_module, persisted_checklist)
            return JsonResponse(expanded_checklist)
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
        expanded_checklists.append(expand_checklist_action_url(course_module, checklist))
    return expanded_checklists


def expand_checklist_action_url(course_module, checklist):
    """
    Expands the action URLs for a given checklist and returns the modified version.

    The method does a copy of the input checklist and does not modify the input argument.
    """
    expanded_checklist = copy.deepcopy(checklist)

    urlconf_map = {
        "ManageUsers": "course_team",
        "CourseOutline": "course",
        "SettingsDetails": "settings/details",
        "SettingsGrading": "settings/grading",
    }

    for item in expanded_checklist.get('items'):
        action_url = item.get('action_url')
        if action_url in urlconf_map:
            url_prefix = urlconf_map[action_url]
            ctx_loc = course_module.location
            location = loc_mapper().translate_location(ctx_loc.course_id, ctx_loc, False, True)
            item['action_url'] = location.url_reverse(url_prefix, '')

    return expanded_checklist
