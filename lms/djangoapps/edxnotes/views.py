"""
Views related to EdxNotes.
"""
import json
import logging
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.conf import settings
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from util.json_request import JsonResponse, JsonResponseBadRequest
from edxnotes.exceptions import EdxNotesParseError
from edxnotes.helpers import (
    get_notes,
    get_id_token,
    is_feature_enabled,
    search
)

log = logging.getLogger(__name__)


@login_required
def edxnotes(request, course_id):
    """
    Displays the EdxNotes page.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    if not is_feature_enabled(course):
        raise Http404

    notes = get_notes(request.user, course)
    context = {
        "course": course,
        "search_endpoint": reverse("search_notes", kwargs={"course_id": course_id}),
        "notes": notes,
        "debug": json.dumps(settings.DEBUG),
    }

    return render_to_response("edxnotes/edxnotes.html", context)


@login_required
def search_notes(request, course_id):
    """
    Handles search requests.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    if not is_feature_enabled(course):
        raise Http404

    if not "text" in request.GET:
        return HttpResponseBadRequest()

    query_string = request.GET["text"]
    try:
        search_results = search(request.user, course, query_string)
    except EdxNotesParseError as err:
        return JsonResponseBadRequest({"error": err.message}, status=500)

    return HttpResponse(search_results)


# pylint: disable=unused-argument
@login_required
def get_token(request, course_id):
    """
    Get JWT ID-Token, in case you need new one.
    """
    return HttpResponse(get_id_token(request.user), content_type='text/plain')


def edxnotes_visibility(request, course_id):
    """
    Handle ajax call from "Show notes" checkbox.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    field_data_cache = FieldDataCache([course], course_key, request.user)
    course_module = get_module_for_descriptor(request.user, request, course, field_data_cache, course_key)

    if not is_feature_enabled(course):
        raise Http404

    try:
        visibility = json.loads(request.body)["visibility"]
        course_module.edxnotes_visibility = visibility
        course_module.save()
        return JsonResponse(status=200)
    except (ValueError, KeyError):
        log.warning(
            "Could not decode request body as JSON and find a boolean visibility field: '{0}'".format(request.body)
        )
        return JsonResponseBadRequest()
