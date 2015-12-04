"""
This module contains all signals.
"""

from django.dispatch import Signal


# Signal that fires when a user is graded (in lms/courseware/grades.py)
GRADES_UPDATED = Signal(providing_args=["username", "grade_summary", "course_key", "deadline"])
