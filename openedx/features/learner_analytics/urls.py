"""
Url setup for learner analytics
"""
from django.conf.urls import url

from views import LearnerAnalyticsView


urlpatterns = [
    url(
        r'^$',
        LearnerAnalyticsView.as_view(),
        name='openedx.learner_analytics.dashboard',
    ),
]
