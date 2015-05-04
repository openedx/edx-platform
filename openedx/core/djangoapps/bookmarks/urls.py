"""
Defines the URL routes for this app.
"""
from .views import BoomarksView

from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^v1/bookmarks$',
        BoomarksView.as_view(),
        name="course_bookmarks"
    ),
)
