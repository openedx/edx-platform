"""Contenstore API v2 URLs."""
from django.conf import settings
from django.urls import path

from cms.djangoapps.contentstore.rest_api.v2.views import HomePageCoursesViewV2

app_name = "v2"

if settings.FEATURES.get('ENABLE_HOME_PAGE_COURSE_API_V2', False):
    urlpatterns = [
        path(
            "home/courses",
            HomePageCoursesViewV2.as_view(),
            name="courses",
        ),
    ]
else:
    urlpatterns = []
