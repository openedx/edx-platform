
from opaque_keys.edx.keys import CourseKey, UsageKey

from xmodule.modulestore.django import modulestore
from bookmarks import serializers

from bookmarks.models import Bookmark


def get_bookmark(requested_user, usage_id, fields_to_add=None, serialized=True):
    """

    :param requested_user:
    :param usage_id:
    :param serialized:
    :return:
    """
    usage_key = UsageKey.from_string(usage_id)
    # usage_key's course_key may have an empty run property
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    bookmark = Bookmark.objects.get(usage_key=usage_key, user=requested_user)

    return serializers.BookmarkSerializer(bookmark, context={"fields": fields_to_add}).data if serialized else bookmark
