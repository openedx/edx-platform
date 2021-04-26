"""
This file contains signal handlers for credentials-related functionality.
"""


from .tasks.v1.tasks import send_grade_if_interesting


def handle_grade_change(user, course_grade, course_key, **kwargs):
    """
    Notifies the Credentials IDA about certain grades it needs for its records, when a grade changes.
    """
    send_grade_if_interesting(
        user,
        course_key,
        None,
        None,
        course_grade.letter_grade,
        course_grade.percent,
        verbose=kwargs.get('verbose', False)
    )


def handle_cert_change(user, course_key, mode, status, **kwargs):
    """
    Notifies the Credentials IDA about certain grades it needs for its records, when a cert changes.
    """
    send_grade_if_interesting(user, course_key, mode, status, None, None, verbose=kwargs.get('verbose', False))
