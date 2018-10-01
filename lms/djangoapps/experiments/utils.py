from student.models import CourseEnrollment
from django_comment_common.models import Role
from courseware.access import has_staff_access_to_preview_mode
from course_modes.models import (
    get_cosmetic_verified_display_price
)
from courseware.date_summary import (
    verified_upgrade_deadline_link, verified_upgrade_link_is_valid
)
from openedx.core.djangoapps.course_groups.cohorts import get_cohort


def check_and_get_upgrade_link_and_date(user, enrollment=None, course=None):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.
    """
    if enrollment is None and course is None:
        raise ValueError("Must specify either an enrollment or a course")

    if enrollment:
        if course is None:
            course = enrollment.course
        elif enrollment.course_id != course.id:
            raise ValueError("{} refers to a different course than {} which was supplied".format(
                enrollment, course
            ))

        if enrollment.user_id != user.id:
            raise ValueError("{} refers to a different user than {} which was supplied".format(
                enrollment, user
            ))

    if enrollment is None:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)

    if user.is_authenticated and verified_upgrade_link_is_valid(enrollment):
        return (
            verified_upgrade_deadline_link(user, course),
            enrollment.upgrade_deadline
        )

    return (None, None)


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    enrollment_mode = None
    enrollment_time = None
    enrollment = None
    try:
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, used the default None values

    upgrade_link, upgrade_date = check_and_get_upgrade_link_and_date(user, enrollment, course)
    has_staff_access = has_staff_access_to_preview_mode(user, course.id)
    forum_roles = []
    if user.is_authenticated:
        forum_roles = list(Role.objects.filter(users=user, course_id=course.id).values_list('name').distinct())
    cohort_name = get_cohort(user, course.id, assign=False, use_cached=True)
    if cohort_name:
        cohort_name = cohort_name.name

    return {
        'upgrade_link': upgrade_link,
        'upgrade_price': unicode(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
        'has_staff_access': has_staff_access,
        'forum_roles': forum_roles,
        'cohort_name': cohort_name
    }
