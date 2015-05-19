"""
File contains bookmark api method(s).
"""
from opaque_keys.edx.keys import CourseKey, UsageKey

from xmodule.modulestore.django import modulestore
from bookmarks.serializers import BookmarkSerializer

from bookmarks.models import Bookmark


def get_bookmark(requested_user, usage_id, fields_to_add=None, serialized=True):
    """Returns bookmark object or JSON response.

    Args:
        requesting_user (User): The user requesting the bookmark.
        fields_to_add (list): List of fields to return for a bookmark.
        usage_id (str): The usage id of an Xblock.
        serialized (Bool): Decides to return object or json.

    Returns:
         A dict or object containing bookmark data.

    Raises:
         InvalidKey: If given usage_id is not in proper format.
         ObjectDoesNotExit: If Bookmark object does not exist.
    """

    usage_key = UsageKey.from_string(usage_id)
    # usage_key's course_key may have an empty run property
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    bookmark = Bookmark.objects.get(usage_key=usage_key, user=requested_user)

    return BookmarkSerializer(bookmark, context={"fields": fields_to_add}).data if serialized else bookmark
