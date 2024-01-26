"""
Content Tagging APIs
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import csv
from itertools import groupby
from io import StringIO

import openedx_tagging.core.tagging.api as oel_tagging
from django.db.models import Q, QuerySet, Exists, OuterRef
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import ObjectTag

from xmodule.modulestore.django import modulestore

from .models import ContentObjectTag, TaxonomyOrg

if TYPE_CHECKING:
    from openedx_tagging.core.tagging.models import Taxonomy
    from xblock.runtime import Runtime
    from organizations.models import Organization
    from .types import ContentKey


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
) -> QuerySet:
    """
    Generates a list of content tags for a given object.

    Pass taxonomy to limit the returned object_tags to a specific taxonomy.
    """
    return oel_tagging.get_object_tags(
        object_id=str(object_key),
        taxonomy_id=taxonomy_id,
        object_tag_class=ContentObjectTag,
    )


# FixMe: The following method (tag_content_object) is only used in tasks.py for auto-tagging. To tag object we are
# using oel_tagging.tag_object and checking permissions via rule overrides.
def tag_content_object(
    object_key: ContentKey,
    taxonomy: Taxonomy,
    tags: list,
) -> QuerySet:
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


def export_content_object_children_tags(
    course_key_str: str,
) -> str:
    """
    Generates a CSV file with the tags for all the children of a course.
    """
    def _get_course_children_tags(course_key: CourseKey) -> tuple[dict[str, dict[int, list[str]]], dict[int, str]]:
        """
        Returns a tuple with a dictionary of object tags for all blocks of a course,
        grouping by the block id and taxonomy id; and a dictionary of taxonomy ids and names.

        I.e.
        // result
        {
            // Block with id block-v1:edX+DemoX+Demo_Course+type@chapter+block@chapter
            "block-v1:edX+DemoX+Demo_Course+type@chapter+block@chapter": {
                // ObjectTags from Taxonomy with id 1
                "1": (
                    "Tag1",
                    "Tag2",
                    ...
                ),
                // ObjectTags from Taxonomy with id 2
                "2": (
                    "Tag3",
                    ...
                ),
                ...
            },
            // Block with id block-v1:edX+DemoX+Demo_Course+type@sequential+block@sequential
            "block-v1:edX+DemoX+Demo_Course+type@sequential+block@sequential": {
                // ObjectTags from Taxonomy with id 1
                "1": (
                    "Tag2",
                    ...
                ),
                ...
            },
        }

        // taxonomies
        {
            "1": "Taxonomy A",
            "2": "Taxonomy B",
            ...
        }
        """
        block_id_prefix = str(course_key).replace("course-v1:", "block-v1:", 1)
        block_tags_records = ObjectTag.objects.filter(object_id__startswith=block_id_prefix) \
            .select_related("tag__taxonomy").all()

        result: dict[str, dict[int, list[str]]] = {}
        taxonomies: dict[int, str] = {}

        for object_id, block_tags in groupby(block_tags_records, lambda x: x.object_id):
            result[object_id] = {}
            for taxonomy_id, taxonomy_tags in groupby(block_tags, lambda x: x.tag.taxonomy_id):
                object_tag_list = list(taxonomy_tags)
                result[object_id][taxonomy_id] = [
                    objecttag.value
                    for objecttag in object_tag_list
                ]

                if taxonomy_id not in taxonomies:
                    taxonomies[taxonomy_id] = object_tag_list[0].tag.taxonomy.name

        return result, taxonomies

    def _generate_csv(
            header: dict[str, str],
            blocks: list[tuple[int, UsageKey]],
            tags: dict[str, dict[int, list[str]]],
            taxonomies: dict[int, str],
            runtime: Runtime,
    ) -> str:
        """
        Receives the blocks, tags and taxonomies and returns a CSV string
        """

        with StringIO() as csv_buffer:
            csv_writer = csv.DictWriter(csv_buffer, fieldnames=header.keys())
            csv_writer.writerow(header)

            # Iterate over the blocks stack and write the block rows
            while blocks:
                level, block_id = blocks.pop()
                # ToDo: fix block typing
                block = runtime.get_block(block_id)

                block_data = {
                    "name": level * "  " + block.display_name_with_default,
                    "type": block.category,
                    "id": block_id
                }

                block_id_str = str(block_id)

                # Add the tags for each taxonomy
                for taxonomy_id in taxonomies:
                    if block_id_str in tags and taxonomy_id in tags[block_id_str]:
                        block_data[f"taxonomy_{taxonomy_id}"] = ", ".join(tags[block_id_str][taxonomy_id])

                csv_writer.writerow(block_data)

                # Add children to the stack
                if block.has_children:
                    for child_id in block.children:
                        blocks.append((level + 1, child_id))

            return csv_buffer.getvalue()

    store = modulestore()
    course_key = CourseKey.from_string(course_key_str)
    if not course_key.is_course:
        raise ValueError(f"Invalid course key {course_key_str}")

    # ToDo: fix course typing
    course = store.get_course(course_key)
    if course is None:
        raise ValueError(f"Course {course_key} not found")

    tags, taxonomies = _get_course_children_tags(course_key)

    blocks = []
    # Add children to the stack
    if course.has_children:
        for child_id in course.children:
            blocks.append((0, child_id))

    header = {"name": "Name", "type": "Type", "id": "ID"}

    # Prepare the header for the taxonomies
    # We are using the taxonomy id as the field name to avoid collisions
    # ToDo: Change name -> export_id after done:
    # - https://github.com/openedx/modular-learning/issues/183
    for taxonomy_id, name in taxonomies.items():
        header[f"taxonomy_{taxonomy_id}"] = name

    return _generate_csv(header, blocks, tags, taxonomies, course.runtime)


# Expose the oel_tagging APIs

get_taxonomy = oel_tagging.get_taxonomy
get_taxonomies = oel_tagging.get_taxonomies
get_tags = oel_tagging.get_tags
get_object_tag_counts = oel_tagging.get_object_tag_counts
delete_object_tags = oel_tagging.delete_object_tags
resync_object_tags = oel_tagging.resync_object_tags
