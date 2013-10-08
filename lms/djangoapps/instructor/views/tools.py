"""
Tools for the instructor dashboard
"""
from django.contrib.auth.models import User

def strip_if_string(value):
    if isinstance(value, basestring):
        return value.strip()
    return value


def get_student_from_identifier(unique_student_identifier):
    """
    Gets a student object using either an email address or username.

    Returns the student object associated with `unique_student_identifier`

    Raises User.DoesNotExist if no user object can be found.
    """
    unique_student_identifier = strip_if_string(unique_student_identifier)
    if "@" in unique_student_identifier:
        student = User.objects.get(email=unique_student_identifier)
    else:
        student = User.objects.get(username=unique_student_identifier)
    return student
