"""
Content libraries API methods to return blocks or containers based on given keys

These methods don't enforce permissions (only the REST APIs do).
"""

from opaque_keys.edx.locator import LibraryContainerLocator, LibraryContainerUsageLocator, LibraryUsageLocatorV2
from openedx_learning.api.authoring_models import Component, Container

from openedx.core.djangoapps.xblock.api import get_component_from_usage_key

from .blocks import LibraryXBlockMetadata, get_library_block
from .containers import ContainerMetadata, get_container, get_container_from_key

__all__ = [
    "get_library_content_metadata",
    "get_library_content",
]


def get_library_content_metadata(
    usage_key: LibraryUsageLocatorV2 | LibraryContainerUsageLocator,
    include_collections=False,
) -> LibraryXBlockMetadata | ContainerMetadata:
    """
    Helper api method to return appropriate library content i.e. block metadata or container metadata based on
    usage_key.
    """
    if isinstance(usage_key, LibraryContainerUsageLocator):
        container_key = LibraryContainerLocator.from_usage_key(usage_key)
        return get_container(container_key, include_collections)
    return get_library_block(usage_key, include_collections)


def get_library_content(
    usage_key: LibraryUsageLocatorV2 | LibraryContainerUsageLocator,
) -> Container | Component:
    """
    Helper api method to return appropriate library content i.e. block or container based on usage_key
    """
    if isinstance(usage_key, LibraryContainerUsageLocator):
        container_key = LibraryContainerLocator.from_usage_key(usage_key)
        return get_container_from_key(container_key)
    return get_component_from_usage_key(usage_key)
