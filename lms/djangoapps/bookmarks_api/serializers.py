from rest_framework import serializers
from openedx.core.djangoapps.user_api.serializers import ReadOnlyFieldsSerializerMixin

from .models import Bookmark


class BookmarkSerializer(serializers.HyperlinkedModelSerializer, ReadOnlyFieldsSerializerMixin):
    """
    Class that serializes the Bookmark model.
    """
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
        return "%s, %s" % (bookmark.user.username, bookmark.usage_key)
