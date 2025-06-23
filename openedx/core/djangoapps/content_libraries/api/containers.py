"""
API for containers (Sections, Subsections, Units) in Content Libraries
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import logging
from uuid import uuid4

from django.utils.text import slugify
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_events.content_authoring.data import (
    ContentObjectChangedData,
    LibraryCollectionData,
    LibraryContainerData,
)
from openedx_events.content_authoring.signals import (
    CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
    LIBRARY_COLLECTION_UPDATED,
    LIBRARY_CONTAINER_CREATED,
    LIBRARY_CONTAINER_DELETED,
    LIBRARY_CONTAINER_UPDATED,
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Container, ContainerVersion, Component
from openedx.core.djangoapps.content_libraries.api.collections import library_collection_locator
from openedx.core.djangoapps.content_tagging.api import get_object_tag_counts

from openedx.core.djangoapps.xblock.api import get_component_from_usage_key

from ..models import ContentLibrary
from .exceptions import ContentLibraryContainerNotFound
from .libraries import PublishableItem
from .block_metadata import LibraryXBlockMetadata
from .. import tasks

# The public API is only the following symbols:
__all__ = [
    # Models
    "ContainerMetadata",
    "ContainerType",
    # API methods
    "get_container",
    "create_container",
    "get_container_children",
    "get_container_children_count",
    "library_container_locator",
    "update_container",
    "delete_container",
    "restore_container",
    "update_container_children",
    "get_containers_contains_item",
    "publish_container_changes",
]

log = logging.getLogger(__name__)


class ContainerType(Enum):
    """
    The container types supported by content_libraries, and logic to map them to OLX.
    """
    Unit = "unit"
    Subsection = "subsection"
    Section = "section"

    @property
    def olx_tag(self) -> str:
        """
        Canonical XML tag to use when representing this container as OLX.

        For example, Units are encoded as <vertical>...</vertical>.

        These tag names are historical. We keep them around for the backwards compatibility of OLX
        and for easier interaction with legacy modulestore-powered structural XBlocks
        (e.g., copy-paste of Units between courses and V2 libraries).
        """
        match self:
            case self.Unit:
                return "vertical"
            case self.Subsection:
                return "sequential"
            case self.Section:
                return "chapter"
        raise TypeError(f"unexpected ContainerType: {self!r}")

    @classmethod
    def from_source_olx_tag(cls, olx_tag: str) -> 'ContainerType':
        """
        Get the ContainerType that this OLX tag maps to.
        """
        if olx_tag == "unit":
            # There is an alternative implementation to VerticalBlock called UnitBlock whose
            # OLX tag is <unit>. When converting from OLX, we want to handle both <vertical>
            # and <unit> as Unit containers, although the canonical serialization is still <vertical>.
            return cls.Unit
        try:
            return next(ct for ct in cls if olx_tag == ct.olx_tag)
        except StopIteration:
            raise ValueError(f"no container_type for XML tag: <{olx_tag}>") from None


@dataclass(frozen=True, kw_only=True)
class ContainerMetadata(PublishableItem):
    """
    Class that represents the metadata about a Container (e.g. Unit) in a content library.
    """
    container_key: LibraryContainerLocator
    container_type: ContainerType
    container_pk: int

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
        tags = get_object_tag_counts(str(container_key), count_implicit=True)

        return cls(
            container_key=container_key,
            container_type=container_type,
            container_pk=container.pk,
            display_name=draft.title,
            created=container.created,
            modified=draft.created,
            draft_version_num=draft.version_num,
            published_version_num=published.version_num if published else None,
            published_display_name=published.title if published else None,
            last_published=None if last_publish_log is None else last_publish_log.published_at,
            published_by=published_by,
            last_draft_created=last_draft_created,
            last_draft_created_by=last_draft_created_by,
            has_unpublished_changes=authoring_api.contains_unpublished_changes(container.pk),
            tags_count=tags.get(str(container_key), 0),
            collections=associated_collections or [],
        )


def library_container_locator(
    library_key: LibraryLocatorV2,
    container: Container,
) -> LibraryContainerLocator:
    """
    Returns a LibraryContainerLocator for the given library + container.
    """
    if hasattr(container, 'unit'):
        container_type = ContainerType.Unit
    elif hasattr(container, 'subsection'):
        container_type = ContainerType.Subsection
    elif hasattr(container, 'section'):
        container_type = ContainerType.Section

    assert container_type is not None

    return LibraryContainerLocator(
        library_key,
        container_type=container_type.value,
        container_id=container.publishable_entity.key,
    )


def _get_container_from_key(container_key: LibraryContainerLocator, isDeleted=False) -> Container:
    """
    Internal method to fetch the Container object from its LibraryContainerLocator

    Raises ContentLibraryContainerNotFound if no container found, or if the container has been soft deleted.
    """
    assert isinstance(container_key, LibraryContainerLocator)
    content_library = ContentLibrary.objects.get_by_key(container_key.lib_key)
    learning_package = content_library.learning_package
    assert learning_package is not None
    container = authoring_api.get_container_by_key(
        learning_package.id,
        key=container_key.container_id,
    )
    if container and (isDeleted or container.versioning.draft):
        return container
    raise ContentLibraryContainerNotFound


def get_container(
    container_key: LibraryContainerLocator,
    *,
    include_collections=False,
) -> ContainerMetadata:
    """
    Get a container (a Section, Subsection, or Unit).
    """
    container = _get_container_from_key(container_key)
    if include_collections:
        associated_collections = authoring_api.get_entity_collections(
            container.publishable_entity.learning_package_id,
            container_key.container_id,
        ).values('key', 'title')
    else:
        associated_collections = None
    container_meta = ContainerMetadata.from_container(
        container_key.lib_key,
        container,
        associated_collections=associated_collections,
    )
    assert container_meta.container_type.value == container_key.container_type
    return container_meta


def create_container(
    library_key: LibraryLocatorV2,
    container_type: ContainerType,
    slug: str | None,
    title: str,
    user_id: int | None,
    created: datetime | None = None,
) -> ContainerMetadata:
    """
    Create a container (a Section, Subsection, or Unit) in the specified content library.

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
        library_key,
        container_type=container_type.value,
        container_id=slug,
    )

    if not created:
        created = datetime.now(tz=timezone.utc)

    container: Container
    _initial_version: ContainerVersion

    # Then try creating the actual container:
    match container_type:
        case ContainerType.Unit:
            container, _initial_version = authoring_api.create_unit_and_version(
                content_library.learning_package_id,
                key=slug,
                title=title,
                created=created,
                created_by=user_id,
            )
        case ContainerType.Subsection:
            container, _initial_version = authoring_api.create_subsection_and_version(
                content_library.learning_package_id,
                key=slug,
                title=title,
                created=created,
                created_by=user_id,
            )
        case ContainerType.Section:
            container, _initial_version = authoring_api.create_section_and_version(
                content_library.learning_package_id,
                key=slug,
                title=title,
                created=created,
                created_by=user_id,
            )
        case _:
            raise NotImplementedError(f"Library does not support {container_type} yet")

    LIBRARY_CONTAINER_CREATED.send_event(
        library_container=LibraryContainerData(
            container_key=container_key,
        )
    )

    return ContainerMetadata.from_container(library_key, container)


