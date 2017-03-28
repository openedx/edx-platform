"""
User Tag Provider for enrollment tracks.
"""
from django.utils.translation import ugettext as _

from course_modes.models import CourseMode
from openedx.core.djangoapps.users.user_tags.contexts.course import UserTagProviderCourseContext
from openedx.core.djangoapps.users.user_tags.tag import UserTag
from student.models import CourseEnrollment
from verified_track_content.models import VerifiedTrackCohortedCourse


# TODO This should really going into common/djangoapps/student/.
# However, stevedore isn't able to find the student module since
# it's confused by the common directory magic.


class EnrollmentTrackUserTag(UserTag):
    """
    UserTag class for enrollment tracks.
    """
    def __init__(self, course_mode):
        self._course_mode = course_mode

    @property
    def name(self):
        return self._course_mode.slug

    @property
    def display_name(self):
        return unicode(self._course_mode.name)

    @property
    def description(self):
        return _(u'Enrollment track for {}').format(self.display_name)

    @property
    def course_key(self):
        """
        Returns the course key associated with this tag.
        """
        return self._course_mode.course_id

    @property
    def users(self):
        """
        Returns the users associated with this tag.
        """
        return [enrollment.user for enrollment in CourseEnrollment.enrollments_for_mode(self.course_key, self.name)]


class EnrollmentTrackUserTagProvider(UserTagProviderCourseContext):
    """
    UserTagProvider class for enrollment tracks.

    Note: If VerifiedTrackCohortedCourse is enabled for a course, then
        tagging is deferred to the CohortUserTagProvider in order to
        avoid double-tagging based on enrollment tracks.
    """
    tag_type = EnrollmentTrackUserTag

    @classmethod
    def name(cls):
        return u'openedx.enrollment.track'

    @classmethod
    def course_tags(cls, course_context, **kwargs):
        if cls._is_course_using_cohort_instead(course_context):
            return []
        course_modes = CourseMode.modes_for_course(course_context.id)
        return [EnrollmentTrackUserTag(course_mode) for course_mode in course_modes]

    @classmethod
    def get_users_for_course_tag(cls, tag, course_context=None, **kwargs):
        if cls._is_course_using_cohort_instead(course_context):
            return []
        return tag.users

    @classmethod
    def get_course_tags_for_user(cls, user, course_context=None, **kwargs):
        if cls._is_course_using_cohort_instead(course_context):
            return []
        mode_slug, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_context.id)
        if mode_slug and is_active:
            course_mode = CourseMode.mode_for_course(course_context.id, mode_slug)
            if not course_mode:
                # TODO are all course-modes set up correctly on prod?
                # TODO on devstack, users are enrolled in non-existent modes
                course_mode = CourseMode.default_mode(course_context.id)
            return [EnrollmentTrackUserTag(course_mode)]
        else:
            return []

    @classmethod
    def _is_course_using_cohort_instead(cls, course_context):
        """
        Returns whether the given course_context is using
        verified-track cohorts and therefore shouldn't use
        track-based user tags.
        """
        return VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_context.id)
