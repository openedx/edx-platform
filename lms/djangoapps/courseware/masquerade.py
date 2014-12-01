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

# The key used to store a user's course-level masquerade information in the Django session.
# The value is a dict from course keys to CourseMasquerade objects.
MASQUERADE_SETTINGS_KEY = 'masquerade_settings'


class CourseMasquerade(object):
    """
    Masquerade settings for a particular course.
    """
    def __init__(self, course_key, role='student', user_partition_id=None, group_id=None):
        self.course_key = course_key
        self.role = role
        self.user_partition_id = user_partition_id
        self.group_id = group_id


@require_POST
@login_required
@expect_json
def handle_ajax(request, course_key_string):
    """
    Handle AJAX posts to update the current user's masquerade for the specified course.
    The masquerade settings are stored in the Django session as a dict from course keys
    to CourseMasquerade objects.
    """
    course_key = CourseKey.from_string(course_key_string)
    masquerade_settings = request.session.get(MASQUERADE_SETTINGS_KEY, {})
    request_json = request.json
    role = request_json.get('role', 'student')
    user_partition_id = request_json.get('user_partition_id', None)
    group_id = request_json.get('group_id', None)
    masquerade_settings[course_key] = CourseMasquerade(
        course_key,
        role=role,
        user_partition_id=user_partition_id,
        group_id=group_id
    )
    request.session[MASQUERADE_SETTINGS_KEY] = masquerade_settings
    return JsonResponse()


def setup_masquerade(request, course_key, staff_access=False):
    """
    Sets up masquerading for the current user within the current request. The
    request's user is updated to have a 'masquerade_settings' attribute with
    the dict of all masqueraded settings if called from within a request context.
    The function then returns the CourseMasquerade object for the specified
    course key, or None if there isn't one.
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


def get_masquerading_group_info(user, course_key):
    """
    If the user is masquerading as belonging to a group, then this method returns
    two values: the id of the group, and the id of the user partition that the group
    belongs to. If the user is not masquerading as a group, then None is returned.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    if not course_masquerade:
        return None, None
    return course_masquerade.group_id, course_masquerade.user_partition_id
