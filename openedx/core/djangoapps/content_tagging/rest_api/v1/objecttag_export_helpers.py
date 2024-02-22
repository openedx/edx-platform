"""
This module contains helper functions to build a object tree with object tags.
"""

from __future__ import annotations

from typing import Iterator

from attrs import define
from opaque_keys.edx.keys import CourseKey, LearningContextKey

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


def build_object_tree_with_objecttags(
    content_key: LearningContextKey,
    object_tag_cache: ObjectTagByObjectIdDict,
) -> TaggedContent:
    """
    Returns the object with the tags associated with it.
    """
    store = modulestore()

    if isinstance(content_key, CourseKey):
        course = store.get_course(content_key)
        if course is None:
            raise ValueError(f"Course not found: {content_key}")
    else:
        raise NotImplementedError(f"Invalid content_key: {type(content_key)} -> {content_key}")

    display_name = course.display_name_with_default
    course_id = str(course.id)

    tagged_course = TaggedContent(
        display_name=display_name,
        block_id=course_id,
        category=course.category,
        object_tags=object_tag_cache.get(str(content_key), {}),
        children=None,
    )

    blocks = [(tagged_course, course)]

    while blocks:
        tagged_block, xblock = blocks.pop()
        tagged_block.children = []

        if xblock.has_children:
            for child_id in xblock.children:
                child_block = store.get_item(child_id)
                tagged_child = TaggedContent(
                    display_name=child_block.display_name_with_default,
                    block_id=str(child_id),
                    category=child_block.category,
                    object_tags=object_tag_cache.get(str(child_id), {}),
                    children=None,
                )
                tagged_block.children.append(tagged_child)

                blocks.append((tagged_child, child_block))

    return tagged_course
