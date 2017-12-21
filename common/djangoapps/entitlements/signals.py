"""
Enrollment track related signals.
"""
from django.dispatch import Signal

REFUND_ENTITLEMENT = Signal(providing_args=['course_entitlement'])
