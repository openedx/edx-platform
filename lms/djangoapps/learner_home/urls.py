"""Learner home URL routing configuration"""

from django.urls import path

from lms.djangoapps.learner_home import mock_views, views

app_name = "learner_home"

# Learner Dashboard Routing
urlpatterns = [
    path("init", views.InitializeView.as_view(), name="initialize"),
    path("mock/init", mock_views.InitializeView.as_view(), name="mock_initialize"),
]
