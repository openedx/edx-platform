"""Filters for appsembler.tpa_admin viewsets
"""
import django_filters
from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig


class SAMLConfigurationFilter(django_filters.FilterSet):

    class Meta:
        model = SAMLConfiguration
        fields = ['site_id']


class SAMLProviderConfigFilter(django_filters.FilterSet):

    class Meta:
        model = SAMLProviderConfig
        fields = ['site_id']
