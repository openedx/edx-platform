"""
Exceptions for Students and enrollment
"""


class UserEnrollmentError(Exception):
    """
    Raised to indicate an issue with a Student enrolling in a Course
    """


class UserAlreadyEnrolledError(UserEnrollmentError):
    """
    Raised to indicate a problem with enrollment due to the Student
    already being enrolled in the Course
    """
