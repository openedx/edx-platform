from rest_framework import serializers
from .models import SiteConfiguration
from .utils import sass_to_dict, dict_to_sass


class SASSDictField(serializers.DictField):
    def to_internal_value(self, data):
        return dict_to_sass(data)

    def to_representation(self, value):
        return sass_to_dict(value)


class SiteConfigurationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='site.name', read_only=True)
    domain = serializers.CharField(source='site.domain', read_only=True)
    values = serializers.DictField()
    sass_variables = SASSDictField()
    page_elements = serializers.DictField()

    class Meta:
        model = SiteConfiguration
        fields = ('id', 'name', 'domain', 'values', 'sass_variables', 'page_elements')


class SiteConfigurationListSerializer(SiteConfigurationSerializer):
    class Meta(SiteConfigurationSerializer.Meta):
        fields = ('id', 'name', 'domain')
