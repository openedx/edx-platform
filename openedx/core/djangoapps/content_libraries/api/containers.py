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
    LibraryLocatorV2,
    LibraryContainerLocator,
)

from openedx_learning.api import authoring as authoring_api
from openedx_learning.api import authoring_models

from ..models import ContentLibrary
from .libraries import PublishableItem

# The public API is only the following symbols:
__all__ = [
    "ContainerMetadata",
    "create_container",
]


class ContainerType(Enum):
    Unit = "unit"


@dataclass(frozen=True, kw_only=True)
class ContainerMetadata(PublishableItem):
    """
    Class that represents the metadata about an XBlock in a content library.
    """
    container_key: LibraryContainerLocator
    container_type: ContainerType

    @classmethod
    def from_container(cls, library_key, container: authoring_models.Container, associated_collections=None):
        """
        Construct a LibraryXBlockMetadata from a Component object.
        """
        last_publish_log = container.versioning.last_publish_log

        assert container.unit is not None
        container_type = ContainerType.Unit

        published_by = None
        if last_publish_log and last_publish_log.published_by:
            published_by = last_publish_log.published_by.username

        draft = container.versioning.draft
        published = container.versioning.published
        last_draft_created = draft.created if draft else None
        last_draft_created_by = draft.publishable_entity_version.created_by.username if draft else ""

        return cls(
            container_key=LibraryContainerLocator(
                library_key,
                container_type=container_type.value,
                container_id=container.publishable_entity.key,
            ),
            container_type=container_type,
            display_name=draft.title,
            created=container.created,
            modified=draft.created,
            draft_version_num=draft.version_num,
            published_version_num=published.version_num if published else None,
            last_published=None if last_publish_log is None else last_publish_log.published_at,
            published_by=published_by or "",
            last_draft_created=last_draft_created,
            last_draft_created_by=last_draft_created_by,
            has_unpublished_changes=authoring_api.contains_unpublished_changes(container.pk),
            collections=associated_collections or [],
        )


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
    LibraryContainerLocator(library_key=library_key, container_type=container_type.value, container_id=slug)
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
    return ContainerMetadata.from_container(library_key, container)
