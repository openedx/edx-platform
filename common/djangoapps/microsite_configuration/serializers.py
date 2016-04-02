from rest_framework import serializers
from .models import Microsite
from .utils import sass_to_dict, json_to_sass


class SASSJSONSerializerField(serializers.DictField):
    child = serializers.CharField()
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        return json_to_sass(data)
    def to_representation(self, value):
        return sass_to_dict(value)


class MicrositeSerializer(serializers.ModelSerializer):
    sass_variables = SASSJSONSerializerField()

    class Meta:
        model = Microsite
        fields = ('id', 'key', 'values', 'sass_variables')
