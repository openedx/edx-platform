"""
Bookmarks Python public API.
"""
# pylint: disable=unused-import

from .api_impl import (
    BookmarksLimitReachedError,
    get_bookmark,
    get_bookmarks,
    can_create_more,
    create_bookmark,
    delete_bookmark,
    delete_bookmarks,
)
from .services import BookmarksService
