from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access

from . import TEAMS_NAMESPACE


def teams_dashboard(request, course_id):
    """
    Renders the teams dashboard, which is shown on the "Teams" tab.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    context = {
        "course": course,
    }

    return render_to_response("teams/teams.html", context, namespace=TEAMS_NAMESPACE)
