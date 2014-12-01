"""
Views related to EdxNotes.
"""
import json
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.conf import settings
from util.json_request import JsonResponseBadRequest
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from edxnotes.exceptions import EdxNotesParseError
from edxnotes.helpers import (
    get_notes,
    get_id_token,
    is_feature_enabled,
    search
)


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
    return HttpResponse(get_id_token(request.user))
