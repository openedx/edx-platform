"""
A service-like user_info interface.  Could be made into an http API later, but for now
just in-process.  Exposes global and per-course key-value pairs for users.

Implementation note:
Stores global metadata using the UserPreference model, and per-course metadata using the
UserCourseMetadata model.
"""

from django.contrib.auth.models import User
from user_api.models import UserCourseTags


def get_course_tag(user_id, course_id, key):
    """
    Gets the value of the user's course tag for the specified key in the specified
    course_id.

    Args:
        user_id: an id into the User table
        course_id: course identifier (string)
        key: arbitrary (<=255 char string)

    Returns:
        string value, or None if there is no value saved
    """
    try:
       record = UserCourseTags.objects.get(
           user__id=user_id,
           course_id=course_id,
           key=key)

       return record.value
    except UserCourseTags.DoesNotExist:
        return None


def set_course_tag(user_id, course_id, key, value):
    """
    Sets the value of the user's course tag for the specified key in the specified
    course_id.  Overwrites any previous value.

    The intention is that the values are fairly short, as they will be included in all
    analytics events about this user.

    Args:
        user_id: an id into the User table
        course_id: course identifier (string)
        key: arbitrary (<=255 char string)
        value: arbitrary string
    """

    record, created = UserCourseTags.objects.get_or_create(
        user__id=user_id,
        course_id=course_id,
        key=key,
        defaults={'value': value,
                  # Have to include this here, because get_or_create does not
                  # automatically pass through params with '__' in them
                  'user_id': user_id})

    if not created:
        # need to update the value
       record.value = value
       record.save()

    # TODO: There is a risk of IntegrityErrors being thrown here given
    # simultaneous calls from many processes.  Handle by retrying after a short delay?
