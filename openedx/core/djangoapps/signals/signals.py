"""
This module contains all general use signals.
"""

from django.dispatch import Signal

# Signal that fires when a user is graded
COURSE_GRADE_CHANGED = Signal(providing_args=["user", "course_grade", "course_key", "deadline"])

# Signal that fires when a user is awarded a certificate in a course (in the certificates django app)
# TODO: runtime coupling between apps will be reduced if this event is changed to carry a username
# rather than a User object; however, this will require changes to the milestones and badges APIs
COURSE_CERT_CHANGED = Signal(providing_args=["user", "course_key", "mode", "status"])
COURSE_CERT_AWARDED = Signal(providing_args=["user", "course_key", "mode", "status"])

# Signal that indicates that a user has passed a course.
COURSE_GRADE_NOW_PASSED = Signal(
    providing_args=[
        'user',  # user object
        'course_id',  # course.id
    ]
)

# Signal that indicates that a user has become verified
LEARNER_NOW_VERIFIED = Signal(providing_args=['user'])
