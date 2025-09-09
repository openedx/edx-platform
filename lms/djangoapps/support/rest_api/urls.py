"""
URL definitions for the support API.
"""

from django.urls import include, path

app_name = "lms.djangoapps.support.rest_api"

urlpatterns = [
    path("v1/", include("lms.djangoapps.support.rest_api.v1.urls", namespace="v1")),
]
