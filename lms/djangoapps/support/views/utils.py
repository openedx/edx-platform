"""
Various utility methods used by support app views.
"""
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig


def get_course_duration_info(course_key):
    """
    Fetch course duration information from database.
    """
    try:
        key = CourseKey.from_string(course_key)
        course = CourseOverview.objects.values('display_name').get(id=key)
        duration_config = CourseDurationLimitConfig.current(course_key=key)
        gating_config = ContentTypeGatingConfig.current(course_key=key)
        duration_enabled = CourseDurationLimitConfig.enabled_for_course(course_key=key)
        gating_enabled = ContentTypeGatingConfig.enabled_for_course(course_key=key)

        gating_dict = {
            'enabled': gating_enabled,
            'enabled_as_of': str(gating_config.enabled_as_of) if gating_config.enabled_as_of else 'N/A',
            'reason': gating_config.provenances['enabled'].value
        }
        duration_dict = {
            'enabled': duration_enabled,
            'enabled_as_of': str(duration_config.enabled_as_of) if duration_config.enabled_as_of else 'N/A',
            'reason': duration_config.provenances['enabled'].value
        }

        return {
            'course_id': course_key,
            'course_name': course.get('display_name'),
            'gating_config': gating_dict,
            'duration_config': duration_dict,
        }

    except (ObjectDoesNotExist, InvalidKeyError):
        return {}
