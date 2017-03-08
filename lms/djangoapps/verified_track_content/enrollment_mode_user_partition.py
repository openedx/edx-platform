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
    CourseMode.HONOR: Group(91111, CourseMode.HONOR),
    CourseMode.PROFESSIONAL: Group(91112, CourseMode.PROFESSIONAL),
    CourseMode.VERIFIED: Group(91113, CourseMode.VERIFIED),
    CourseMode.AUDIT: Group(91114, CourseMode.AUDIT),
    CourseMode.NO_ID_PROFESSIONAL_MODE: Group(91115, CourseMode.NO_ID_PROFESSIONAL_MODE),
    CourseMode.CREDIT_MODE: Group(91116, CourseMode.CREDIT_MODE)
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
    # HONOR = 'honor'
    # PROFESSIONAL = 'professional'
    # VERIFIED = "verified"
    # AUDIT = "audit"
    # NO_ID_PROFESSIONAL_MODE = "no-id-professional"
    # CREDIT_MODE = "credit"


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

        # cohort = get_cohort(user, course_key, use_cached=use_cached)
        # if cohort is None:
        #     # student doesn't have a cohort
        #     return None
        #
        # group_id, partition_id = get_group_info_for_cohort(cohort, use_cached=use_cached)
        # if partition_id is None:
        #     # cohort isn't mapped to any partition group.
        #     return None
        #
        # if partition_id != user_partition.id:
        #     # if we have a match but the partition doesn't match the requested
        #     # one it means the mapping is invalid.  the previous state of the
        #     # partition configuration may have been modified.
        #     log.warn(
        #         "partition mismatch in CohortPartitionScheme: %r",
        #         {
        #             "requested_partition_id": user_partition.id,
        #             "found_partition_id": partition_id,
        #             "found_group_id": group_id,
        #             "cohort_id": cohort.id,
        #         }
        #     )
        #     # fail silently
        #     return None
        #
        # try:
        #     return user_partition.get_group(group_id)
        # except NoSuchUserPartitionGroupError:
        #     # if we have a match but the group doesn't exist in the partition,
        #     # it means the mapping is invalid.  the previous state of the
        #     # partition configuration may have been modified.
        #     log.warn(
        #         "group not found in CohortPartitionScheme: %r",
        #         {
        #             "requested_partition_id": user_partition.id,
        #             "requested_group_id": group_id,
        #             "cohort_id": cohort.id,
        #         },
        #         exc_info=True
        #     )
        #     # fail silently
        #     return None

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



# def get_cohorted_user_partition(course):
#     """
#     Returns the first user partition from the specified course which uses the CohortPartitionScheme,
#     or None if one is not found. Note that it is currently recommended that each course have only
#     one cohorted user partition.
#     """
#     for user_partition in course.user_partitions:
#         if user_partition.scheme == CohortPartitionScheme:
#             return user_partition
#
#     return None


# TODO This should really going into common/djangoapps/student/.
# However, stevedore isn't able to find the student module since
# it's confused by the common directory magic.


# class EnrollmentTrackUserTag(UserTag):
#     """
#     UserTag class for enrollment tracks.
#     """
#     def __init__(self, course_mode):
#         self._course_mode = course_mode
#
#     @property
#     def name(self):
#         return self._course_mode.slug
#
#     @property
#     def display_name(self):
#         return unicode(self._course_mode.name)
#
#     @property
#     def description(self):
#         return _(u'Enrollment track for {}').format(self.display_name)
#
#     @property
#     def course_key(self):
#         """
#         Returns the course key associated with this tag.
#         """
#         return self._course_mode.course_id
#
#     @property
#     def users(self):
#         """
#         Returns the users associated with this tag.
#         """
#         return [enrollment.user for enrollment in CourseEnrollment.enrollments_for_mode(self.course_key, self.name)]


# class EnrollmentTrackUserTagProvider(UserTagProviderCourseContext):
#     """
#     UserTagProvider class for enrollment tracks.
#     Note: If VerifiedTrackCohortedCourse is enabled for a course, then
#         tagging is deferred to the CohortUserTagProvider in order to
#         avoid double-tagging based on enrollment tracks.
#     """
#     tag_type = EnrollmentTrackUserTag
#
#     @classmethod
#     def name(cls):
#         return u'openedx.enrollment.track'
#
#     @classmethod
#     def course_tags(cls, course_context, **kwargs):
#         if cls._is_course_using_cohort_instead(course_context):
#             return []
#         course_modes = CourseMode.modes_for_course(course_context.id)
#         return [EnrollmentTrackUserTag(course_mode) for course_mode in course_modes]
#
#     @classmethod
#     def get_users_for_course_tag(cls, tag, course_context=None, **kwargs):
#         if cls._is_course_using_cohort_instead(course_context):
#             return []
#         return tag.users
#
#     @classmethod
#     def get_course_tags_for_user(cls, user, course_context=None, **kwargs):
#         if cls._is_course_using_cohort_instead(course_context):
#             return []
#         mode_slug, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_context.id)
#         if mode_slug and is_active:
#             course_mode = CourseMode.mode_for_course(course_context.id, mode_slug)
#             if not course_mode:
#                 # TODO are all course-modes set up correctly on prod?
#                 # TODO on devstack, users are enrolled in non-existent modes
#                 course_mode = CourseMode.default_mode(course_context.id)
#             return [EnrollmentTrackUserTag(course_mode)]
#         else:
#             return []
#
#     @classmethod
#     def _is_course_using_cohort_instead(cls, course_context):
#         """
#         Returns whether the given course_context is using
#         verified-track cohorts and therefore shouldn't use
#         track-based user tags.
#         """
#         return VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_context.id)