"""
Helper functions used by both content_type_gating and course_duration_limits.
"""
import logging

from django.apps import apps

from xmodule.partitions.partitions import Group
from course_modes.models import CourseMode

# Studio generates partition IDs starting at 100. There is already a manually generated
# partition for Enrollment Track that uses ID 50, so we'll use 51.
CONTENT_GATING_PARTITION_ID = 51

CONTENT_TYPE_GATE_GROUP_IDS = {
    'limited_access': 1,
    'full_access': 2,
}
LIMITED_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['limited_access'], 'Limited-access Users')
FULL_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['full_access'], 'Full-access Users')
LOG = logging.getLogger(__name__)


def correct_modes_for_fbe(course_key, enrollment=None, user=None):
    """
    If CONTENT_TYPE_GATING is enabled use the following logic to determine whether
    enabled_for_enrollment should be false
    """
    if course_key is None:
        return True

    course_mode = apps.get_model('course_modes.CourseMode')
    modes = course_mode.modes_for_course(course_key, include_expired=True, only_selectable=False)
    modes_dict = {mode.slug: mode for mode in modes}

    # If there is no verified mode, FBE will not be enabled
    if not course_mode.has_verified_mode(modes_dict):
        return False

    if enrollment and user:
        mode_slug = enrollment.mode
        if enrollment.is_active:
            course_mode = course_mode.mode_for_course(
                course_key,
                mode_slug,
                modes=modes,
            )
            if course_mode is None:
                LOG.error(
                    u"User %s is in an unknown CourseMode '%s'"
                    u" for course %s. Granting full access to content for this user",
                    user.username,
                    mode_slug,
                    course_key,
                )
                return False

            if mode_slug != CourseMode.AUDIT:
                return False
    return True
