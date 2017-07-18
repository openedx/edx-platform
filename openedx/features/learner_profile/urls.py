"""
Defines URLs for the learner profile.
"""

from django.conf import settings
from django.conf.urls import url

urlpatterns = [
    url(
        r'^{username_pattern}$'.format(
            username_pattern=settings.USERNAME_PATTERN,
        ),
        'openedx.features.learner_profile.views.learner_profile',
        name='learner_profile',
    ),
]
