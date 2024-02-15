"""
This module contains helper functions to build a object tree with object tags.
"""

from __future__ import annotations

from typing import Iterator

from attrs import define
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
from xblock.core import XBlock

import openedx.core.djangoapps.content_libraries.api as library_api
from openedx.core.djangoapps.content_libraries.api import LibraryXBlockMetadata
from xmodule.modulestore.django import modulestore

from ...types import ObjectTagByObjectIdDict, ObjectTagByTaxonomyIdDict


@define
class TaggedContent:
    """
    A tagged content, with its tags and children.
    """
    display_name: str
    block_id: str
    category: str
    object_tags: ObjectTagByTaxonomyIdDict
    children: list[TaggedContent] | None


def iterate_with_level(
    tagged_content: TaggedContent, level: int = 0
) -> Iterator[tuple[TaggedContent, int]]:
    """
    Iterator that yields the tagged content and the level of the block
    """
    yield tagged_content, level
    if tagged_content.children:
        for child in tagged_content.children:
            yield from iterate_with_level(child, level + 1)


def get_course_tagged_object_and_children(
    course_key: CourseKey, object_tag_cache: ObjectTagByObjectIdDict
) -> tuple[TaggedContent, list[XBlock]]:
    store = modulestore()

    course = store.get_course(course_key)
    assert course is not None
    course_id = str(course_key)

    tagged_course = TaggedContent(
        display_name=course.display_name_with_default,
        block_id=course_id,
        category=course.category,
        object_tags=object_tag_cache.get(course_id, {}),
        children=None,
    )
    if course.has_children:
        children = course.children
    else:
        children = []

    return tagged_course, children


def get_library_tagged_object_and_children(
    library_key: LibraryLocatorV2, object_tag_cache: ObjectTagByObjectIdDict
) -> tuple[TaggedContent, list[LibraryXBlockMetadata]]:
    library = library_api.get_library(library_key)
    assert library is not None

    library_id = str(library_key)

    tagged_library = TaggedContent(
        display_name=library.title,
        block_id=library_id,
        category='library',
        object_tags=object_tag_cache.get(library_id, {}),
        children=None,
    )

    children = library_api.get_library_blocks(library_key)

    return tagged_library, children


def get_xblock_tagged_object_and_children(
    usage_key: UsageKey, object_tag_cache: ObjectTagByObjectIdDict, store
) -> tuple[TaggedContent, list[XBlock]]:
    block = store.get_item(usage_key)
    block_id = str(usage_key)
    tagged_block = TaggedContent(
        display_name=block.display_name_with_default,
        block_id=block_id,
        category=block.category,
        object_tags=object_tag_cache.get(block_id, {}),
        children=None,
    )

    return tagged_block, block.children if block.has_children else []


def get_library_block_tagged_object(
    library_block: LibraryXBlockMetadata, object_tag_cache: ObjectTagByObjectIdDict
) -> tuple[TaggedContent, None]:
    block_id = str(library_block.usage_key)
    tagged_library_block = TaggedContent(
        display_name=library_block.display_name,
        block_id=block_id,
        category=library_block.usage_key.block_type,
        object_tags=object_tag_cache.get(block_id, {}),
        children=None,
    )

    return tagged_library_block, None


def build_object_tree_with_objecttags(
    content_key: LibraryLocatorV2 | CourseKey,
    object_tag_cache: ObjectTagByObjectIdDict,
) -> TaggedContent:
    """
    Returns the object with the tags associated with it.
    """
    if isinstance(content_key, CourseKey):
        tagged_content, children = get_course_tagged_object_and_children(
            content_key, object_tag_cache
        )
    elif isinstance(content_key, LibraryLocatorV2):
        tagged_content, children = get_library_tagged_object_and_children(
            content_key, object_tag_cache
        )
    else:
        raise NotImplementedError(f"Invalid content_key: {type(content_key)} -> {content_key}")

    blocks: list[tuple[TaggedContent, list | None]] = [(tagged_content, children)]

    store = modulestore()

    while blocks:
        tagged_block, children = blocks.pop()
        tagged_block.children = []

        if not children:
            continue

        for child in children:
            child_children: list | None

            if isinstance(child, UsageKey):
                tagged_child, child_children = get_xblock_tagged_object_and_children(
                    child, object_tag_cache, store
                )
            elif isinstance(child, LibraryXBlockMetadata):
                tagged_child, child_children = get_library_block_tagged_object(
                    child, object_tag_cache
                )
            else:
                raise NotImplementedError(f"Invalid child: {type(child)} -> {child}")

            tagged_block.children.append(tagged_child)

            blocks.append((tagged_child, child_children))

    return tagged_content
