"""
Content Tagging APIs
"""
from __future__ import annotations

from itertools import groupby

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import Exists, OuterRef, Q, QuerySet
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy
from organizations.models import Organization
from urllib.parse import quote, unquote

from .models import TaxonomyOrg
from .types import (
    ContentKey,
    ObjectTagByObjectIdDict,
    TagValuesByTaxonomyExportIdDict,
    TaxonomyExportDict,
    TaxonomyDict,
)

from .utils import check_taxonomy_context_key_org, get_context_key_from_key


def create_taxonomy(
    name: str,
    description: str | None = None,
    enabled=True,
    allow_multiple=True,
    allow_free_text=False,
    orgs: list[Organization] | None = None,
    export_id: str | None = None,
) -> Taxonomy:
    """
    Creates, saves, and returns a new Taxonomy with the given attributes.
    """
    taxonomy = oel_tagging.create_taxonomy(
        name=name,
        description=description,
        enabled=enabled,
        allow_multiple=allow_multiple,
        allow_free_text=allow_free_text,
        export_id=export_id,
    )

    if orgs is not None:
        set_taxonomy_orgs(taxonomy=taxonomy, all_orgs=False, orgs=orgs)

    return taxonomy


def set_taxonomy_orgs(
    taxonomy: Taxonomy,
    all_orgs=False,
    orgs: list[Organization] | None = None,
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
    if taxonomy.system_defined:
        raise ValueError("Cannot set orgs for a system-defined taxonomy")

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
    org_short_name: str | None = None,
) -> QuerySet:
    """
    Generates a list of the enabled Taxonomies available for the given org, sorted by name.

    We return a QuerySet here for ease of use with Django Rest Framework and other query-based use cases.
    So be sure to use `Taxonomy.cast()` to cast these instances to the appropriate subclass before use.

    If no `org` is provided, then only Taxonomies which are available for _all_ Organizations are returned.

    If you want the disabled Taxonomies, pass enabled=False.
    If you want all Taxonomies (both enabled and disabled), pass enabled=None.
    """
    return oel_tagging.get_taxonomies(enabled=enabled).filter(
        Exists(
            TaxonomyOrg.get_relationships(
                taxonomy=OuterRef("pk"),  # type: ignore
                rel_type=TaxonomyOrg.RelType.OWNER,
                org_short_name=org_short_name,
            )
        )
    )


def get_unassigned_taxonomies(enabled=True) -> QuerySet:
    """
    Generate a list of the enabled orphaned Taxomonies, i.e. that do not belong to any
    organization. We don't use `TaxonomyOrg.get_relationships` as that returns
    Taxonomies which are available for all Organizations when no `org` is provided
    """
    return oel_tagging.get_taxonomies(enabled=enabled).filter(
        ~(
            Exists(
                TaxonomyOrg.objects.filter(
                    taxonomy=OuterRef("pk"),
                    rel_type=TaxonomyOrg.RelType.OWNER,
                )
            )
        )
    )


def get_all_object_tags(
    content_key: LibraryLocatorV2 | CourseKey | ContentKey,
    prefetch_orgs: bool = False,
) -> tuple[ObjectTagByObjectIdDict, TaxonomyDict]:
    """
    Get all the object tags applied to components in the given course/library.

    Includes any tags applied to the course/library as a whole.
    Returns a tuple with a dictionary of grouped object tags for all blocks and a dictionary of taxonomies.

    If `prefetch_orgs` is set, then the returned ObjectTag taxonomies will have their TaxonomyOrgs prefetched,
    which makes checking permissions faster.
    """
    context_key_str = str(content_key)
    # We use a block_id_prefix (i.e. the modified course id) to get the tags for the children of the Content
    # (course/library) in a single db query.
    if isinstance(content_key, CourseKey):
        block_id_prefix = context_key_str.replace("course-v1:", "block-v1:", 1)
    elif isinstance(content_key, LibraryLocatorV2):
        block_id_prefix = context_key_str.replace("lib:", "lb:", 1)
    else:
        # No context, so we'll just match the object_id, with no prefix.
        block_id_prefix = None

    # There is no API method in oel_tagging.api that does this yet,
    # so for now we have to build the ORM query directly.
    object_id_clause = Q(object_id=content_key)
    if block_id_prefix:
        object_id_clause |= Q(object_id__startswith=block_id_prefix)

    all_object_tags = ObjectTag.objects.filter(
        Q(tag__isnull=False, tag__taxonomy__isnull=False),
        object_id_clause,
    ).select_related("tag__taxonomy")

    if prefetch_orgs:
        all_object_tags = all_object_tags.prefetch_related("tag__taxonomy__taxonomyorg_set")

    grouped_object_tags: ObjectTagByObjectIdDict = {}
    taxonomies: TaxonomyDict = {}

    for object_id, block_tags in groupby(all_object_tags, lambda x: x.object_id):
        grouped_object_tags[object_id] = {}
        for taxonomy_id, taxonomy_tags in groupby(block_tags, lambda x: x.tag.taxonomy_id if x.tag else 0):
            object_tags_list = list(taxonomy_tags)
            grouped_object_tags[object_id][taxonomy_id] = object_tags_list

            if taxonomy_id not in taxonomies:
                assert object_tags_list[0].tag
                assert object_tags_list[0].tag.taxonomy
                taxonomies[taxonomy_id] = object_tags_list[0].tag.taxonomy

    return grouped_object_tags, taxonomies


