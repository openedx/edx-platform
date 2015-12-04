"""
Views related to EdxNotes.
"""
import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.conf import settings
from django.core.urlresolvers import reverse
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from util.json_request import JsonResponse, JsonResponseBadRequest
from edxnotes.exceptions import EdxNotesParseError, EdxNotesServiceUnavailable
from edxnotes.helpers import (
    get_notes,
    get_id_token,
    is_feature_enabled,
    search,
    get_course_position,
)

log = logging.getLogger(__name__)


@login_required
def edxnotes(request, course_id):
    """
    Displays the EdxNotes page.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    if not is_feature_enabled(course):
        raise Http404

    try:
        notes = get_notes(request.user, course)
    except EdxNotesServiceUnavailable:
        raise Http404

    context = {
        "course": course,
        "search_endpoint": reverse("search_notes", kwargs={"course_id": course_id}),
        "notes": notes,
        "debug": json.dumps(settings.DEBUG),
        'position': None,
    }

    if not notes:
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2
        )
        course_module = get_module_for_descriptor(
            request.user, request, course, field_data_cache, course_key, course=course
        )
        position = get_course_position(course_module)
        if position:
            context.update({
                'position': position,
            })

    return render_to_response("edxnotes/edxnotes.html", context)


@login_required
def search_notes(request, course_id):
    """
    Handles search requests.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    if not is_feature_enabled(course):
        raise Http404

    if "text" not in request.GET:
        return HttpResponseBadRequest()

    query_string = request.GET["text"]
    try:
        search_results = search(request.user, course, query_string)
    except (EdxNotesParseError, EdxNotesServiceUnavailable) as err:
        return JsonResponseBadRequest({"error": err.message}, status=500)

    return HttpResponse(search_results)


# pylint: disable=unused-argument
@login_required
def get_token(request, course_id):
    """
    Get JWT ID-Token, in case you need new one.
    """
    return HttpResponse(get_id_token(request.user), content_type='text/plain')


@login_required
def edxnotes_visibility(request, course_id):
    """
    Handle ajax call from "Show notes" checkbox.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    field_data_cache = FieldDataCache([course], course_key, request.user)
    course_module = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course_key, course=course
    )

    if not is_feature_enabled(course):
        raise Http404

    try:
        visibility = json.loads(request.body)["visibility"]
        course_module.edxnotes_visibility = visibility
        course_module.save()
        return JsonResponse(status=200)
    except (ValueError, KeyError):
        log.warning(
            "Could not decode request body as JSON and find a boolean visibility field: '%s'", request.body
        )
        return JsonResponseBadRequest()
