"""Learner home URL routing configuration"""

from django.urls import path

from lms.djangoapps.learner_home import mock_views, views

app_name = "learner_home"

# Learner Dashboard Routing
urlpatterns = [
    path("home/", views.dashboard_view, name="dashboard_view"),
    path("mock/home/", mock_views.dashboard_view),
]
