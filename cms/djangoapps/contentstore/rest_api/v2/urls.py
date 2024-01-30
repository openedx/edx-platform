""" Contenstore API v2 URLs. """

from django.conf import settings
from django.urls import re_path, path

from .views import HomePageCoursesView

app_name = 'v2'

urlpatterns = [
    path(
        'home/courses',
        HomePageCoursesView.as_view(),
        name="courses"),
]