def set_object_tags(
    content_key: ContentKey,
    object_tags: TagValuesByTaxonomyExportIdDict,
    taxonomy_cache: TaxonomyExportDict | None = None,
) -> None:
    """
    Sets the tags for the given content object.

    (Optional) provide a cache of taxonomies keyed by export_id to save refetching from the database.
    """
    context_key = get_context_key_from_key(content_key)

    if taxonomy_cache is None:
        taxonomy_cache = {}

    for taxonomy_export_id, tags_values in object_tags.items():

        if taxonomy_export_id not in taxonomy_cache:
            taxonomy_cache[taxonomy_export_id] = oel_tagging.get_taxonomy_by_export_id(taxonomy_export_id)
        taxonomy = taxonomy_cache.get(taxonomy_export_id)

        if not taxonomy:
            continue

        if not check_taxonomy_context_key_org(taxonomy, context_key):
            continue

        oel_tagging.tag_object(
            object_id=str(content_key),
            taxonomy=taxonomy,
            tags=tags_values,
        )


def copy_object_tags(
    source_content_key: ContentKey,
    dest_content_key: ContentKey,
) -> None:
    """
    Copies the permitted object tags on source_object_id to dest_object_id.

    If an source object tag is not available for use on the dest_object_id, it will not be copied.
    """
    all_object_tags, taxonomies = get_all_object_tags(
        content_key=source_content_key,
        prefetch_orgs=True,
    )

    # Convert returned data into the format expected by set_object_tags
    source_object_tags = all_object_tags.get(str(source_content_key), {})
    taxonomy_cache: TaxonomyExportDict = {
        taxonomy.export_id: taxonomy
        for taxonomy in taxonomies.values()
    }
    tags_by_taxonomy: TagValuesByTaxonomyExportIdDict = {}
    for taxonomy_id, tags in source_object_tags.items():
        taxonomy = taxonomies[taxonomy_id]
        tags_by_taxonomy[taxonomy.export_id] = [tag.value for tag in tags]

    set_object_tags(
        content_key=dest_content_key,
        object_tags=tags_by_taxonomy,
        taxonomy_cache=taxonomy_cache,
    )


def serialize_object_tags(usage_id: str) -> str:
    """
    Serialize the given object tags to a string, escaping special characters

    Note that we are serializing the tag data only, not the object_id.

    Example tags:
        LightCast Skills Taxonomy: ["Typing", "Microsoft Office"]
        Open Canada Skills Taxonomy: ["MS Office", "<some:;,skill/|=>"]

    Example serialized tags:
        lightcast-skills:Typing,Microsoft Office;open-canada-skills:MS Office,%3Csome%3A%3B%2Cskill%2F%7C%3D%3E
    """
    content_tags = get_object_tags(usage_id)
    serialized_tags = []
    taxonomies_and_tags: dict[str, list[str]] = {}
    for tag in content_tags:
        taxonomy_export_id = tag.taxonomy.export_id

        if not taxonomies_and_tags.get(taxonomy_export_id):
            taxonomies_and_tags[taxonomy_export_id] = []

        # Escape special characters in tag values, except spaces (%20) for better readability
        escaped_tag = quote(tag.value).replace("%20", " ")
        taxonomies_and_tags[taxonomy_export_id].append(escaped_tag)

    for taxonomy in taxonomies_and_tags:
        merged_tags = ','.join(taxonomies_and_tags.get(taxonomy, []))
        serialized_tags.append(f"{taxonomy}:{merged_tags}")

    return ";".join(serialized_tags)


def deserialize_object_tags(
    tag_data: str,
) -> TagValuesByTaxonomyExportIdDict:
    """
    Deserializes a string of formatted tag data. See serialize_object_tags for details.
    """
    serialized_tags = tag_data.split(';')
    taxonomy_and_tags_dict: TagValuesByTaxonomyExportIdDict = {}
    for serialized_tag in serialized_tags:
        taxonomy_export_id, tags = serialized_tag.split(':')
        tag_values = [unquote(tag) for tag in tags.split(',')]
        taxonomy_and_tags_dict[taxonomy_export_id] = tag_values

    return taxonomy_and_tags_dict


# Expose the oel_tagging APIs

get_taxonomy = oel_tagging.get_taxonomy
get_taxonomies = oel_tagging.get_taxonomies
get_tags = oel_tagging.get_tags
get_object_tag_counts = oel_tagging.get_object_tag_counts
delete_object_tags = oel_tagging.delete_object_tags
resync_object_tags = oel_tagging.resync_object_tags
get_object_tags = oel_tagging.get_object_tags
tag_object = oel_tagging.tag_object
add_tag_to_taxonomy = oel_tagging.add_tag_to_taxonomy
