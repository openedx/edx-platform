"""
Types used by content tagging API and implementation
"""
from __future__ import annotations

from typing import Dict, List, Union

<<<<<<< HEAD
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import Taxonomy

ContentKey = Union[LibraryLocatorV2, CourseKey, UsageKey]
=======
from opaque_keys.edx.keys import CourseKey, UsageKey, LibraryCollectionKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import Taxonomy

ContentKey = Union[LibraryLocatorV2, CourseKey, UsageKey, LibraryCollectionKey]
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
ContextKey = Union[LibraryLocatorV2, CourseKey]

TagValuesByTaxonomyIdDict = Dict[int, List[str]]
TagValuesByObjectIdDict = Dict[str, TagValuesByTaxonomyIdDict]
TaxonomyDict = Dict[int, Taxonomy]
