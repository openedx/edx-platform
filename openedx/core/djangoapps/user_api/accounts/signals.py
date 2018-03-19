"""
Django Signal related functionality for user_api accounts
"""

from django.dispatch import Signal

USER_RETIRE_MAILINGS = Signal(providing_args=["user"])
