"""
Cohorts related signals.
"""

from django.dispatch import Signal

# providing_args=['user', 'course_key']
COHORT_MEMBERSHIP_UPDATED = Signal()
