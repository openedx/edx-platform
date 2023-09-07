"""
API Serializers for content tagging org
"""

from rest_framework import serializers

from openedx_tagging.core.tagging.rest_api.v1.serializers import (
    TaxonomyListQueryParamsSerializer,
)

from organizations.models import Organization


class TaxonomyOrgListQueryParamsSerializer(TaxonomyListQueryParamsSerializer):
    """
    Serializer for the query params for the GET view
    """

    org = serializers.SlugRelatedField(
        slug_field="short_name",
        queryset=Organization.objects.all(),
        required=False,
    )
