"""Learner home URL routing configuration"""

from django.urls import re_path

from lms.djangoapps.learner_home import mock_views, views

app_name = "learner_home"

# Learner Dashboard Routing
urlpatterns = [
    re_path(r"^init/?", views.InitializeView.as_view(), name="initialize"),
    re_path(
        r"^mock/init/?", mock_views.InitializeView.as_view(), name="mock_initialize"
    ),
    re_path(r"^recommendation/courses/$", views.CourseRecommendationApiView.as_view(), name="courses"),
]
