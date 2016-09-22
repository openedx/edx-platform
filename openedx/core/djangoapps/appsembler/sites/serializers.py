from django.contrib.sites.models import Site
from rest_framework import serializers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from .utils import sass_to_dict, dict_to_sass, bootstrap_site


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


class SiteSerializer(serializers.ModelSerializer):
    configuration = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Site
        fields = ('id', 'name', 'domain', 'configuration')

    def create(self, validated_data):
        site = super(SiteSerializer, self).create(validated_data)
        site = bootstrap_site(site)
        return site
