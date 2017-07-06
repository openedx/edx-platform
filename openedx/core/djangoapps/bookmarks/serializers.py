"""
Serializers for Bookmarks.
"""
from rest_framework import serializers
from openedx.core.lib.api.serializers import CourseKeyField, UsageKeyField

from . import DEFAULT_FIELDS
from .models import Bookmark


class BookmarkSerializer(serializers.ModelSerializer):
    """
    Serializer for the Bookmark model.
    """
    id = serializers.SerializerMethodField()  # pylint: disable=invalid-name
    course_id = CourseKeyField(source='course_key')
    usage_id = UsageKeyField(source='usage_key')
    block_type = serializers.ReadOnlyField(source='usage_key.block_type')
    display_name = serializers.ReadOnlyField()
    path = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        try:
            fields = kwargs['context'].pop('fields', DEFAULT_FIELDS) or DEFAULT_FIELDS
        except KeyError:
            fields = DEFAULT_FIELDS
        # Instantiate the superclass normally
        super(BookmarkSerializer, self).__init__(*args, **kwargs)

        # Drop any fields that are not specified in the `fields` argument.
        required_fields = set(fields)
        all_fields = set(self.fields.keys())
        for field_name in all_fields - required_fields:
            self.fields.pop(field_name)

    class Meta(object):
        """ Serializer metadata. """
        model = Bookmark
        fields = (
            'id',
            'course_id',
            'usage_id',
            'block_type',
            'display_name',
            'path',
            'created',
        )

    def get_id(self, bookmark):
        """
        Return the REST resource id: {username,usage_id}.
        """
        return "{0},{1}".format(bookmark.user.username, bookmark.usage_key)

    def get_path(self, bookmark):
        """
        Serialize and return the path data of the bookmark.
        """
        path_items = [path_item._asdict() for path_item in bookmark.path]
        for path_item in path_items:
            path_item['usage_key'] = unicode(path_item['usage_key'])
        return path_items
