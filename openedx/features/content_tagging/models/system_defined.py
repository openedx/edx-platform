"""
System defined models
"""
from openedx_tagging.core.tagging.models import (
    UserSystemDefinedTaxonomy,
    LanguageTaxonomy,
)

from .base import ContentTaxonomyMixin


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
