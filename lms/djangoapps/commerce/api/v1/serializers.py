""" API v1 serializers. """
from rest_framework import serializers

from commerce.api.v1.models import Course
from course_modes.models import CourseMode


class CourseModeSerializer(serializers.ModelSerializer):
    """ CourseMode serializer. """
    name = serializers.CharField(source='mode_slug')
    price = serializers.IntegerField(source='min_price')

    def get_identity(self, data):
        try:
            return data.get('name', None)
        except AttributeError:
            return None

    class Meta(object):  # pylint: disable=missing-docstring
        model = CourseMode
        fields = ('name', 'currency', 'price', 'sku')


class CourseSerializer(serializers.Serializer):
    """ Course serializer. """
    id = serializers.CharField()  # pylint: disable=invalid-name
    modes = CourseModeSerializer(many=True, allow_add_remove=True)

    def restore_object(self, attrs, instance=None):
        if instance is None:
            return Course(attrs['id'], attrs['modes'])

        instance.update(attrs)
        return instance
