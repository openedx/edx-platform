"""
The utility methods and functions to help the djangoapp logic
"""
from datetime import datetime

from opaque_keys.edx.keys import CourseKey
import pytz

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import UserProfile

FAKE_COURSE_KEY = CourseKey.from_string('course-v1:fake+course+run')


def strip_course_id(path):
    """
    The utility function to help remove the fake
    course ID from the url path
    """
    course_id = unicode(FAKE_COURSE_KEY)
    return path.split(course_id)[0]


def display_incomplete_profile_notification(request):
    """
    Utility function to return if the incomplete profile
    notification should be displayed or not
    """
    days_passed_threshold = configuration_helpers.get_value(
        'DAYS_PASSED_TO_ALERT_PROFILE_INCOMPLETION',
        7,
    )
    user_profile = UserProfile.objects.get(user_id=request.user.id)
    joined = user_profile.user.date_joined
    current = datetime.now(pytz.utc)
    delta = current - joined

    if delta.days > days_passed_threshold:
        additional_fields = configuration_helpers.get_value(
            'FIELDS_TO_CHECK_PROFILE_COMPLETION',
            [],
        )
        for field_name in additional_fields:
            if not getattr(user_profile, field_name, None):
                return True

    return False
