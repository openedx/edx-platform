"""
Python API for units in content libraries
================================

Via ``views.py``, most of these API methods are also exposed as a REST API.

The API methods in this file are focused on authoring and specific to units
in content libraries.

To import this API methods you can use:

    from openedx.core.djangoapps.content_libraries import api as library_api

"""
from __future__ import annotations

from opaque_keys.edx.locator import LibraryLocatorV2, LibraryContainerLocator

from ..constants import CONTAINER_UNIT_TYPE


def get_library_unit_usage_key(
    library_key: LibraryLocatorV2,
    unit_key: str,
) -> LibraryContainerLocator:
    """
    Returns the LibraryContainerLocator associated to a Unit.
    """

    return LibraryContainerLocator(library_key, CONTAINER_UNIT_TYPE, unit_key)
