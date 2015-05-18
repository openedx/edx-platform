"""
Unit Bookmark API URLs
"""

from django.conf import settings
from django.conf.urls import include, patterns, url

from .views import BookmarksView, BookmarksDetailView

USERNAME_PATTERN = '(?P<username>[\w.@+-]+)'

urlpatterns = patterns(
    "bookmarks",
    url(
        r"^v0/bookmarks/$",
        BookmarksView.as_view(),
        name="bookmarks"
    ),
    url(
        r"^v0/bookmarks/{username},{usage_key}/$".format(
            username=USERNAME_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN
        ),
        BookmarksDetailView.as_view(),
        name="bookmarks_detail"
    ),
)
