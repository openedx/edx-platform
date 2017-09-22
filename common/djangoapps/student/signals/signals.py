"""
Enrollment track related signals.
"""
from django.dispatch import Signal

ENROLLMENT_TRACK_UPDATED = Signal(providing_args=['user', 'course_key'])
