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


class ContentLanguageTaxonomy(
    ContentTaxonomy,
    LanguageTaxonomy
):
    """
    Language system-defined taxonomy that accepts ContentTags

    Inherit `_check_object` and `_check_taxonomy` from ContentTaxonomy
    and inherit `_check_tag` from LanguageTaxonomy
    """

    class Meta:
        proxy = True

    def _check_tag(self, object_tag: ObjectTag) -> bool:
        return super(LanguageTaxonomy, self)._check_tag(object_tag)


class ContentAuthorTaxonomy(
    ContentTaxonomy,
    UserSystemDefinedTaxonomy
):
    """
    Author system-defined taxonomy that accepts Content Tags

    Inherit `_check_object` and `_check_taxonomy` from ContentTaxonomy
    and inherit `_check_tag` from UserSystemDefinedTaxonomy
    """

    class Meta:
        proxy = True

    def _check_tag(self, object_tag: ObjectTag) -> bool:
        return super(UserSystemDefinedTaxonomy, self)._check_tag(object_tag)


class ContentOrganizationTaxonomy(
    ContentTaxonomy,
    OrganizarionSystemDefinedTaxonomy
):
    """
    Organization system-defined taxonomy that accepts Content Tags

    Inherit `_check_object` and `_check_taxonomy` from ContentTaxonomy
    and inherit `_check_tag` from OrganizarionSystemDefinedTaxonomy
    """

    class Meta:
        proxy = True

    def _check_tag(self, object_tag: ObjectTag) -> bool:
        return super(OrganizarionSystemDefinedTaxonomy, self)._check_tag(object_tag)
