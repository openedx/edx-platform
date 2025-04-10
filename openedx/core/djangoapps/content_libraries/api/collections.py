"""
Python API for library collections
==================================
"""
from django.db import IntegrityError
from opaque_keys.edx.keys import BlockTypeKey, UsageKeyV2
from opaque_keys.edx.locator import (
    LibraryLocatorV2,
    LibraryCollectionLocator,
)

from openedx_events.content_authoring.data import LibraryCollectionData
from openedx_events.content_authoring.signals import LIBRARY_COLLECTION_UPDATED

from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import (
    Collection,
    Component,
    PublishableEntity,
)

from .exceptions import (
    ContentLibraryBlockNotFound,
    ContentLibraryCollectionNotFound,
    LibraryCollectionAlreadyExists,
)
from ..models import ContentLibrary

# The public API is only the following symbols:
__all__ = [
    "create_library_collection",
    "update_library_collection",
    "update_library_collection_components",
    "set_library_component_collections",
    "get_library_collection_usage_key",
    "get_library_collection_from_usage_key",
]


def create_library_collection(
    library_key: LibraryLocatorV2,
    collection_key: str,
    title: str,
    *,
    description: str = "",
    created_by: int | None = None,
    # As an optimization, callers may pass in a pre-fetched ContentLibrary instance
    content_library: ContentLibrary | None = None,
) -> Collection:
    """
    Creates a Collection in the given ContentLibrary.

    If you've already fetched a ContentLibrary for the given library_key, pass it in here to avoid refetching.
    """
    if not content_library:
        content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    assert content_library
    assert content_library.learning_package_id
    assert content_library.library_key == library_key

    try:
        collection = authoring_api.create_collection(
            learning_package_id=content_library.learning_package_id,
            key=collection_key,
            title=title,
            description=description,
            created_by=created_by,
        )
    except IntegrityError as err:
        raise LibraryCollectionAlreadyExists from err

    return collection


def update_library_collection(
    library_key: LibraryLocatorV2,
    collection_key: str,
    *,
    title: str | None = None,
    description: str | None = None,
    # As an optimization, callers may pass in a pre-fetched ContentLibrary instance
    content_library: ContentLibrary | None = None,
) -> Collection:
    """
    Updates a Collection in the given ContentLibrary.
    """
    if not content_library:
        content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    assert content_library
    assert content_library.learning_package_id
    assert content_library.library_key == library_key

    try:
        collection = authoring_api.update_collection(
            learning_package_id=content_library.learning_package_id,
            key=collection_key,
            title=title,
            description=description,
        )
    except Collection.DoesNotExist as exc:
        raise ContentLibraryCollectionNotFound from exc

    return collection


def update_library_collection_components(
    library_key: LibraryLocatorV2,
    collection_key: str,
    *,
    usage_keys: list[UsageKeyV2],
    created_by: int | None = None,
    remove=False,
    # As an optimization, callers may pass in a pre-fetched ContentLibrary instance
    content_library: ContentLibrary | None = None,
) -> Collection:
    """
    Associates the Collection with Components for the given UsageKeys.

    By default the Components are added to the Collection.
    If remove=True, the Components are removed from the Collection.

    If you've already fetched the ContentLibrary, pass it in to avoid refetching.

    Raises:
    * ContentLibraryCollectionNotFound if no Collection with the given pk is found in the given library.
    * ContentLibraryBlockNotFound if any of the given usage_keys don't match Components in the given library.

    Returns the updated Collection.
    """
    if not content_library:
        content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    assert content_library
    assert content_library.learning_package_id
    assert content_library.library_key == library_key

    # Fetch the Component.key values for the provided UsageKeys.
    component_keys = []
    for usage_key in usage_keys:
        # Parse the block_family from the key to use as namespace.
        block_type = BlockTypeKey.from_string(str(usage_key))

        try:
            component = authoring_api.get_component_by_key(
                content_library.learning_package_id,
                namespace=block_type.block_family,
                type_name=usage_key.block_type,
                local_key=usage_key.block_id,
            )
        except Component.DoesNotExist as exc:
            raise ContentLibraryBlockNotFound(usage_key) from exc

        component_keys.append(component.key)

    # Note: Component.key matches its PublishableEntity.key
    entities_qset = PublishableEntity.objects.filter(
        key__in=component_keys,
        learning_package_id=content_library.learning_package_id,
    )

    if remove:
        collection = authoring_api.remove_from_collection(
            content_library.learning_package_id,
            collection_key,
            entities_qset,
        )
    else:
        collection = authoring_api.add_to_collection(
            content_library.learning_package_id,
            collection_key,
            entities_qset,
            created_by=created_by,
        )

    return collection


def set_library_component_collections(
    library_key: LibraryLocatorV2,
    component: Component,
    *,
    collection_keys: list[str],
    created_by: int | None = None,
    # As an optimization, callers may pass in a pre-fetched ContentLibrary instance
    content_library: ContentLibrary | None = None,
) -> Component:
    """
    It Associates the component with collections for the given collection keys.

    Only collections in queryset are associated with component, all previous component-collections
    associations are removed.

    If you've already fetched the ContentLibrary, pass it in to avoid refetching.

    Raises:
    * ContentLibraryCollectionNotFound if any of the given collection_keys don't match Collections in the given library.

    Returns the updated Component.
    """
    if not content_library:
        content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    assert content_library
    assert content_library.learning_package_id
    assert content_library.library_key == library_key

    # Note: Component.key matches its PublishableEntity.key
    collection_qs = authoring_api.get_collections(content_library.learning_package_id).filter(
        key__in=collection_keys
    )

    affected_collections = authoring_api.set_collections(
        content_library.learning_package_id,
        component,
        collection_qs,
        created_by=created_by,
    )

    # For each collection, trigger LIBRARY_COLLECTION_UPDATED signal and set background=True to trigger
    # collection indexing asynchronously.
    for collection in affected_collections:
        LIBRARY_COLLECTION_UPDATED.send_event(
            library_collection=LibraryCollectionData(
                library_key=library_key,
                collection_key=collection.key,
                background=True,
            )
        )

    return component


def get_library_collection_usage_key(
    library_key: LibraryLocatorV2,
    collection_key: str,
) -> LibraryCollectionLocator:
    """
    Returns the LibraryCollectionLocator associated to a collection
    """

    return LibraryCollectionLocator(library_key, collection_key)


def get_library_collection_from_usage_key(
    collection_usage_key: LibraryCollectionLocator,
) -> Collection:
    """
    Return a Collection using the LibraryCollectionLocator
    """

    library_key = collection_usage_key.library_key
    collection_key = collection_usage_key.collection_id
    content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    assert content_library.learning_package_id is not None  # shouldn't happen but it's technically possible.
    try:
        return authoring_api.get_collection(
            content_library.learning_package_id,
            collection_key,
        )
    except Collection.DoesNotExist as exc:
        raise ContentLibraryCollectionNotFound from exc
