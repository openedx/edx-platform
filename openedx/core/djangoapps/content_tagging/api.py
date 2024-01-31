"""
Content Tagging APIs
"""
from __future__ import annotations

from itertools import groupby

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import Exists, OuterRef, Q, QuerySet
from opaque_keys.edx.keys import CourseKey, LearningContextKey
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy
from organizations.models import Organization

from .models import ContentObjectTag, TaxonomyOrg
from .types import ContentKey, ObjectTagByObjectIdDict, TaxonomyDict


def create_taxonomy(
    name: str,
    description: str | None = None,
    enabled=True,
    allow_multiple=True,
    allow_free_text=False,
    orgs: list[Organization] | None = None,
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
    org_owner: Organization | None = None,
) -> QuerySet:
    """
    Generates a list of the enabled Taxonomies available for the given org, sorted by name.

    We return a QuerySet here for ease of use with Django Rest Framework and other query-based use cases.
    So be sure to use `Taxonomy.cast()` to cast these instances to the appropriate subclass before use.

    If no `org` is provided, then only Taxonomies which are available for _all_ Organizations are returned.

    If you want the disabled Taxonomies, pass enabled=False.
    If you want all Taxonomies (both enabled and disabled), pass enabled=None.
    """
    org_short_name = org_owner.short_name if org_owner else None
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


def get_content_tags(
    object_key: ContentKey,
    taxonomy_id: int | None = None,
) -> QuerySet[ContentObjectTag]:
    """
    Generates a list of content tags for a given object.

    Pass taxonomy to limit the returned object_tags to a specific taxonomy.
    """

    tags = oel_tagging.get_object_tags(
        object_id=str(object_key),
        taxonomy_id=taxonomy_id,
        object_tag_class=ContentObjectTag,
    )

    # Add a generic type to get_object_tags to fix this
    return tags  # type: ignore


# FixMe: The following method (tag_content_object) is only used in tasks.py for auto-tagging. To tag object we are
# using oel_tagging.tag_object and checking permissions via rule overrides.
def tag_content_object(
    object_key: ContentKey,
    taxonomy: Taxonomy,
    tags: list,
) -> QuerySet[ContentObjectTag]:
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
    if not taxonomy.system_defined:
        # We require that this taxonomy is linked to the content object's "org" or linked to "all orgs" (None):
        org_short_name = object_key.org  # type: ignore
        if not taxonomy.taxonomyorg_set.filter(Q(org__short_name=org_short_name) | Q(org=None)).exists():
            raise ValueError(f"The specified Taxonomy is not enabled for the content object's org ({org_short_name})")
    oel_tagging.tag_object(
        taxonomy=taxonomy,
        tags=tags,
        object_id=str(object_key),
        object_tag_class=ContentObjectTag,
    )
    return get_content_tags(object_key, taxonomy_id=taxonomy.id)


def get_all_object_tags(
    content_key: LearningContextKey,
) -> tuple[ObjectTagByObjectIdDict, TaxonomyDict]:
    """
    Returns a tuple with a dictionary of grouped object tags for all blocks and a dictionary of taxonomies.
    """
    # ToDo: Add support for other content types (like LibraryContent and LibraryBlock)
    if isinstance(content_key, CourseKey):
        course_key_str = str(content_key)
        # We use a block_id_prefix (i.e. the modified course id) to get the tags for the children of the Content
        # (course) in a single db query.
        block_id_prefix = course_key_str.replace("course-v1:", "block-v1:", 1)
    else:
        raise NotImplementedError(f"Invalid content_key: {type(content_key)} -> {content_key}")

    # There is no API method in oel_tagging.api that does this yet,
    # so for now we have to build the ORM query directly.
    all_object_tags = list(ObjectTag.objects.filter(
        Q(object_id__startswith=block_id_prefix) | Q(object_id=course_key_str),
        Q(tag__isnull=False, tag__taxonomy__isnull=False),
    ).select_related("tag__taxonomy"))

    grouped_object_tags: ObjectTagByObjectIdDict = {}
    taxonomies: TaxonomyDict = {}

    for object_id, block_tags in groupby(all_object_tags, lambda x: x.object_id):
        grouped_object_tags[object_id] = {}
        for taxonomy_id, taxonomy_tags in groupby(block_tags, lambda x: x.tag.taxonomy_id):
            object_tags_list = list(taxonomy_tags)
            grouped_object_tags[object_id][taxonomy_id] = object_tags_list

            if taxonomy_id not in taxonomies:
                taxonomies[taxonomy_id] = object_tags_list[0].tag.taxonomy

    return grouped_object_tags, taxonomies


# Expose the oel_tagging APIs

get_taxonomy = oel_tagging.get_taxonomy
get_taxonomies = oel_tagging.get_taxonomies
get_tags = oel_tagging.get_tags
get_object_tag_counts = oel_tagging.get_object_tag_counts
delete_object_tags = oel_tagging.delete_object_tags
resync_object_tags = oel_tagging.resync_object_tags
