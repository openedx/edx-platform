"""
Serializer file for Bookmarks.
"""
from rest_framework import serializers
from .views import DEFAULT_FIELDS

from .models import Bookmark


class BookmarkSerializer(serializers.ModelSerializer):
    """
    Class that serializes the Bookmark model.
    """
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        try:
            fields = kwargs['context'].pop('fields', [])
        except KeyError:
            fields = DEFAULT_FIELDS
        # Instantiate the superclass normally
        super(BookmarkSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    id = serializers.SerializerMethodField('get_id')
    path = serializers.Field(source='path')
    usage_id = serializers.Field(source='usage_key')
    course_id = serializers.Field(source='course_key')

    class Meta:
        model = Bookmark
        fields = ("id", "course_id", "usage_id", "display_name", "path", "created")

    def get_id(self, bookmark):
        """
        Gets the bookmark id.
        """
        return "%s,%s" % (bookmark.user.username, bookmark.usage_key)
