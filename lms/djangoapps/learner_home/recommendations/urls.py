"""Learner home URL routing configuration"""

from django.urls import re_path

from lms.djangoapps.learner_home.recommendations import views

urlpatterns = [
    re_path(
        r"^courses/$",
        views.CourseRecommendationApiView.as_view(),
        name="courses",
    ),
]