def update_container(
    container_key: LibraryContainerLocator,
    display_name: str,
    user_id: int | None,
) -> ContainerMetadata:
    """
    Update a container (a Section, Subsection, or Unit) title.
    """
    container = _get_container_from_key(container_key)
    library_key = container_key.lib_key
    created = datetime.now(tz=timezone.utc)

    container_type = ContainerType(container_key.container_type)

    version: ContainerVersion
    affected_containers: list[ContainerMetadata] = []

    match container_type:
        case ContainerType.Unit:
            version = authoring_api.create_next_unit_version(
                container.unit,
                title=display_name,
                created=created,
                created_by=user_id,
            )
            affected_containers = get_containers_contains_item(container_key)
        case ContainerType.Subsection:
            version = authoring_api.create_next_subsection_version(
                container.subsection,
                title=display_name,
                created=created,
                created_by=user_id,
            )
            affected_containers = get_containers_contains_item(container_key)
        case ContainerType.Section:
            version = authoring_api.create_next_section_version(
                container.section,
                title=display_name,
                created=created,
                created_by=user_id,
            )

            # The `affected_containers` are not obtained, because the sections are
            # not contained in any container.
        case _:
            raise NotImplementedError(f"Library does not support {container_type} yet")

    # Send event related to the updated container
    LIBRARY_CONTAINER_UPDATED.send_event(
        library_container=LibraryContainerData(
            container_key=container_key,
        )
    )

    # Send events related to the containers that contains the updated container.
    # This is to update the children display names used in the section/subsection previews.
    for affected_container in affected_containers:
        LIBRARY_CONTAINER_UPDATED.send_event(
            library_container=LibraryContainerData(
                container_key=affected_container.container_key,
            )
        )

    return ContainerMetadata.from_container(library_key, version.container)


