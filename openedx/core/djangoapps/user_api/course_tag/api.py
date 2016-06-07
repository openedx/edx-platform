"""
A service-like user_info interface.  Could be made into an http API later, but for now
just in-process.  Exposes global and per-course key-value pairs for users.

Implementation note:
Stores global metadata using the UserPreference model, and per-course metadata using the
UserCourseTag model.
"""

from ..models import UserCourseTag

# Scopes
# (currently only allows per-course tags.  Can be expanded to support
# global tags (e.g. using the existing UserPreferences table))
COURSE_SCOPE = 'course'


def get_course_tag(user, course_id, key):
    """
    Gets the value of the user's course tag for the specified key in the specified
    course_id.

    Args:
        user: the User object for the course tag
        course_id: course identifier (string)
        key: arbitrary (<=255 char string)

    Returns:
        string value, or None if there is no value saved
    """
    try:
        record = UserCourseTag.objects.get(
            user=user,
            course_id=course_id,
            key=key)

        return record.value
    except UserCourseTag.DoesNotExist:
        return None


def set_course_tag(user, course_id, key, value):
    """
    Sets the value of the user's course tag for the specified key in the specified
    course_id.  Overwrites any previous value.

    The intention is that the values are fairly short, as they will be included in all
    analytics events about this user.

    Args:
        user: the User object
        course_id: course identifier (string)
        key: arbitrary (<=255 char string)
        value: arbitrary string
    """
    # pylint: disable=fixme
    # TODO: There is a risk of IntegrityErrors being thrown here given
    # simultaneous calls from many processes. Handle by retrying after
    # a short delay?

    record, _ = UserCourseTag.objects.get_or_create(
        user=user,
        course_id=course_id,
        key=key)

    record.value = value
    record.save()
