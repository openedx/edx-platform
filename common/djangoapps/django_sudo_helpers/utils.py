"""
Django sudo utils.
"""

from django.conf import settings

from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from track import contexts

from lms.djangoapps.courseware.access import get_user_role


def emit_sudo_event(request, user, region, next_url, social_auth=False):
    """
    Track django sudo requests.
    """
    try:
        course_key = CourseKey.from_string(region)
    except InvalidKeyError:
        course_key = None

    user_role = None
    if request.user.is_staff:
        user_role = "global_staff"
    elif course_key:
        user_role = get_user_role(user, course_key)
    elif region == "django_admin":
        user_role = region

    params = {
        "is_sudo": False,
        "success": False,
        "region": region,
        "user_id": user.id,
        "user_role": user_role,
        "next_url": next_url,
        "service": settings.SERVICE_VARIANT,
        "auth_type": "edx_login"
    }
    if social_auth:
        params["auth_type"] = "third_party_auth"

    if request.is_sudo(region):
        params['is_sudo'] = True
        params['success'] = True

    event_name = "edx.user.sudo.reauthenticated"

    if 'library-' in region:
        course_key = None
    context = contexts.course_context_from_course_id(course_key)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, params)
