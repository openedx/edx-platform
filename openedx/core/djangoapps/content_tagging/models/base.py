"""
Content Tagging models
"""
from __future__ import annotations

from django.db import models
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils.translation import gettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import LearningContextKey
from opaque_keys.edx.locator import BlockUsageLocator
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy
from organizations.models import Organization


class TaxonomyOrg(models.Model):
    """
    Represents the many-to-many relationship between Taxonomies and Organizations.

    We keep this as a separate class from ContentTaxonomy so that class can remain a proxy for Taxonomy, keeping the
    data models and usage simple.
    """

    class RelType(models.TextChoices):
        OWNER = "OWN", _("owner")

    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE)
    org = models.ForeignKey(
        Organization,
        null=True,
        default=None,
        on_delete=models.CASCADE,
        help_text=_(
            "Organization that is related to this taxonomy."
            "If None, then this taxonomy is related to all organizations."
        ),
    )
    rel_type = models.CharField(
        max_length=3,
        choices=RelType.choices,
        default=RelType.OWNER,
    )

    class Meta:
        indexes = [
            models.Index(fields=["taxonomy", "rel_type"]),
            models.Index(fields=["taxonomy", "rel_type", "org"]),
        ]

    @classmethod
    def get_relationships(
        cls, taxonomy: Taxonomy, rel_type: RelType, org_short_name: str | None = None
    ) -> QuerySet:
        """
        Returns the relationships of the given rel_type and taxonomy where:
        * the relationship is available for all organizations, OR
        * (if provided) the relationship is available to the org with the given org_short_name
        """
        # A relationship with org=None means all Organizations
        org_filter = Q(org=None)
        if org_short_name is not None:
            org_filter |= Q(org__short_name=org_short_name)
        return cls.objects.filter(
            taxonomy=taxonomy,
            rel_type=rel_type,
        ).filter(org_filter)

    @classmethod
    def get_organizations(
        cls, taxonomy: Taxonomy, rel_type: RelType
    ) -> list[Organization]:
        """
        Returns the list of Organizations which have the given relationship to the taxonomy.
        """
        rels = cls.objects.filter(
            taxonomy=taxonomy,
            rel_type=rel_type,
        )
        # A relationship with org=None means all Organizations
        if rels.filter(org=None).exists():
            return list(Organization.objects.all())
        return [rel.org for rel in rels]


class ContentObjectTag(ObjectTag):
    """
    ObjectTag that requires an LearningContextKey or BlockUsageLocator as the object ID.
    """

    class Meta:
        proxy = True

    @property
    def object_key(self) -> BlockUsageLocator | LearningContextKey:
        """
        Returns the object ID parsed as a UsageKey or LearningContextKey.
        Raises InvalidKeyError object_id cannot be parse into one of those key types.

        Returns None if there's no object_id.
        """
        try:
            return LearningContextKey.from_string(str(self.object_id))
        except InvalidKeyError:
            return BlockUsageLocator.from_string(str(self.object_id))


class ContentTaxonomyMixin:
    """
    Taxonomy which can only tag Content objects (e.g. XBlocks or Courses) via ContentObjectTag.

    Also ensures a valid TaxonomyOrg owner relationship with the content object.
    """

    @classmethod
    def taxonomies_for_org(
        cls,
        queryset: QuerySet,
        org: Organization | None = None,
    ) -> QuerySet:
        """
        Filters the given QuerySet to those ContentTaxonomies which are available for the given organization.

        If no `org` is provided, then only ContentTaxonomies available to all organizations are returned.
        If `org` is provided, then ContentTaxonomies available to this organizations are also returned.
        """
        org_short_name = org.short_name if org else None
        return queryset.filter(
            Exists(
                TaxonomyOrg.get_relationships(
                    taxonomy=OuterRef("pk"),
                    rel_type=TaxonomyOrg.RelType.OWNER,
                    org_short_name=org_short_name,
                )
            )
        )

    def _check_object(self, object_tag: ObjectTag) -> bool:
        """
        Returns True if this ObjectTag has a valid object_id.
        """
        content_tag = ContentObjectTag.cast(object_tag)
        try:
            content_tag.object_key
        except InvalidKeyError:
            return False
        return super()._check_object(content_tag)

    def _check_taxonomy(self, object_tag: ObjectTag) -> bool:
        """
        Returns True if this taxonomy is owned by the tag's org.
        """
        content_tag = ContentObjectTag.cast(object_tag)
        try:
            object_key = content_tag.object_key
        except InvalidKeyError:
            return False
        if not TaxonomyOrg.get_relationships(
            taxonomy=self,
            rel_type=TaxonomyOrg.RelType.OWNER,
            org_short_name=object_key.org,
        ).exists():
            return False
        return super()._check_taxonomy(content_tag)


class ContentTaxonomy(ContentTaxonomyMixin, Taxonomy):
    """
    Taxonomy that accepts ContentTags,
    and ensures a valid TaxonomyOrg owner relationship with the content object.
    """

    class Meta:
        proxy = True