def delete_container(
    container_key: LibraryContainerLocator,
) -> None:
    """
    Delete a container (a Section, Subsection, or Unit) (soft delete).

    No-op if container doesn't exist or has already been soft-deleted.
    """
    library_key = container_key.lib_key
    container = _get_container_from_key(container_key)

    affected_collections = authoring_api.get_entity_collections(
        container.publishable_entity.learning_package_id,
        container.key,
    )
    authoring_api.soft_delete_draft(container.pk)

    LIBRARY_CONTAINER_DELETED.send_event(
        library_container=LibraryContainerData(
            container_key=container_key,
        )
    )

    # For each collection, trigger LIBRARY_COLLECTION_UPDATED signal and set background=True to trigger
    # collection indexing asynchronously.
    #
    # To delete the container on collections
    for collection in affected_collections:
        LIBRARY_COLLECTION_UPDATED.send_event(
            library_collection=LibraryCollectionData(
                collection_key=library_collection_locator(
                    library_key=library_key,
                    collection_key=collection.key,
                ),
                background=True,
            )
        )


def restore_container(container_key: LibraryContainerLocator) -> None:
    """
    Restore the specified library container.
    """
    library_key = container_key.lib_key
    container = _get_container_from_key(container_key, isDeleted=True)

    affected_collections = authoring_api.get_entity_collections(
        container.publishable_entity.learning_package_id,
        container.key,
    )

    authoring_api.set_draft_version(container.pk, container.versioning.latest.pk)

    LIBRARY_CONTAINER_CREATED.send_event(
        library_container=LibraryContainerData(
            container_key=container_key,
        )
    )

    # Add tags and collections back to index
    CONTENT_OBJECT_ASSOCIATIONS_CHANGED.send_event(
        content_object=ContentObjectChangedData(
            object_id=str(container_key),
            changes=["collections", "tags"],
        ),
    )

    # For each collection, trigger LIBRARY_COLLECTION_UPDATED signal and set background=True to trigger
    # collection indexing asynchronously.
    #
    # To restore the container on collections
    for collection in affected_collections:
        LIBRARY_COLLECTION_UPDATED.send_event(
            library_collection=LibraryCollectionData(
                collection_key=library_collection_locator(
                    library_key=library_key,
                    collection_key=collection.key,
                ),
            )
        )


def get_container_children(
    container_key: LibraryContainerLocator,
    *,
    published=False,
) -> list[LibraryXBlockMetadata | ContainerMetadata]:
    """
    Get the entities contained in the given container
    (e.g. the components/xblocks in a unit, units in a subsection, subsections in a section)
    """
    container = _get_container_from_key(container_key)
    container_type = ContainerType(container_key.container_type)

    match container_type:
        case ContainerType.Unit:
            child_components = authoring_api.get_components_in_unit(container.unit, published=published)
            return [LibraryXBlockMetadata.from_component(
                container_key.lib_key,
                entry.component
            ) for entry in child_components]
        case ContainerType.Subsection:
            child_units = authoring_api.get_units_in_subsection(container.subsection, published=published)
            return [ContainerMetadata.from_container(
                container_key.lib_key,
                entry.unit
            ) for entry in child_units]
        case ContainerType.Section:
            child_subsections = authoring_api.get_subsections_in_section(container.section, published=published)
            return [ContainerMetadata.from_container(
                container_key.lib_key,
                entry.subsection,
            ) for entry in child_subsections]
        case _:
            child_entities = authoring_api.get_entities_in_container(container, published=published)
            return [ContainerMetadata.from_container(
                container_key.lib_key,
                entry.entity
            ) for entry in child_entities]


def get_container_children_count(
    container_key: LibraryContainerLocator,
    published=False,
) -> int:
    """
    Get the count of entities contained in the given container (e.g. the components/xblocks in a unit)
    """
    container = _get_container_from_key(container_key)
    return authoring_api.get_container_children_count(container, published=published)


