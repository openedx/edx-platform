"""
Models used to implement support related models in such as SSO History model
"""

from simple_history import register
from social_django.models import UserSocialAuth

# Registers UserSocialAuth with simple-django-history.
register(UserSocialAuth, app=__package__)
