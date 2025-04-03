"""
API for containers (Sections, Subsections, Units) in Content Libraries
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from django.utils.text import slugify
from opaque_keys.edx.locator import (
    LibraryContainerLocator,
    LibraryLocatorV2,
    UsageKeyV2,
    LibraryUsageLocatorV2,
)
from openedx_events.content_authoring.data import LibraryContainerData
from openedx_events.content_authoring.signals import (
    LIBRARY_CONTAINER_CREATED,
    LIBRARY_CONTAINER_DELETED,
    LIBRARY_CONTAINER_UPDATED,
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Container

from openedx.core.djangoapps.xblock.api import get_component_from_usage_key

from ..models import ContentLibrary
from .libraries import LibraryXBlockMetadata, PublishableItem


# The public API is only the following symbols:
__all__ = [
    "ContentLibraryContainerNotFound",
    "ContainerMetadata",
    "ContainerType",
    "get_container",
    "create_container",
    "get_container_children",
    "get_container_children_count",
    "library_container_locator",
    "update_container",
    "delete_container",
    "update_container_children",
    "get_containers_contains_component",
]


ContentLibraryContainerNotFound = Container.DoesNotExist


class ContainerType(Enum):
    Unit = "unit"


@dataclass(frozen=True, kw_only=True)
class ContainerMetadata(PublishableItem):
    """
    Class that represents the metadata about a Container (e.g. Unit) in a content library.
    """
    container_key: LibraryContainerLocator
    container_type: ContainerType

    @classmethod
    def from_container(cls, library_key, container: Container, associated_collections=None):
        """
        Construct a ContainerMetadata object from a Container object.
        """
        last_publish_log = container.versioning.last_publish_log
        container_key = library_container_locator(
            library_key,
            container=container,
        )
        container_type = ContainerType(container_key.container_type)

        published_by = ""
        if last_publish_log and last_publish_log.published_by:
            published_by = last_publish_log.published_by.username

        draft = container.versioning.draft
        published = container.versioning.published
        last_draft_created = draft.created if draft else None
        if draft and draft.publishable_entity_version.created_by:
            last_draft_created_by = draft.publishable_entity_version.created_by.username
        else:
            last_draft_created_by = ""

        return cls(
            container_key=container_key,
            container_type=container_type,
            display_name=draft.title,
            created=container.created,
            modified=draft.created,
            draft_version_num=draft.version_num,
            published_version_num=published.version_num if published else None,
            last_published=None if last_publish_log is None else last_publish_log.published_at,
            published_by=published_by,
            last_draft_created=last_draft_created,
            last_draft_created_by=last_draft_created_by,
            has_unpublished_changes=authoring_api.contains_unpublished_changes(container.pk),
            collections=associated_collections or [],
        )


def library_container_locator(
    library_key: LibraryLocatorV2,
    container: Container,
) -> LibraryContainerLocator:
    """
    Returns a LibraryContainerLocator for the given library + container.

    Currently only supports Unit-type containers; will support other container types in future.
    """
    assert container.unit is not None
    container_type = ContainerType.Unit

    return LibraryContainerLocator(
        library_key,
        container_type=container_type.value,
        container_id=container.publishable_entity.key,
    )


def _get_container(container_key: LibraryContainerLocator) -> Container:
    """
    Internal method to fetch the Container object from its LibraryContainerLocator

    Raises ContentLibraryContainerNotFound if no container found, or if the container has been soft deleted.
    """
    assert isinstance(container_key, LibraryContainerLocator)
    content_library = ContentLibrary.objects.get_by_key(container_key.library_key)
    learning_package = content_library.learning_package
    assert learning_package is not None
    container = authoring_api.get_container_by_key(
        learning_package.id,
        key=container_key.container_id,
    )
    if container and container.versioning.draft:
        return container
    raise ContentLibraryContainerNotFound


def get_container(container_key: LibraryContainerLocator) -> ContainerMetadata:
    """
    Get a container (a Section, Subsection, or Unit).
    """
    container = _get_container(container_key)
    container_meta = ContainerMetadata.from_container(container_key.library_key, container)
    assert container_meta.container_type.value == container_key.container_type
    return container_meta


def create_container(
    library_key: LibraryLocatorV2,
    container_type: ContainerType,
    slug: str | None,
    title: str,
    user_id: int | None,
) -> ContainerMetadata:
    """
    Create a container (e.g. a Unit) in the specified content library.

    It will initially be empty.
    """
    assert isinstance(library_key, LibraryLocatorV2)
    content_library = ContentLibrary.objects.get_by_key(library_key)
    assert content_library.learning_package_id  # Should never happen but we made this a nullable field so need to check
    if slug is None:
        # Automatically generate a slug. Append a random suffix so it should be unique.
        slug = slugify(title, allow_unicode=True) + '-' + uuid4().hex[-6:]
    # Make sure the slug is valid by first creating a key for the new container:
    container_key = LibraryContainerLocator(
        library_key=library_key,
        container_type=container_type.value,
        container_id=slug,
    )
    # Then try creating the actual container:
    match container_type:
        case ContainerType.Unit:
            container, _initial_version = authoring_api.create_unit_and_version(
                content_library.learning_package_id,
                key=slug,
                title=title,
                created=datetime.now(),
                created_by=user_id,
            )
        case _:
            raise ValueError(f"Invalid container type: {container_type}")

    LIBRARY_CONTAINER_CREATED.send_event(
        library_container=LibraryContainerData(
            library_key=library_key,
            container_key=str(container_key),
        )
    )

    return ContainerMetadata.from_container(library_key, container)


def update_container(
    container_key: LibraryContainerLocator,
    display_name: str,
    user_id: int | None,
) -> ContainerMetadata:
    """
    Update a container (e.g. a Unit) title.
    """
    container = _get_container(container_key)
    library_key = container_key.library_key

    assert container.unit
    unit_version = authoring_api.create_next_unit_version(
        container.unit,
        title=display_name,
        created=datetime.now(),
        created_by=user_id,
    )

    LIBRARY_CONTAINER_UPDATED.send_event(
        library_container=LibraryContainerData(
            library_key=library_key,
            container_key=str(container_key),
        )
    )

    return ContainerMetadata.from_container(library_key, unit_version.container)


def delete_container(
    container_key: LibraryContainerLocator,
) -> None:
    """
    Delete a container (e.g. a Unit) (soft delete).

    No-op if container doesn't exist or has already been soft-deleted.
    """
    try:
        container = _get_container(container_key)
    except ContentLibraryContainerNotFound:
        return

    authoring_api.soft_delete_draft(container.pk)

    LIBRARY_CONTAINER_DELETED.send_event(
        library_container=LibraryContainerData(
            library_key=container_key.library_key,
            container_key=str(container_key),
        )
    )

    # TODO: trigger a LIBRARY_COLLECTION_UPDATED for each collection the container was in


def get_container_children(
    container_key: LibraryContainerLocator,
    published=False,
) -> list[authoring_api.ContainerEntityListEntry]:
    """
    Get the entities contained in the given container (e.g. the components/xblocks in a unit)
    """
    container = _get_container(container_key)
    if container_key.container_type == ContainerType.Unit.value:
        child_components = authoring_api.get_components_in_unit(container.unit, published=published)
        return [LibraryXBlockMetadata.from_component(
            container_key.library_key,
            entry.component
        ) for entry in child_components]
    else:
        child_entities = authoring_api.get_entities_in_container(container, published=published)
        return [ContainerMetadata.from_container(
            container_key.library_key,
            entry.entity
        ) for entry in child_entities]


def get_container_children_count(
    container_key: LibraryContainerLocator,
    published=False,
) -> int:
    """
    Get the count of entities contained in the given container (e.g. the components/xblocks in a unit)
    """
    container = _get_container(container_key)
    return authoring_api.get_container_children_count(container, published=published)


def update_container_children(
    container_key: LibraryContainerLocator,
    children_ids: list[UsageKeyV2] | list[LibraryContainerLocator],
    user_id: int | None,
    entities_action: authoring_api.ChildrenEntitiesAction = authoring_api.ChildrenEntitiesAction.REPLACE,
):
    """
    Adds children components or containers to given container.
    """
    library_key = container_key.library_key
    container_type = container_key.container_type
    container = _get_container(container_key)
    match container_type:
        case ContainerType.Unit.value:
            components = [get_component_from_usage_key(key) for key in children_ids]  # type: ignore[arg-type]
            new_version = authoring_api.create_next_unit_version(
                container.unit,
                components=components,  # type: ignore[arg-type]
                created=datetime.now(),
                created_by=user_id,
                entities_action=entities_action,
            )
        case _:
            raise ValueError(f"Invalid container type: {container_type}")

    LIBRARY_CONTAINER_UPDATED.send_event(
        library_container=LibraryContainerData(
            library_key=library_key,
            container_key=str(container_key),
        )
    )

    return ContainerMetadata.from_container(library_key, new_version.container)


def get_containers_contains_component(
    usage_key: LibraryUsageLocatorV2
) -> list[ContainerMetadata]:
    """
    Get containers that contains the component.
    """
    assert isinstance(usage_key, LibraryUsageLocatorV2)
    component = get_component_from_usage_key(usage_key)
    containers = authoring_api.get_containers_with_entity(
        component.publishable_entity.pk,
    )
    return [
        ContainerMetadata.from_container(usage_key.context_key, container)
        for container in containers
    ]
