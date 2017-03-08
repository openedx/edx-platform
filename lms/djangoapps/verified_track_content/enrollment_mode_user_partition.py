"""
User Tag Provider for enrollment tracks.
"""
from django.utils.translation import ugettext as _

from courseware.masquerade import (  # pylint: disable=import-error
    get_course_masquerade,
    get_masquerading_group_info,
    is_masquerading_as_specific_student,
)
from course_modes.models import CourseMode
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from verified_track_content.models import VerifiedTrackCohortedCourse
from xmodule.partitions.partitions import NoSuchUserPartitionGroupError, Group, UserPartition

# TODO: how to make sure IDs are unique across all partitions?
# TODO: show display names instead of slugs
ENROLLMENT_GROUPS = {
    CourseMode.HONOR: Group(91111, _('Honor')),
    CourseMode.PROFESSIONAL: Group(91112, _('Professional')),
    CourseMode.VERIFIED: Group(91113, _('Verified')),
    CourseMode.AUDIT: Group(91114, _('Audit')),
    CourseMode.NO_ID_PROFESSIONAL_MODE: Group(91115, _('No ID Professional')),
    CourseMode.CREDIT_MODE: Group(91116, _('Credit'))
}


class EnrollmentModeUserPartition(UserPartition):

    # TODO: what about persistence? Will course_id have to be moved up into UserParititon?
    @property
    def groups(self):
        course_key = CourseKey.from_string(self.parameters["course_id"])
        all_groups = []
        for mode in CourseMode.all_modes_for_courses([course_key])[course_key]:
            all_groups.append(ENROLLMENT_GROUPS[mode.slug])

        return all_groups


class EnrollmentModePartitionScheme(object):
    """
    This scheme uses learners' enrollment modes to map them into partition groups.
    """

    # pylint: disable=unused-argument
    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition, track_function=None, use_cached=True):
        """
        Returns the Group from the specified user partition to which the user
        is assigned, via enrollment mode.
        """
        # First, check if we have to deal with masquerading.
        # If the current user is masquerading as a specific student, use the
        # same logic as normal to return that student's group. If the current
        # user is masquerading as a generic student in a specific group, then
        # return that group.
        # TODO: this was copied from CohortPartitionScheme, may need some changes
        if get_course_masquerade(user, course_key) and not is_masquerading_as_specific_student(user, course_key):
            group_id, user_partition_id = get_masquerading_group_info(user, course_key)
            if user_partition_id == user_partition.id and group_id is not None:
                try:
                    return user_partition.get_group(group_id)
                except NoSuchUserPartitionGroupError:
                    return None
            # The user is masquerading as a generic student. We can't show any particular group.
            return None

        if cls._is_course_using_cohort_instead(course_key):
            return None
        mode_slug, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_key)
        if mode_slug and is_active:
            course_mode = CourseMode.mode_for_course(course_key, mode_slug)
            if not course_mode:
                # TODO are all course-modes set up correctly on prod?
                # TODO on devstack, users are enrolled in non-existent modes
                course_mode = CourseMode.default_mode(course_key)
            return ENROLLMENT_GROUPS[course_mode.slug]
        else:
            return None

    @classmethod
    def create_user_partition(cls, id, name, description, groups=None, parameters=None, active=None):
        return EnrollmentModeUserPartition(id, name, description, [], cls, parameters, active)


    @classmethod
    def _is_course_using_cohort_instead(cls, course_key):
         """
         Returns whether the given course_context is using
         verified-track cohorts and therefore shouldn't useN
         track-based user tags.
         """
         return VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key)