def update_container_children(
    container_key: LibraryContainerLocator,
    children_ids: list[LibraryUsageLocatorV2] | list[LibraryContainerLocator],
    user_id: int | None,
    entities_action: authoring_api.ChildrenEntitiesAction = authoring_api.ChildrenEntitiesAction.REPLACE,
):
    """
    Adds children components or containers to given container.
    """
    library_key = container_key.lib_key
    container_type = ContainerType(container_key.container_type)
    container = _get_container_from_key(container_key)
    created = datetime.now(tz=timezone.utc)
    new_version: ContainerVersion
    match container_type:
        case ContainerType.Unit:
            components = [get_component_from_usage_key(key) for key in children_ids]  # type: ignore[arg-type]
            new_version = authoring_api.create_next_unit_version(
                container.unit,
                components=components,  # type: ignore[arg-type]
                created=created,
                created_by=user_id,
                entities_action=entities_action,
            )

            for key in children_ids:
                CONTENT_OBJECT_ASSOCIATIONS_CHANGED.send_event(
                    content_object=ContentObjectChangedData(
                        object_id=str(key),
                        changes=["units"],
                    ),
                )
        case ContainerType.Subsection:
            units = [_get_container_from_key(key).unit for key in children_ids]  # type: ignore[arg-type]
            new_version = authoring_api.create_next_subsection_version(
                container.subsection,
                units=units,  # type: ignore[arg-type]
                created=created,
                created_by=user_id,
                entities_action=entities_action,
            )

            for key in children_ids:
                CONTENT_OBJECT_ASSOCIATIONS_CHANGED.send_event(
                    content_object=ContentObjectChangedData(
                        object_id=str(key),
                        changes=["subsections"],
                    ),
                )
        case ContainerType.Section:
            subsections = [_get_container_from_key(key).subsection for key in children_ids]  # type: ignore[arg-type]
            new_version = authoring_api.create_next_section_version(
                container.section,
                subsections=subsections,  # type: ignore[arg-type]
                created=created,
                created_by=user_id,
                entities_action=entities_action,
            )

            for key in children_ids:
                CONTENT_OBJECT_ASSOCIATIONS_CHANGED.send_event(
                    content_object=ContentObjectChangedData(
                        object_id=str(key),
                        changes=["sections"],
                    ),
                )
        case _:
            raise ValueError(f"Invalid container type: {container_type}")

    LIBRARY_CONTAINER_UPDATED.send_event(
        library_container=LibraryContainerData(
            container_key=container_key,
        )
    )

    return ContainerMetadata.from_container(library_key, new_version.container)


def get_containers_contains_item(
    key: LibraryUsageLocatorV2 | LibraryContainerLocator
) -> list[ContainerMetadata]:
    """
    Get containers that contains the item,
    that can be a component or another container.
    """
    item: Component | Container

    if isinstance(key, LibraryUsageLocatorV2):
        item = get_component_from_usage_key(key)

    elif isinstance(key, LibraryContainerLocator):
        item = _get_container_from_key(key)

    containers = authoring_api.get_containers_with_entity(
        item.publishable_entity.pk,
    )
    return [
        ContainerMetadata.from_container(key.lib_key, container)
        for container in containers
    ]


def publish_container_changes(container_key: LibraryContainerLocator, user_id: int | None) -> None:
    """
    Publish all unpublished changes in a container and all its child
    containers/blocks.
    """
    container = _get_container_from_key(container_key)
    library_key = container_key.lib_key
    content_library = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    learning_package = content_library.learning_package
    assert learning_package
    # The core publishing API is based on draft objects, so find the draft that corresponds to this container:
    drafts_to_publish = authoring_api.get_all_drafts(learning_package.id).filter(entity__pk=container.pk)
    # Publish the container, which will also auto-publish any unpublished child components:
    publish_log = authoring_api.publish_from_drafts(
        learning_package.id,
        draft_qset=drafts_to_publish,
        published_by=user_id,
    )
    # Update the search index (and anything else) for the affected container + blocks
    # This is mostly synchronous but may complete some work asynchronously if there are a lot of changes.
    tasks.wait_for_post_publish_events(publish_log, library_key)
