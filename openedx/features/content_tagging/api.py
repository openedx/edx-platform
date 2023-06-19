"""
Content Tagging APIs
"""
from typing import List

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import QuerySet
from openedx_tagging.core.tagging.models import ObjectTag, Tag, Taxonomy
from organizations.models import Organization

from .models import ContentTaxonomy


def create_taxonomy(
    name,
    org_owners: List[Organization] = None,
    description=None,
    enabled=True,
    required=False,
    allow_multiple=False,
    allow_free_text=False,
) -> ContentTaxonomy:
    """
    Creates, saves, and returns a new ContentTaxonomy with the given attributes.

    If `org_owners` is empty/None, then the returned taxonomy is enabled for all organizations.
    """
    taxonomy = ContentTaxonomy.objects.create(
        name=name,
        description=description,
        enabled=enabled,
        required=required,
        allow_multiple=allow_multiple,
        allow_free_text=allow_free_text,
    )
    if org_owners:
        set_taxonomy_org_owners(taxonomy, org_owners)
    return taxonomy


def set_taxonomy_org_owners(
    taxonomy: ContentTaxonomy,
    org_owners: List[Organization] = None,
) -> ContentTaxonomy:
    """
    Updates the list of org_owners on the given taxonomy.

    If `org_owners` is empty/None, then the returned taxonomy is enabled for all organizations.
    """
    if org_owners:
        taxonomy.org_owners.set(org_owners)
    else:
        taxonomy.org_owners.clear()
    return taxonomy


def get_taxonomies(org_owner: Organization = None, enabled=True) -> QuerySet:
    """
    Returns a queryset containing the enabled taxonomies owned by the given org, sorted by name.

    If you want the disabled taxonomies, pass enabled=False.
    If you want all taxonomies (both enabled and disabled), pass enabled=None.
    """
    return (
        ContentTaxonomy.objects.filter_enabled(
            org_owner,
            enabled,
        )
        .order_by("name", "id")
        .select_subclasses()
    )


# Expose the oel_tagging APIs


def get_tags(taxonomy: Taxonomy) -> List[Tag]:
    """
    Exposes the oel_tagging.get_tags API method.
    """
    return oel_tagging.get_tags(taxonomy)


def resync_object_tags(object_tags: QuerySet = None) -> int:
    """
    Exposes the oel_tagging.resync_object_tags API method.
    """
    return oel_tagging.resync_object_tags(object_tags)


def get_object_tags(
    taxonomy: Taxonomy, object_id: str, object_type: str, valid_only=True
) -> List[ObjectTag]:
    """
    Exposes the oel_tagging.get_object_tags API method.
    """
    return oel_tagging.get_object_tags(taxonomy, object_id, object_type, valid_only)


def tag_object(
    taxonomy: Taxonomy, tags: List, object_id: str, object_type: str
) -> List[ObjectTag]:
    """
    Exposes the oel_tagging.tag_object API method.
    """
    return oel_tagging.tag_object(taxonomy, tags, object_id, object_type)
