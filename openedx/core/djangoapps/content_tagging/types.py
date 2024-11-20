"""
Types used by content tagging API and implementation
"""
from __future__ import annotations

from typing import Dict, List, Union

from opaque_keys.edx.keys import CourseKey, UsageKey, LibraryCollectionKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import Taxonomy

ContentKey = Union[LibraryLocatorV2, CourseKey, UsageKey, LibraryCollectionKey]
ContextKey = Union[LibraryLocatorV2, CourseKey]

TagValuesByTaxonomyIdDict = Dict[int, List[str]]
TagValuesByObjectIdDict = Dict[str, TagValuesByTaxonomyIdDict]
TaxonomyDict = Dict[int, Taxonomy]
