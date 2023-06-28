"""
Content Tagging APIs
"""
from typing import List

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import QuerySet
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


# Expose the oel_tagging APIs that we haven't overridden here:

get_tags = oel_tagging.get_tags
resync_object_tags = oel_tagging.resync_object_tags
get_object_tags = oel_tagging.get_object_tags
tag_object = oel_tagging.tag_object
