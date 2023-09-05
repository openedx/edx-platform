"""
Content Tagging APIs
"""
from __future__ import annotations

from typing import Iterator, List, Type

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import QuerySet
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import Taxonomy
from organizations.models import Organization

from .models import ContentObjectTag, ContentTaxonomy, TaxonomyOrg


def create_taxonomy(
    name: str,
    description: str = None,
    enabled=True,
    required=False,
    allow_multiple=False,
    allow_free_text=False,
    taxonomy_class: Type = ContentTaxonomy,
) -> Taxonomy:
    """
    Creates, saves, and returns a new Taxonomy with the given attributes.

    If `taxonomy_class` not provided, then uses ContentTaxonomy.
    """
    return oel_tagging.create_taxonomy(
        name=name,
        description=description,
        enabled=enabled,
        required=required,
        allow_multiple=allow_multiple,
        allow_free_text=allow_free_text,
        taxonomy_class=taxonomy_class,
    )


def set_taxonomy_orgs(
    taxonomy: Taxonomy,
    all_orgs=False,
    orgs: List[Organization] = None,
    relationship: TaxonomyOrg.RelType = TaxonomyOrg.RelType.OWNER,
):
    """
    Updates the list of orgs associated with the given taxonomy.

    Currently, we only have an "owner" relationship, but there may be other types added in future.

    When an org has an "owner" relationship with a taxonomy, that taxonomy is available for use by content in that org,
    mies

    If `all_orgs`, then the taxonomy is associated with all organizations, and the `orgs` parameter is ignored.

    If not `all_orgs`, the taxonomy is associated with each org in the `orgs` list. If that list is empty, the
    taxonomy is not associated with any orgs.
    """
    TaxonomyOrg.objects.filter(
        taxonomy=taxonomy,
        rel_type=relationship,
    ).delete()

    # org=None means the relationship is with "all orgs"
    if all_orgs:
        orgs = [None]
    if orgs:
        TaxonomyOrg.objects.bulk_create(
            [
                TaxonomyOrg(
                    taxonomy=taxonomy,
                    org=org,
                    rel_type=relationship,
                )
                for org in orgs
            ]
        )


def get_taxonomies_for_org(
    enabled=True,
    org_owner: Organization = None,
) -> QuerySet:
    """
    Generates a list of the enabled Taxonomies available for the given org, sorted by name.

    We return a QuerySet here for ease of use with Django Rest Framework and other query-based use cases.
    So be sure to use `Taxonomy.cast()` to cast these instances to the appropriate subclass before use.

    If no `org` is provided, then only Taxonomies which are available for _all_ Organizations are returned.

    If you want the disabled Taxonomies, pass enabled=False.
    If you want all Taxonomies (both enabled and disabled), pass enabled=None.
    """
    taxonomies = oel_tagging.get_taxonomies(enabled=enabled)
    return ContentTaxonomy.taxonomies_for_org(
        org=org_owner,
        queryset=taxonomies,
    )


def get_content_tags(
    object_id: str, taxonomy_id: str = None
) -> Iterator[ContentObjectTag]:
    """
    Generates a list of content tags for a given object.

    Pass taxonomy to limit the returned object_tags to a specific taxonomy.
    """
    for object_tag in oel_tagging.get_object_tags(
        object_id=object_id,
        taxonomy_id=taxonomy_id,
    ):
        yield ContentObjectTag.cast(object_tag)


def tag_content_object(
    taxonomy: Taxonomy,
    tags: list,
    object_id: CourseKey | UsageKey,
) -> list[ContentObjectTag]:
    """
    This is the main API to use when you want to add/update/delete tags from a content object (e.g. an XBlock or
    course).

    It works one "Taxonomy" at a time, i.e. one field at a time, so you can set call it with taxonomy=Keywords,
    tags=["gravity", "newton"] to replace any "Keywords" [Taxonomy] tags on the given content object with "gravity" and
    "newton". Doing so to change the "Keywords" Taxonomy won't affect other Taxonomy's tags (other fields) on the
    object, such as "Language: [en]" or "Difficulty: [hard]".

    If it's a free-text taxonomy, then the list should be a list of tag values.
    Otherwise, it should be a list of existing Tag IDs.

    Raises ValueError if the proposed tags are invalid for this taxonomy.
    Preserves existing (valid) tags, adds new (valid) tags, and removes omitted (or invalid) tags.
    """
    content_tags = []
    for object_tag in oel_tagging.tag_object(
        taxonomy=taxonomy,
        tags=tags,
        object_id=str(object_id),
    ):
        content_tags.append(ContentObjectTag.cast(object_tag))
    return content_tags


# Expose the oel_tagging APIs

get_taxonomy = oel_tagging.get_taxonomy
get_taxonomies = oel_tagging.get_taxonomies
get_tags = oel_tagging.get_tags
delete_object_tags = oel_tagging.delete_object_tags
resync_object_tags = oel_tagging.resync_object_tags
