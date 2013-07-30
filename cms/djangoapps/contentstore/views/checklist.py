import json

from util.json_request import JsonResponse
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore.inheritance import own_metadata

from ..utils import get_modulestore, get_url_reverse
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

    # If course was created before checklists were introduced, copy them over from the template.
    copied = False
    if not course_module.checklists:
        course_module.checklists = CourseDescriptor.checklists.default
        copied = True

    checklists, modified = expand_checklist_action_urls(course_module)
    if copied or modified:
        course_module.save()
        modulestore.update_metadata(location, own_metadata(course_module))
    return render_to_response('checklists.html',
                              {
                                  'context_course': course_module,
                                  'checklists': checklists
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
            course_module.checklists[index] = json.loads(request.body)
            # seeming noop which triggers kvs to record that the metadata is not default
            course_module.checklists = course_module.checklists
            checklists, _ = expand_checklist_action_urls(course_module)
            course_module.save()
            modulestore.update_metadata(location, own_metadata(course_module))
            return JsonResponse(checklists[index])
        else:
            return HttpResponseBadRequest(
                "Could not save checklist state because the checklist index was out of range or unspecified.",
                content_type="text/plain")
    elif request.method == 'GET':
        # In the JavaScript view initialize method, we do a fetch to get all the checklists.
        checklists, modified = expand_checklist_action_urls(course_module)
        if modified:
            course_module.save()
            modulestore.update_metadata(location, own_metadata(course_module))
        return JsonResponse(checklists)


def expand_checklist_action_urls(course_module):
    """
    Gets the checklists out of the course module and expands their action urls
    if they have not yet been expanded.

    Returns the checklists with modified urls, as well as a boolean
    indicating whether or not the checklists were modified.
    """
    checklists = course_module.checklists
    modified = False
    for checklist in checklists:
        if not checklist.get('action_urls_expanded', False):
            for item in checklist.get('items'):
                item['action_url'] = get_url_reverse(item.get('action_url'), course_module)
            checklist['action_urls_expanded'] = True
            modified = True

    return checklists, modified
