"""
Grades related signals.
"""
from django.dispatch import Signal


# Signal that indicates that a user's score for a problem has been updated.
# This signal is generated when a scoring event occurs either within the core
# platform or in the Submissions module. Note that this signal will be triggered
# regardless of the new and previous values of the score (i.e. it may be the
# case that this signal is generated when a user re-attempts a problem but
# receives the same score).
SCORE_CHANGED = Signal(
    providing_args=[
        'points_possible',  # Maximum score available for the exercise
        'points_earned',   # Score obtained by the user
        'user',  # User object
        'course_id',  # Unicode string representing the course
        'usage_id'  # Unicode string indicating the courseware instance
    ]
)


# Signal that indicates that a user's score for a subsection has been updated.
# This is a downstream signal of SCORE_CHANGED sent for each affected containing
# subsection.
SUBSECTION_SCORE_UPDATED = Signal(
    providing_args=[
        'course',  # Course object
        'user',  # User object
        'subsection_grade',  # SubsectionGrade object
    ]
)
