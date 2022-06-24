"""Learner dashboard URL routing configuration"""

from django.urls import path
from lms.djangoapps.learner_dashboard import views

app_name = "learner_dashboard"

# Learner Dashboard Routing
urlpatterns = [
    path("", views.course_listing, name="course_listing_view")
]
