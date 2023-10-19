"""
Defines URLs for the learner profile.
"""


from django.conf import settings
from django.urls import path, re_path

from openedx.features.learner_profile.views.learner_profile import learner_profile

from .views.learner_achievements import LearnerAchievementsFragmentView

urlpatterns = [
    re_path(
        r'^{username_pattern}$'.format(
            username_pattern=settings.USERNAME_PATTERN,
        ),
        learner_profile,
        name='learner_profile',
    ),
    path('achievements', LearnerAchievementsFragmentView.as_view(),
         name='openedx.learner_profile.learner_achievements_fragment_view',
         ),
]
