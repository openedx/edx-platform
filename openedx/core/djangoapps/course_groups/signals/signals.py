"""
Cohorts related signals.
"""

from django.dispatch import Signal

COHORT_MEMBERSHIP_UPDATED = Signal(providing_args=['user', 'course_key'])
