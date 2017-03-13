"""
UserPartitionScheme for enrollment tracks.
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
# Note that course-specific display names will be set by the EnrollmentTrackUserPartition
ENROLLMENT_GROUPS = {
    CourseMode.HONOR: Group(91111, CourseMode.HONOR),
    CourseMode.PROFESSIONAL: Group(91112, CourseMode.PROFESSIONAL),
    CourseMode.VERIFIED: Group(91113, CourseMode.VERIFIED),
    CourseMode.AUDIT: Group(91114, CourseMode.AUDIT),
    CourseMode.NO_ID_PROFESSIONAL_MODE: Group(91115, CourseMode.NO_ID_PROFESSIONAL_MODE),
    CourseMode.CREDIT_MODE: Group(91116, CourseMode.CREDIT_MODE)
}


class EnrollmentTrackUserPartition(UserPartition):

    @property
    def groups(self):
        # Note that when the key is stored during course_module creation, it is the draft version.
        course_key = CourseKey.from_string(self.parameters["course_id"]).for_branch(None)
        all_groups = []
        for mode in CourseMode.all_modes_for_courses([course_key])[course_key]:
            group = ENROLLMENT_GROUPS[mode.slug]
            # group.name = mode.name
            all_groups.append(group)

        return all_groups


class EnrollmentTrackPartitionScheme(object):
    """
    This scheme uses learner enrollment tracks to map learners into partition groups.
    """

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition):
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
        # This work will be done in a future story (ADD ticket number).
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
                # TODO: is this the right thing to return of the learner is in a course mode that
                # doesn't actually exist for the course? Possible on devstack/sandbox.
                course_mode = CourseMode.default_mode(course_key)
            return ENROLLMENT_GROUPS[course_mode.slug]
        else:
            return None

    @classmethod
    def create_user_partition(cls, id, name, description, groups=None, parameters=None, active=True):
        return EnrollmentTrackUserPartition(id, name, description, [], cls, parameters, active)

    @classmethod
    def _is_course_using_cohort_instead(cls, course_key):
         """
         Returns whether the given course_context is using verified-track cohorts
         and therefore shouldn't use a track-based partition.
         """
         return VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key)
