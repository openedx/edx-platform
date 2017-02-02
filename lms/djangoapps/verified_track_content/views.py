"""
View methods for verified track content.
"""

from util.json_request import expect_json, JsonResponse
from django.contrib.auth.decorators import login_required

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access

from verified_track_content.models import VerifiedTrackCohortedCourse


@expect_json
@login_required
def cohorting_settings(request, course_key_string):
    """
    The handler for verified track cohorting requests.
    This will raise 404 if user is not staff.

    Returns a JSON representation of whether or not the course has verified track cohorting enabled.
    The "verified_cohort_name" field will only be present if "enabled" is True.

    Example:
        >>> example = {
        >>>               "enabled": True,
        >>>               "verified_cohort_name" : "Micromasters"
        >>>           }
    """
    course_key = CourseKey.from_string(course_key_string)
    get_course_with_access(request.user, 'staff', course_key)

    settings = {}
    verified_track_cohort_enabled = VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key)
    settings['enabled'] = verified_track_cohort_enabled
    if verified_track_cohort_enabled:
        settings['verified_cohort_name'] = VerifiedTrackCohortedCourse.verified_cohort_name_for_course(course_key)

    return JsonResponse(settings)
