"""
This module contains all signals.
"""

from django.dispatch import Signal


# Signal that fires when a user is graded
COURSE_GRADE_CHANGED = Signal(providing_args=["user", "course_grade", "course_key", "deadline"])

# Signal that fires when a user is awarded a certificate in a course (in the certificates django app)
# TODO: runtime coupling between apps will be reduced if this event is changed to carry a username
# rather than a User object; however, this will require changes to the milestones and badges APIs
COURSE_CERT_AWARDED = Signal(providing_args=["user", "course_key", "mode", "status"])
