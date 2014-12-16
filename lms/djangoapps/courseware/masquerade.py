'''
---------------------------------------- Masquerade ----------------------------------------
Allow course staff to see a student or staff view of courseware.
Which kind of view has been selected is stored in the session state.
'''

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from util.json_request import expect_json, JsonResponse

from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)

MASQUERADE_SETTINGS_KEY = 'masquerade_settings'


class CourseMasquerade(object):
    """
    Masquerade settings for a particular course.
    """
    def __init__(self, course_key, role='student', group_id=None):
        self.course_key = course_key
        self.role = role
        self.group_id = group_id


@require_POST
@login_required
@expect_json
def handle_ajax(request, course_key_string):
    """
    Handle AJAX posts to update the current user's masquerade for the specified course.
    """
    course_key = CourseKey.from_string(course_key_string)
    masquerade_settings = request.session.get(MASQUERADE_SETTINGS_KEY, {})
    request_json = request.json
    role = request_json.get('role', 'student')
    group_id = request_json.get('group_id', None)
    masquerade_settings[course_key] = CourseMasquerade(course_key, role=role, group_id=group_id)
    request.session[MASQUERADE_SETTINGS_KEY] = masquerade_settings
    return JsonResponse()


def setup_masquerade(request, course_key, staff_access=False):
    """
    Setup masquerade identity (allows staff to view courseware as either staff or student)

    Uses request.session[MASQUERADE_SETTINGS_KEY] to store status of masquerading.
    Adds masquerade status to request.user, if masquerading active.
    Return string version of status of view (either 'staff' or 'student')
    """
    if request.user is None:
        return None

    if not settings.FEATURES.get('ENABLE_MASQUERADE', False):
        return None

    if not staff_access:  # can masquerade only if user has staff access to course
        return None

    masquerade_settings = request.session.get(MASQUERADE_SETTINGS_KEY, {})

    # Store the masquerade settings on the user so it can be accessed without the request
    request.user.masquerade_settings = masquerade_settings

    # Return the masquerade for the current course, or none if there isn't one
    return masquerade_settings.get(course_key, None)


def get_course_masquerade(user, course_key):
    """
    Returns the masquerade for the current user for the specified course. If no masquerade has
    been installed, then a default no-op masquerade is returned.
    """
    masquerade_settings = getattr(user, 'masquerade_settings', {})
    return masquerade_settings.get(course_key, None)


def get_masquerade_role(user, course_key):
    """
    Returns the role that the user is masquerading as, or None if no masquerade is in effect.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    return course_masquerade.role if course_masquerade else None


def is_masquerading_as_student(user, course_key):
    """
    Returns true if the user is a staff member masquerading as a student.
    """
    return get_masquerade_role(user, course_key) == 'student'


def get_masquerading_group_id(user, course_key):
    """
    Returns the id of the user partition group that the user is currently masquerading as,
    or None if none.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    return course_masquerade.group_id if course_masquerade else None
