
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from xmodule.modulestore.django import modulestore
from bookmarks_api import serializers

from bookmarks_api.models import Bookmark


def get_bookmark(requested_user, usage_key_string, serialized=True):
    try:
        usage_key = UsageKey.from_string(usage_key_string)
        # usage_key's course_key may have an empty run property
        usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    except InvalidKeyError:
        raise InvalidKeyError(u"Invalid usage id '{usage_key_string}'".format(usage_key_string=usage_key_string))
    try:
        bookmark = Bookmark.objects.get(usage_key=usage_key, user=requested_user)
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        raise ObjectDoesNotExist(u'The bookmark does not exist.')

    return serializers.BookmarkSerializer(bookmark).data if serialized else bookmark
