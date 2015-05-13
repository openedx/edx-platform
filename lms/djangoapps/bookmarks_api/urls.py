"""
Discussion API URLs
"""
from django.conf.urls import include, patterns, url

from .views import BookmarksView


urlpatterns = patterns(
    "bookmarks_api",
    url(
        r"^v0/bookmarks/$",
        BookmarksView.as_view(),
        name="bookmarks"
    ),
)
