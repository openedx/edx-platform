"""
Provides Python APIs exposed from Bulk Email models.
"""


from lms.djangoapps.bulk_email.models import BulkEmailFlag, CourseAuthorization, DisabledCourse, Optout


def is_user_opted_out_for_course(user, course_id):
    """
    Arguments:
        user: user whose opt out status is to be returned
        course_id (CourseKey): id of the course

    Returns:
        bool: True if user has opted out of e-mails for the course
        associated with course_id, False otherwise.
    """
    return Optout.is_user_opted_out_for_course(user, course_id)


def is_bulk_email_feature_enabled(course_id=None):
    """
    Looks at the currently active configuration model to determine whether the bulk email feature is available.

    Arguments:
        course_id (string; optional): the course id of the course

    Returns:
        bool: True or False, depending on the following:
            If the flag is not enabled, the feature is not available.
            If the flag is enabled, course-specific authorization is required, and the course_id is either not provided
                or not authorixed, the feature is not available.
            If the flag is enabled, course-specific authorization is required, and the provided course_id is authorized,
                the feature is available.
            If the flag is enabled and course-specific authorization is not required, the feature is available.
    """
    return BulkEmailFlag.feature_enabled(course_id)


def is_bulk_email_enabled_for_course(course_id):
    """
    Arguments:
        course_id: the course id of the course

    Returns:
        bool: True if the Bulk Email feature is enabled for the course
        associated with the course_id; False otherwise
    """
    return CourseAuthorization.instructor_email_enabled(course_id)


def is_bulk_email_disabled_for_course(course_id):
    """
    Arguments:
        course_id: the course id of the course

    Returns:
        bool: True if the Bulk Email feature is disabled for the course
        associated with the course_id; False otherwise
    """
    return DisabledCourse.instructor_email_disabled_for_course(course_id)
