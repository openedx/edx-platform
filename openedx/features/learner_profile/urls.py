"""
Defines URLs for the learner profile.
"""

from django.conf import settings
from django.conf.urls import url

from views.learner_achievements import LearnerAchievementsFragmentView
from openedx.features.learner_profile.views.learner_profile import learner_profile

urlpatterns = [
    url(
        r'^{username_pattern}$'.format(
            username_pattern=settings.USERNAME_PATTERN,
        ),
        learner_profile,
        name='learner_profile',
    ),
    url(
        r'^achievements$',
        LearnerAchievementsFragmentView.as_view(),
        name='openedx.learner_profile.learner_achievements_fragment_view',
    ),
]
