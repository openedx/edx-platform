"""
System defined models
"""
from typing import Type

from openedx_tagging.core.tagging.models import (
    ModelSystemDefinedTaxonomy,
    ModelObjectTag,
    UserSystemDefinedTaxonomy,
    LanguageTaxonomy,
)

from organizations.models import Organization
from .base import ContentTaxonomyMixin


class OrganizationModelObjectTag(ModelObjectTag):
    """
    ObjectTags for the OrganizationSystemDefinedTaxonomy.
    """

    class Meta:
        proxy = True

    @property
    def tag_class_model(self) -> Type:
        """
        Associate the organization model
        """
        return Organization

    @property
    def tag_class_value(self) -> str:
        """
        Returns the organization name to use it on Tag.value when creating Tags for this taxonomy.
        """
        return "name"


class ContentOrganizationTaxonomy(ContentTaxonomyMixin, ModelSystemDefinedTaxonomy):
    """
    Organization system-defined taxonomy that accepts ContentTags

    Side note: The organization of an object is already encoded in its usage ID,
    but a Taxonomy with Organization as Tags is being used so that the objects can be
    indexed and can be filtered in the same tagging system, without any special casing.
    """

    class Meta:
        proxy = True

    @property
    def object_tag_class(self) -> Type:
        """
        Returns OrganizationModelObjectTag as ObjectTag subclass associated with this taxonomy.
        """
        return OrganizationModelObjectTag


class ContentLanguageTaxonomy(ContentTaxonomyMixin, LanguageTaxonomy):
    """
    Language system-defined taxonomy that accepts ContentTags
    """

    class Meta:
        proxy = True


class ContentAuthorTaxonomy(ContentTaxonomyMixin, UserSystemDefinedTaxonomy):
    """
    Author system-defined taxonomy that accepts ContentTags
    """

    class Meta:
        proxy = True
