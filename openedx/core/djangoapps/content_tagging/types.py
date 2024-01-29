"""
Types used by content tagging API and implementation
"""
from __future__ import annotations
from typing import Union, Dict, List

from attrs import define
from opaque_keys.edx.keys import LearningContextKey, UsageKey
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy
from xblock.core import XBlock

ContentKey = Union[LearningContextKey, UsageKey]

ObjectTagByTaxonomyIdDict = Dict[int, List[ObjectTag]]
ObjectTagByObjectIdDict = Dict[str, ObjectTagByTaxonomyIdDict]
TaxonomyDict = Dict[int, Taxonomy]


@define
class TaggedContent:
    """
    A tagged content, with its tags and children.
    """
    xblock: XBlock  # ToDo: Check correct type here
    object_tags: ObjectTagByTaxonomyIdDict
    children: list[TaggedContent] | None
