"""
Views related to EdxNotes.
"""
import json
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from edxnotes.helpers import (
    get_endpoint,
    get_token,
    get_notes,
    is_feature_enabled
)


@login_required
def edxnotes(request, course_id):
    """ Displays the EdxNotes page. """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    if not is_feature_enabled(course):
        raise Http404

    notes = get_notes(request.user, course)
    context = {
        # Use camelCase to name keys.
        "course": course,
        "endpoint": get_endpoint(),
        "notes": notes,
        "token": get_token(),
        "debug": json.dumps(settings.DEBUG),
    }

    return render_to_response("edxnotes.html", context)
