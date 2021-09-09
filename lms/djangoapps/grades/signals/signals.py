"""
Grades related signals.
"""


from django.dispatch import Signal

# Signal that indicates that a user's grade for a course has been updated.
# This is a downstream signal of SUBSECTION_SCORE_CHANGED.

# Signal that indicates that a user's raw score for a problem has been updated.
# This signal is generated when a scoring event occurs within the core
# platform. Note that this signal will be triggered
# regardless of the new and previous values of the score (i.e. it may be the
# case that this signal is generated when a user re-attempts a problem but
# receives the same score).
PROBLEM_RAW_SCORE_CHANGED = Signal()

# Signal that indicates that a user's weighted score for a problem has been updated.
# This signal is generated when a scoring event occurs in the Submissions module
# or a PROBLEM_RAW_SCORE_CHANGED event is handled in the core platform.
# Note that this signal will be triggered
# regardless of the new and previous values of the score (i.e. it may be the
# case that this signal is generated when a user re-attempts a problem but
# receives the same score).
PROBLEM_WEIGHTED_SCORE_CHANGED = Signal()


# Signal that indicates that a user's score for a problem has been published
# for possible persistence and update.  Typically, most clients should listen
# to the PROBLEM_WEIGHTED_SCORE_CHANGED signal instead, since that is signalled
# only after the problem's score is changed.
SCORE_PUBLISHED = Signal()


# Signal that indicates that a user's score for a subsection has been updated.
# This is a downstream signal of PROBLEM_WEIGHTED_SCORE_CHANGED sent for each
# affected containing subsection.
SUBSECTION_SCORE_CHANGED = Signal()

# Signal that indicates that a user's score for a subsection has been overridden.
# This signal is generated when a user's exam attempt state is set to rejected or
# to verified from rejected. This signal may also be sent by any other client
# using the GradesService to override subsections in the future.
SUBSECTION_OVERRIDE_CHANGED = Signal()


# This Signal indicates that the user has received a passing grade in the course for the first time.
# Any subsequent grade changes that may vary the passing/failing status will not re-trigger this event.
# Emits course grade passed first time event
COURSE_GRADE_PASSED_FIRST_TIME = Signal()
