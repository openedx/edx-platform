"""
Types used by content tagging API and implementation
"""
from __future__ import annotations

from typing import Dict, List, Union

from opaque_keys.edx.keys import LearningContextKey, UsageKey
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy

ContentKey = Union[LearningContextKey, UsageKey]

ObjectTagByTaxonomyIdDict = Dict[int, List[ObjectTag]]
ObjectTagByObjectIdDict = Dict[str, ObjectTagByTaxonomyIdDict]
TaxonomyDict = Dict[int, Taxonomy]
