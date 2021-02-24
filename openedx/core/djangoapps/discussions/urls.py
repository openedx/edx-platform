"""
Configure URL endpoints for the djangoapp
"""
from django.conf.urls import url

from .views import DiscussionsConfigurationView


urlpatterns = [
    url(
        r'^api/v0/(?P<course_key_string>.+)$',
        DiscussionsConfigurationView.as_view(),
        name='discussions',
    ),
]
