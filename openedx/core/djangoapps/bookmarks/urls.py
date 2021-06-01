"""
URL routes for the bookmarks app.
"""


from django.conf import settings
from django.conf.urls import url

from .views import BookmarksDetailView, BookmarksListView

urlpatterns = [
    url(
        r'^v1/bookmarks/$',
        BookmarksListView.as_view(),
        name='bookmarks'
    ),
    url(
        r'^v1/bookmarks/{username},{usage_key}/$'.format(
            username=settings.USERNAME_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN
        ),
        BookmarksDetailView.as_view(),
        name='bookmarks_detail'
    ),
]
