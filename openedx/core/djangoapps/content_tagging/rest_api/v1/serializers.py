"""
API Serializers for content tagging org
"""

from __future__ import annotations

from rest_framework import serializers, fields

from openedx_tagging.core.tagging.rest_api.v1.serializers import (
    TaxonomyListQueryParamsSerializer,
    TaxonomySerializer,
)

from organizations.models import Organization


class TaxonomyOrgListQueryParamsSerializer(TaxonomyListQueryParamsSerializer):
    """
    Serializer for the query params for the GET view
    """

    org: fields.Field = serializers.SlugRelatedField(
        slug_field="short_name",
        queryset=Organization.objects.all(),
        required=False,
    )


class TaxonomyUpdateOrgBodySerializer(serializers.Serializer):
    """
    Serializer for the body params for the update orgs action
    """

    orgs: fields.Field = serializers.SlugRelatedField(
        many=True,
        slug_field="short_name",
        queryset=Organization.objects.all(),
        required=False,
    )

    all_orgs: fields.Field = serializers.BooleanField(required=False)

    def validate(self, attrs: dict) -> dict:
        """
        Validate the serializer data
        """
        if bool(attrs.get("orgs") is not None) == bool(attrs.get("all_orgs")):
            raise serializers.ValidationError(
                "You must specify either orgs or all_orgs, but not both."
            )

        return attrs


class OrgListField(serializers.RelatedField):
    """
    Serializer to return the list of orgs for a taxonomy
    """
    def to_representation(self, value):
        """
        Return the Organization short_name, not the TaxonomyOrg object
        """
        return value.org.short_name if value.org else None


class TaxonomyOrgSerializer(TaxonomySerializer):
    """
    Serializer for Taxonomy objects inclusing the associated orgs
    """

    orgs = OrgListField(many=True, read_only=True, source="taxonomyorg_set")

    class Meta:
        model = TaxonomySerializer.Meta.model
        fields = TaxonomySerializer.Meta.fields + ["orgs"]
        read_only_fields = ["orgs"]

