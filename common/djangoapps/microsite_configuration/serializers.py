from rest_framework import serializers
from .models import Microsite
from .utils import sass_to_dict, json_to_sass


class SASSDictField(serializers.DictField):
    child = serializers.CharField()

    def to_internal_value(self, data):
        return json_to_sass(data)

    def to_representation(self, value):
        return sass_to_dict(value)


class MicrositeSerializer(serializers.ModelSerializer):
    values = serializers.DictField()
    sass_variables = SASSDictField()

    class Meta:
        model = Microsite
        fields = ('id', 'key', 'values', 'sass_variables')
