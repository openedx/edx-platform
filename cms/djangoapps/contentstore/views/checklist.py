import json
import copy

from util.json_request import JsonResponse
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore.inheritance import own_metadata

from ..utils import get_modulestore
from .access import get_location_and_verify_access
from xmodule.course_module import CourseDescriptor

__all__ = ['get_checklists', 'update_checklist']


@ensure_csrf_cookie
@login_required
def get_checklists(request, org, course, name):
    """
    Send models, views, and html for displaying the course checklists.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    modulestore = get_modulestore(location)
    course_module = modulestore.get_item(location)

    # If course was created before checklists were introduced, copy them over
    # from the template.
    if not course_module.checklists:
        course_module.checklists = CourseDescriptor.checklists.default
        course_module.save()
        modulestore.update_metadata(location, own_metadata(course_module))

    expanded_checklists = expand_all_action_urls(course_module)
    return render_to_response('checklists.html',
                              {
                                  'context_course': course_module,
                                  'checklists': expanded_checklists
                              })


@require_http_methods(("GET", "POST", "PUT"))
@ensure_csrf_cookie
@login_required
def update_checklist(request, org, course, name, checklist_index=None):
    """
    restful CRUD operations on course checklists. The payload is a json rep of
    the modified checklist. For PUT or POST requests, the index of the
    checklist being modified must be included; the returned payload will
    be just that one checklist. For GET requests, the returned payload
    is a json representation of the list of all checklists.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)
    modulestore = get_modulestore(location)
    course_module = modulestore.get_item(location)

    if request.method in ("POST", "PUT"):
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
            modulestore.update_metadata(location, own_metadata(course_module))
            expanded_checklist = expand_checklist_action_url(course_module, persisted_checklist)
            return JsonResponse(expanded_checklist)
        else:
            return HttpResponseBadRequest(
                ( "Could not save checklist state because the checklist index "
                "was out of range or unspecified."),
                content_type="text/plain"
            )
    elif request.method == 'GET':
        # In the JavaScript view initialize method, we do a fetch to get all
        # the checklists.
        expanded_checklists = expand_all_action_urls(course_module)
        return JsonResponse(expanded_checklists)


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
        "ManageUsers": "manage_users",
        "SettingsDetails": "settings_details",
        "SettingsGrading": "settings_grading",
        "CourseOutline": "course_index",
        "Checklists": "checklists",
    }
    for item in expanded_checklist.get('items'):
        action_url = item.get('action_url')
        if action_url not in urlconf_map:
            continue
        urlconf_name = urlconf_map[action_url]
        item['action_url'] = reverse(urlconf_name, kwargs={
            'org': course_module.location.org,
            'course': course_module.location.course,
            'name': course_module.location.name,
        })

    return expanded_checklist
