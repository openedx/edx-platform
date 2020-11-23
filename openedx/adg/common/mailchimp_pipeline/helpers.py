"""
Helper methods for Mailchimp pipeline
"""
from student.models import CourseEnrollment


def get_enrollment_course_names_and_short_ids_by_user(user):
    """
    Get comma separated course names and short ids, for all enrolled courses.

    Args:
        user (user object): User model object

    Returns:
        Tuple of comma separated course short ids and course names
    """
    enrollments = CourseEnrollment.enrollments_for_user(user).values_list(
        'course__course_meta__short_id', 'course__display_name'
    )

    if not enrollments:
        return '', ''

    short_ids, display_names = zip(*enrollments)
    return ','.join(map(str, short_ids)), ','.join(display_names)
