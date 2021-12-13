"""
Configure URL endpoints for the djangoapp
"""

from .views import DiscussionsConfigurationView
from django.urls import path


urlpatterns = [
    path('v0/<path:course_key_string>', DiscussionsConfigurationView.as_view(),
        name='discussions',
    ),
]
