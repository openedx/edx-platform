"""
Cohorts related signals.
"""
from __future__ import absolute_import
from django.dispatch import Signal

COHORT_MEMBERSHIP_UPDATED = Signal(providing_args=['user', 'course_key'])
