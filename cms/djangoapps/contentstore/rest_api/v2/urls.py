"""Contenstore API v2 URLs."""

from django.urls import path

from cms.djangoapps.contentstore.rest_api.v2.views import HomePageCoursesViewV2, HomePageLibrariesViewV2

app_name = "v2"

urlpatterns = [
    path(
        "home/courses",
        HomePageCoursesViewV2.as_view(),
        name="courses",
    ),
    path(
        "home/libraries",
        HomePageLibrariesViewV2.as_view(),
        name="libraries",
    ),
]
