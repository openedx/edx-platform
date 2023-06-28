"""
Content Tagging models
"""
from django.db import models
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import Taxonomy, TaxonomyManager
from organizations.models import Organization


class ContentTaxonomyManager(TaxonomyManager):
    """
    Manages ContentTaxonomy objects, providing custom utility methods.

    Inherits from InheritanceManager so that subclasses of ContentTaxonomy can be selected in a queryset.
    """

    def filter_enabled(self, org: Organization = None, enabled=True) -> models.QuerySet:
        """
        Returns a query set filtered to return the enabled ContentTaxonomy objects owned by the given org.
        """
        queryset = self
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled)
        org_filter = models.Q(org_owners=None)
        if org:
            org_filter |= models.Q(org_owners=org)
        queryset = queryset.filter(org_filter)
        return queryset


class ContentTaxonomy(Taxonomy):
    """
    Taxonomy used for tagging content-related objects.

    ContentTaxonomies can be owned by one or more organizations, which allows content authors from that organization to
    create taxonomies, edit the taxonomy fields, and add/edit/remove Tags linked to the taxonomy.

    .. no_pii:
    """

    objects = ContentTaxonomyManager()

    org_owners = models.ManyToManyField(Organization, through="ContentTaxonomyOrg")

    class Meta:
        verbose_name_plural = "ContentTaxonomies"

    def validate_object_tag(
        self,
        object_tag: "ObjectTag",
        check_taxonomy=True,
        check_tag=True,
        check_object=True,
    ) -> bool:
        """
        Returns True if the given object tag is valid for this ContentTaxonomy.

        Extends the superclass method by adding its own object checks to ensure:

        * object_tag.object_id is a valid UsageKey or CourseKey, and
        * object_tag.object_id's "org" is enabled for this taxonomy.
        """
        if check_object:
            # ContentTaxonomies require object_id to be a valid CourseKey or UsageKey
            try:
                object_key = UsageKey.from_string(object_tag.object_id)
            except InvalidKeyError:
                try:
                    object_key = CourseKey.from_string(object_tag.object_id)
                except InvalidKeyError:
                    return False

            # ...and object to be in an org that is enabled for this taxonomy.
            if not self.enabled_for_org(object_key.org):
                return False

        return super().validate_object_tag(
            object_tag,
            check_taxonomy=check_taxonomy,
            check_tag=check_tag,
            check_object=check_object,
        )

    def enabled_for_org(self, org_short_name: str) -> bool:
        """
        Returns True if this taxonomy is enabled for the given organization.
        """
        enabled = self.enabled
        if self.org_owners.count():
            enabled &= self.org_owners.filter(
                contenttaxonomyorg__org__short_name=org_short_name,
            ).exists()
        return enabled


class ContentTaxonomyOrg(models.Model):
    """
    Represents the many-to-many relationship between ContentTaxonomies and Organizations.
    """

    taxonomy = models.ForeignKey(ContentTaxonomy, on_delete=models.CASCADE)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
