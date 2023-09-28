"""
Configure URL endpoints for the djangoapp
"""
from django.urls import re_path
from django.conf import settings

from .views import CombinedDiscussionsConfigurationView, DiscussionsConfigurationSettingsView, DiscussionsProvidersView


urlpatterns = [
    re_path(
        fr'^v0/{settings.COURSE_KEY_PATTERN}$',
        CombinedDiscussionsConfigurationView.as_view(),
        name='discussions',
    ),
    re_path(
        fr'^v0/course/{settings.COURSE_KEY_PATTERN}/settings$',
        DiscussionsConfigurationSettingsView.as_view(),
        name='discussions-settings',
    ),
    re_path(
        fr'^v0/course/{settings.COURSE_KEY_PATTERN}/providers$',
        DiscussionsProvidersView.as_view(),
        name='discussions-providers',
    ),
]
