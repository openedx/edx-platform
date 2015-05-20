"""
Bookmarks Python API.
"""
from eventtracking import tracker
from . import DEFAULT_FIELDS, OPTIONAL_FIELDS
from .models import Bookmark
from .serializers import BookmarkSerializer


def get_bookmark(user, usage_key, fields=None):
    """
    Return data for a bookmark.

    Arguments:
        user (User): The user of the bookmark.
        usage_key (UsageKey): The usage_key of the bookmark.
        fields (list): List of field names the data should contain (optional).

    Returns:
        Dict.

    Raises:
        ObjectDoesNotExist: If a bookmark with the parameters does not exist.
    """
    bookmarks_queryset = Bookmark.objects

    if len(set(fields or []) & set(OPTIONAL_FIELDS)) > 0:
        bookmarks_queryset = bookmarks_queryset.select_related('user', 'xblock_cache')
    else:
        bookmarks_queryset = bookmarks_queryset.select_related('user')

    bookmark = bookmarks_queryset.get(user=user, usage_key=usage_key)
    return BookmarkSerializer(bookmark, context={'fields': fields}).data


def get_bookmarks(user, course_key=None, fields=None, serialized=True):
    """
    Return data for bookmarks of a user.

    Arguments:
        user (User): The user of the bookmarks.
        course_key (CourseKey): The course_key of the bookmarks (optional).
        fields (list): List of field names the data should contain (optional).
            N/A if serialized is False.
        serialized (bool): Whether to return a queryset or a serialized list of dicts.
            Default is True.

    Returns:
         List of dicts if serialized is True else queryset.
    """
    bookmarks_queryset = Bookmark.objects.filter(user=user)

    if course_key:
        bookmarks_queryset = bookmarks_queryset.filter(course_key=course_key)

    if len(set(fields or []) & set(OPTIONAL_FIELDS)) > 0:
        bookmarks_queryset = bookmarks_queryset.select_related('user', 'xblock_cache')
    else:
        bookmarks_queryset = bookmarks_queryset.select_related('user')

    bookmarks_queryset = bookmarks_queryset.order_by('-created')

    if serialized:
        return BookmarkSerializer(bookmarks_queryset, context={'fields': fields}, many=True).data

    return bookmarks_queryset


def create_bookmark(user, usage_key):
    """
    Create a bookmark.

    Arguments:
        user (User): The user of the bookmark.
        usage_key (UsageKey): The usage_key of the bookmark.

    Returns:
         Dict.

    Raises:
        ItemNotFoundError: If no block exists for the usage_key.
    """
    bookmark, created = Bookmark.create({
        'user': user,
        'usage_key': usage_key
    })
    if created:
        _track_event('edx.bookmark.added', bookmark)
    return BookmarkSerializer(bookmark, context={'fields': DEFAULT_FIELDS + OPTIONAL_FIELDS}).data


def delete_bookmark(user, usage_key):
    """
    Delete a bookmark.

    Arguments:
        user (User): The user of the bookmark.
        usage_key (UsageKey): The usage_key of the bookmark.

    Returns:
         Dict.

    Raises:
        ObjectDoesNotExist: If a bookmark with the parameters does not exist.
    """
    bookmark = Bookmark.objects.get(user=user, usage_key=usage_key)
    bookmark.delete()
    _track_event('edx.bookmark.removed', bookmark)


def _track_event(event_name, bookmark):
    """
    Emit events for a bookmark.

    Arguments:
        event_name: name of event to track
        bookmark: Bookmark object
    """
    tracker.emit(
        event_name,
        {
            'course_id': unicode(bookmark.course_key),
            'bookmark_id': bookmark.resource_id,
            'component_type': bookmark.usage_key.block_type,
            'component_usage_id': unicode(bookmark.usage_key),
        }
    )
