"""
API Serializers for content tagging org
"""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers, fields

from openedx_tagging.core.tagging.rest_api.v1.serializers import (
    TaxonomyListQueryParamsSerializer,
    TaxonomySerializer,
)

from organizations.models import Organization


class OptionalSlugRelatedField(serializers.SlugRelatedField):
    """
    Modifies the DRF serializer SlugRelatedField.

    Non-existent slug values are represented internally as an empty queryset, instead of throwing a validation error.
    """

    def to_internal_value(self, data):
        """
        Returns the object related to the given slug value, or an empty queryset if not found.
        """

        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            return queryset.none()
        except (TypeError, ValueError):
            self.fail('invalid')


class TaxonomyOrgListQueryParamsSerializer(TaxonomyListQueryParamsSerializer):
    """
    Serializer for the query params for the GET view
    """

    org: fields.Field = OptionalSlugRelatedField(
        slug_field="short_name",
        queryset=Organization.objects.all(),
        required=False,
    )
    unassigned: fields.Field = serializers.BooleanField(required=False)


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


class TaxonomyOrgSerializer(TaxonomySerializer):
    """
    Serializer for Taxonomy objects inclusing the associated orgs
    """

    orgs = serializers.SerializerMethodField()
    all_orgs = serializers.SerializerMethodField()

    def get_orgs(self, obj) -> list[str]:
        """
        Return the list of orgs for the taxonomy.
         """
        return [taxonomy_org.org.short_name for taxonomy_org in obj.taxonomyorg_set.all() if taxonomy_org.org]

    def get_all_orgs(self, obj) -> bool:
        """
        Return True if the taxonomy is associated with all orgs.
        """
        return obj.taxonomyorg_set.filter(org__isnull=True).exists()

    class Meta:
        model = TaxonomySerializer.Meta.model
        fields = TaxonomySerializer.Meta.fields + ["orgs", "all_orgs"]
        read_only_fields = ["orgs", "all_orgs"]
