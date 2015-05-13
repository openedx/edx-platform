"""
Bookmarks service.
"""
import logging

from django.core.exceptions import ObjectDoesNotExist

from xmodule.modulestore.exceptions import ItemNotFoundError

from . import DEFAULT_FIELDS, OPTIONAL_FIELDS, api

log = logging.getLogger(__name__)


class BookmarksService(object):
    """
    A service that provides access to the bookmarks API.
    """

    def __init__(self, user, **kwargs):
        super(BookmarksService, self).__init__(**kwargs)
        self._user = user

    def bookmarks(self, course_key):
        """
        Return a list of bookmarks for the course for the current user.

        Arguments:
            course_key: CourseKey of the course for which to retrieve the user's bookmarks for.

        Returns:
            list of dict:
        """
        return api.get_bookmarks(self._user, course_key=course_key, fields=DEFAULT_FIELDS + OPTIONAL_FIELDS)

    def is_bookmarked(self, usage_key):
        """
        Return whether the block has been bookmarked by the user.

        Arguments:
            usage_key: UsageKey of the block.

        Returns:
            Bool
        """
        try:
            api.get_bookmark(user=self._user, usage_key=usage_key)
        except ObjectDoesNotExist:
            log.error(u'Bookmark with usage_id: %s does not exist.', usage_key)
            return False

        return True

    def set_bookmarked(self, usage_key):
        """
        Adds a bookmark for the block.

        Arguments:
            usage_key: UsageKey of the block.

        Returns:
            Bool indicating whether the bookmark was added.
        """
        try:
            api.create_bookmark(user=self._user, usage_key=usage_key)
        except ItemNotFoundError:
            log.error(u'Block with usage_id: %s not found.', usage_key)
            return False

        return True

    def unset_bookmarked(self, usage_key):
        """
        Removes the bookmark for the block.

        Arguments:
            usage_key: UsageKey of the block.

        Returns:
            Bool indicating whether the bookmark was removed.
        """
        try:
            api.delete_bookmark(self._user, usage_key=usage_key)
        except ObjectDoesNotExist:
            log.error(u'Bookmark with usage_id: %s does not exist.', usage_key)
            return False

        return True
