from student.models import CourseEnrollment
from course_modes.models import (
    get_cosmetic_verified_display_price
)
from courseware.date_summary import (
    VerifiedUpgradeDeadlineDate
)


def check_and_get_upgrade_link(user, course_id):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.
    """
    if user.is_authenticated():
        upgrade_data = VerifiedUpgradeDeadlineDate(None, user, course_id=course_id)
        if upgrade_data.is_enabled:
            return upgrade_data

    return None


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    enrollment_mode = None
    enrollment_time = None
    try:
        enrollment = CourseEnrollment.objects.get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, used the default None values

    upgrade_data = check_and_get_upgrade_link(user, course.id)

    return {
        'upgrade_link': upgrade_data and upgrade_data.link,
        'upgrade_price': unicode(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_data and upgrade_data.date,
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
    }
