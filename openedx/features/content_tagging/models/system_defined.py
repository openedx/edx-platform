"""
System defined models
"""
from typing import Type

from openedx_tagging.core.tagging.models import (
    ObjectTag,
    ModelSystemDefinedTaxonomy,
    ModelObjectTag,
    UserSystemDefinedTaxonomy,
    LanguageTaxonomy,
)

from organizations.models import Organization
from .base import ContentTaxonomy


class OrganizationModelObjectTag(ModelObjectTag):
    """
    ObjectTags for the OrganizarionSystemDefinedTaxonomy.
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


class OrganizarionSystemDefinedTaxonomy(ModelSystemDefinedTaxonomy):
    """
    Organization based system taxonomy class.
    """

    class Meta:
        proxy = True

    @property
    def object_tag_class(self) -> Type:
        """
        Returns OrganizationModelObjectTag as ObjectTag subclass associated with this taxonomy.
        """
        return OrganizationModelObjectTag


class ContentLanguageTaxonomy(LanguageTaxonomy):
    """
    Language system-defined taxonomy that accepts ContentTags

    Inherit `_check_tag` from LanguageTaxonomy and uses
    `_check_object` and `_check_taxonomy` from ContentTaxonomy
    """

    class Meta:
        proxy = True

    def _check_object(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_object(object_tag)  # pylint: disable=protected-access

    def _check_taxonomy(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_taxonomy(object_tag)  # pylint: disable=protected-access


class ContentAuthorTaxonomy(UserSystemDefinedTaxonomy):
    """
    Author system-defined taxonomy that accepts Content Tags

    Inherit `_check_tag` from UserSystemDefinedTaxonomy and uses
    `_check_object` and `_check_taxonomy` from ContentTaxonomy
    """

    class Meta:
        proxy = True

    def _check_object(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_object(object_tag)  # pylint: disable=protected-access

    def _check_taxonomy(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_taxonomy(object_tag)  # pylint: disable=protected-access


class ContentOrganizationTaxonomy(OrganizarionSystemDefinedTaxonomy):
    """
    Organization system-defined taxonomy that accepts Content Tags

    Inherit `_check_tag` from OrganizarionSystemDefinedTaxonomy and uses
    `_check_object` and `_check_taxonomy` from ContentTaxonomy
    """

    class Meta:
        proxy = True

    def _check_object(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_object(object_tag)  # pylint: disable=protected-access

    def _check_taxonomy(self, object_tag: ObjectTag) -> bool:
        taxonomy = ContentTaxonomy().copy(self)
        return taxonomy._check_taxonomy(object_tag)  # pylint: disable=protected-access
