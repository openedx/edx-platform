"""
UserPartitionScheme for enrollment tracks.
"""
from courseware.masquerade import (  # pylint: disable=import-error
    get_course_masquerade,
    get_masquerading_group_info,
    is_masquerading_as_specific_student,
)
from course_modes.models import CourseMode, EnrollmentMode
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.verified_track_content.models import VerifiedTrackCohortedCourse
from xmodule.partitions.partitions import NoSuchUserPartitionGroupError, Group, UserPartition


# EnrollmentMode IDs will be low integers (starting at 0), which is important so that they
# do not overlap with Groups in the CohortUserPartition or the RandomUserPartitionScheme
# (CMS' course_group_config uses a minimum value of 100 for all generated IDs).
ENROLLMENT_GROUP_IDS = {}
try:
    for enrollment_mode in EnrollmentMode.objects.all():
        ENROLLMENT_GROUP_IDS[enrollment_mode.mode_slug] = enrollment_mode.id
except:  # pylint: disable=bare-except
    pass

if not ENROLLMENT_GROUP_IDS:
    # The entries in this table are populated in a migration file, and migration files do not
    # run as part of unit tests. Therefore, for tests hard-code the modes.
    ENROLLMENT_GROUP_IDS = {
        CourseMode.AUDIT: 1,
        CourseMode.VERIFIED: 2,
        CourseMode.PROFESSIONAL: 3,
        CourseMode.NO_ID_PROFESSIONAL_MODE: 4,
        CourseMode.CREDIT_MODE: 5,
        CourseMode.HONOR: 6
    }


class EnrollmentTrackUserPartition(UserPartition):
    """
    Extends UserPartition to support dynamic groups pulled from the current course Enrollment tracks.
    """

    @property
    def groups(self):
        """
        Return the groups (based on CourseModes) for the course associated with this
        EnrollmentTrackUserPartition instance.
        """
        course_key = CourseKey.from_string(self.parameters["course_id"])

        if is_course_using_cohort_instead(course_key):
            return []

        all_groups = []
        for mode in CourseMode.modes_for_course(course_key, include_expired=True, only_selectable=False):
            group = Group(ENROLLMENT_GROUP_IDS[mode.slug], unicode(mode.name))
            all_groups.append(group)

        return all_groups

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the partition, with an empty array for
            `groups` because it is dynamic based on the current course modes.
        """
        return {
            "id": self.id,
            "name": self.name,
            "scheme": self.scheme.name,
            "description": self.description,
            "parameters": self.parameters,
            "groups": [],  # Do not persist groups because they are dynamic.
            "active": bool(self.active),
            "version": UserPartition.VERSION
        }


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
        # NOTE: masquerade code was copied from CohortPartitionScheme, and it may need
        # some changes (or if not, code should be refactored out and shared).
        # This work will be done in a future story TNL-6739.

        # First, check if we have to deal with masquerading.
        # If the current user is masquerading as a specific student, use the
        # same logic as normal to return that student's group. If the current
        # user is masquerading as a generic student in a specific group, then
        # return that group.
        if get_course_masquerade(user, course_key) and not is_masquerading_as_specific_student(user, course_key):
            group_id, user_partition_id = get_masquerading_group_info(user, course_key)
            if user_partition_id == user_partition.id and group_id is not None:
                try:
                    return user_partition.get_group(group_id)
                except NoSuchUserPartitionGroupError:
                    return None
            # The user is masquerading as a generic student. We can't show any particular group.
            return None

        if is_course_using_cohort_instead(course_key):
            return None
        mode_slug, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_key)
        if mode_slug and is_active:
            course_mode = CourseMode.mode_for_course(course_key, mode_slug)
            if not course_mode:
                course_mode = CourseMode.DEFAULT_MODE
            return Group(ENROLLMENT_GROUP_IDS[course_mode.slug], unicode(course_mode.name))
        else:
            return None

    @classmethod
    def create_user_partition(cls, id, name, description, groups=None, parameters=None, active=True):  # pylint: disable=redefined-builtin, invalid-name, unused-argument
        """
        Create a custom UserPartition to support dynamic groups.

        A Partition has an id, name, scheme, description, parameters, and a list
        of groups. The id is intended to be unique within the context where these
        are used. (e.g., for partitions of users within a course, the ids should
        be unique per-course). The scheme is used to assign users into groups.
        The parameters field is used to save extra parameters e.g., location of
        the course ID for this partition scheme.

        Partitions can be marked as inactive by setting the "active" flag to False.
        Any group access rule referencing inactive partitions will be ignored
        when performing access checks.
        """
        return EnrollmentTrackUserPartition(id, name, description, [], cls, parameters, active)


def is_course_using_cohort_instead(course_key):
    """
    Returns whether the given course_context is using verified-track cohorts
    and therefore shouldn't use a track-based partition.
    """
    return VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key)
