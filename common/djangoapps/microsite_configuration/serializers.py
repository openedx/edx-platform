from rest_framework import serializers
from .models import Microsite
from .utils import sass_to_dict, dict_to_sass


class SASSDictField(serializers.DictField):
    def to_internal_value(self, data):
        return dict_to_sass(data)

    def to_representation(self, value):
        return sass_to_dict(value)


class MicrositeSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()
    values = serializers.DictField()
    sass_variables = SASSDictField()
    page_elements = serializers.DictField()

    class Meta:
        model = Microsite
        fields = ('id', 'key', 'site', 'values', 'sass_variables', 'page_elements')


class MicrositeListSerializer(MicrositeSerializer):
    class Meta(MicrositeSerializer.Meta):
        fields = ('id', 'key', 'site')
